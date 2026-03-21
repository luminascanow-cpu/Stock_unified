import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

from ..models.models import Alert
from ..utils.config import config, get_env

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


@dataclass
class AlertConfig:
    enabled: bool
    thresholds: Dict[str, float]
    escalation_levels: Dict[str, float]


class TelegramAlertService:
    def __init__(self):
        self.config = config.get('telegram', {})
        self.enabled = self.config.get('enabled', False) and TELEGRAM_AVAILABLE
        
        if self.enabled:
            self.bot_token = self.config.get('bot_token', '')
            self.chat_id = self.config.get('chat_id', '')
            try:
                self.bot = Bot(token=self.bot_token)
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.bot = None
        else:
            self.bot = None
    
    async def send_alert(self, alert: Alert) -> bool:
        if not self.enabled or not self.bot:
            return False
        
        try:
            emoji = self._get_severity_emoji(alert.severity)
            message = f"{emoji} *{alert.title}*\n\n{alert.message}\n\n"
            
            if alert.related_sectors:
                message += f"Sectors: {', '.join(alert.related_sectors)}\n"
            if alert.related_stocks:
                message += f"Stocks: {', '.join(alert.related_stocks)}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    async def send_digest(self, title: str, content: str, alerts: List[Alert]) -> bool:
        if not self.enabled or not self.bot:
            return False
        
        try:
            message = f"📊 *{title}*\n\n"
            message += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += f"Total Alerts: {len(alerts)}\n\n"
            
            if alerts:
                message += "*Recent Alerts:*\n"
                for alert in alerts[:5]:
                    emoji = self._get_severity_emoji(alert.severity)
                    message += f"{emoji} {alert.title}\n"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Telegram digest error: {e}")
            return False
    
    def _get_severity_emoji(self, severity: str) -> str:
        return {
            'info': 'ℹ️',
            'warning': '⚠️',
            'medium': '⚠️',
            'high': '🔴',
            'critical': '🚨',
            'urgent': '🆘'
        }.get(severity.lower(), '📌')


class WhatsAppAlertService:
    def __init__(self):
        self.config = config.get('whatsapp', {})
        self.enabled = self.config.get('enabled', False) and TWILIO_AVAILABLE
        
        if self.enabled:
            self.sid = self.config.get('twilio_sid', '')
            self.token = self.config.get('twilio_token', '')
            self.from_number = self.config.get('from_number', '')
            self.to_number = self.config.get('to_number', '')
            
            try:
                self.client = Client(self.sid, self.token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            self.client = None
    
    async def send_alert(self, alert: Alert) -> bool:
        if not self.enabled or not self.client:
            return False
        
        try:
            emoji = self._get_severity_emoji(alert.severity)
            message = f"{emoji} {alert.title}\n\n{alert.message}"
            
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            return True
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return False
    
    async def send_digest(self, title: str, content: str, alerts: List[Alert]) -> bool:
        if not self.enabled or not self.client:
            return False
        
        try:
            message = f"📊 {title}\n\nAlerts: {len(alerts)}"
            
            for alert in alerts[:3]:
                emoji = self._get_severity_emoji(alert.severity)
                message += f"\n{emoji} {alert.title}"
            
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            return True
        except Exception as e:
            logger.error(f"WhatsApp digest error: {e}")
            return False
    
    def _get_severity_emoji(self, severity: str) -> str:
        return {
            'info': 'ℹ️',
            'warning': '⚠️',
            'medium': '⚠️',
            'high': '🔴',
            'critical': '🚨',
            'urgent': '🆘'
        }.get(severity.lower(), '📌')


class EmailAlertService:
    def __init__(self):
        self.config = config.get('email', {})
        self.enabled = self.config.get('enabled', False)
        
        if self.enabled:
            self.smtp_host = self.config.get('smtp_host', 'smtp.gmail.com')
            self.smtp_port = self.config.get('smtp_port', 587)
            self.smtp_user = self.config.get('smtp_user', '')
            self.smtp_password = self.config.get('smtp_password', '')
            self.from_email = self.config.get('from_email', '')
            self.to_emails = self.config.get('to_emails', [])
        else:
            self.to_emails = []
    
    def _send_email(self, subject: str, body: str, html: bool = False) -> bool:
        if not self.enabled or not self.to_emails:
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            
            msg.attach(part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    async def send_alert(self, alert: Alert) -> bool:
        if not self.enabled:
            return False
        
        subject = f"[{alert.severity.upper()}] {alert.title}"
        body = f"""
Alert Details
=============
Title: {alert.title}
Severity: {alert.severity}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{alert.message}
"""
        
        if alert.related_sectors:
            body += f"\nSectors: {', '.join(alert.related_sectors)}"
        if alert.related_stocks:
            body += f"\nStocks: {', '.join(alert.related_stocks)}"
        
        return self._send_email(subject, body)
    
    async def send_digest(self, title: str, content: str, alerts: List[Alert]) -> bool:
        if not self.enabled:
            return False
        
        subject = f"📊 {title} - {datetime.now().strftime('%Y-%m-%d')}"
        
        html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert-item {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .alert-high {{ background: #ffebee; border-left: 4px solid #f44336; }}
        .alert-medium {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
        .alert-low {{ background: #e8f5e9; border-left: 4px solid #4caf50; }}
        .severity {{ font-weight: bold; text-transform: uppercase; }}
    </style>
</head>
<body>
    <h2>{title}</h2>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Total Alerts: {len(alerts)}</p>
    
    <h3>Recent Alerts</h3>
"""
        
        for alert in alerts[:10]:
            severity_class = 'alert-high' if alert.severity == 'high' else 'alert-medium' if alert.severity == 'medium' else 'alert-low'
            html_content += f"""
    <div class="alert-item {severity_class}">
        <span class="severity">{alert.severity.upper()}</span>
        <strong>{alert.title}</strong>
        <p>{alert.message}</p>
        <small>{alert.timestamp.strftime('%H:%M:%S')}</small>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        return self._send_email(subject, html_content, html=True)


class AlertManager:
    def __init__(self):
        self.telegram = TelegramAlertService()
        self.whatsapp = WhatsAppAlertService()
        self.email = EmailAlertService()
        
        self.alert_config = config.get('alerts', {})
        self.escalation_levels = self.alert_config.get('escalation_levels', {})
        
        self.last_alerts: Dict[str, datetime] = {}
        self.cooldown_seconds = 300
    
    async def process_alert(self, alert: Alert) -> bool:
        if not self.alert_config.get('enabled', True):
            return False
        
        alert_key = f"{alert.id}"
        if alert_key in self.last_alerts:
            time_since_last = (datetime.now() - self.last_alerts[alert_key]).total_seconds()
            if time_since_last < self.cooldown_seconds:
                return False
        
        self.last_alerts[alert_key] = datetime.now()
        
        severity_level = self._get_escalation_level(alert.severity)
        
        tasks = []
        
        if severity_level >= self.escalation_levels.get('info', 0):
            tasks.append(self.telegram.send_alert(alert))
        
        if severity_level >= self.escalation_levels.get('warning', 0.5):
            tasks.append(self.whatsapp.send_alert(alert))
        
        if severity_level >= self.escalation_levels.get('critical', 0.7):
            tasks.append(self.email.send_alert(alert))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return any(r is True for r in results)
    
    async def send_morning_briefing(self, content: str, alerts: List[Alert]) -> bool:
        tasks = [
            self.telegram.send_digest("Morning Briefing", content, alerts),
            self.whatsapp.send_digest("Morning Briefing", content, alerts),
            self.email.send_digest("Morning Briefing", content, alerts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(r is True for r in results)
    
    async def send_eod_summary(self, content: str, alerts: List[Alert]) -> bool:
        tasks = [
            self.telegram.send_digest("EOD Summary", content, alerts),
            self.whatsapp.send_digest("EOD Summary", content, alerts),
            self.email.send_digest("EOD Summary", content, alerts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(r is True for r in results)
    
    def _get_escalation_level(self, severity: str) -> float:
        return {
            'info': 0.3,
            'warning': 0.5,
            'medium': 0.5,
            'high': 0.7,
            'critical': 0.85,
            'urgent': 1.0
        }.get(severity.lower(), 0.3)


alert_manager = AlertManager()