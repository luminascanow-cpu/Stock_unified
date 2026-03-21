import logging
from datetime import datetime
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

from ..utils.config import config
from ..services.prediction_engine_v2 import prediction_engine_v2
from ..services.alert_service import alert_manager
from ..services.nse_service import market_hours_service, nse_service

scheduler = AsyncIOScheduler()


class MarketHoursScheduler:
    def __init__(self):
        self.scheduler_config = config.get('scheduler', {})
        self.enabled = self.scheduler_config.get('market_hours', {}).get('enabled', True)
        self.interval_minutes = self.scheduler_config.get('market_hours', {}).get('interval_minutes', 5)
        
        self.morning_config = self.scheduler_config.get('morning_digest', {})
        self.eod_config = self.scheduler_config.get('eod_summary', {})
    
    def setup_jobs(self):
        if not self.enabled:
            logger.info("Market hours scheduler disabled")
            return
        
        if self.morning_config.get('enabled', True):
            morning_time = self.morning_config.get('time', '08:00')
            hour, minute = map(int, morning_time.split(':'))
            
            scheduler.add_job(
                self.morning_digest_job,
                CronTrigger(hour=hour, minute=minute),
                id='morning_digest',
                replace_existing=True
            )
            logger.info(f"Morning digest scheduled at {morning_time}")
        
        if self.eod_config.get('enabled', True):
            eod_time = self.eod_config.get('time', '16:00')
            hour, minute = map(int, eod_time.split(':'))
            
            scheduler.add_job(
                self.eod_summary_job,
                CronTrigger(hour=hour, minute=minute),
                id='eod_summary',
                replace_existing=True
            )
            logger.info(f"EOD summary scheduled at {eod_time}")
        
        scheduler.add_job(
            self.market_refresh_job,
            IntervalTrigger(minutes=self.interval_minutes),
            id='market_refresh',
            replace_existing=True
        )
        logger.info(f"Market refresh scheduled every {self.interval_minutes} minutes")
        
        scheduler.add_job(
            self.health_check_job,
            IntervalTrigger(minutes=15),
            id='health_check',
            replace_existing=True
        )
    
    async def market_refresh_job(self):
        if not market_hours_service.should_run_scheduler():
            logger.info("Market closed, skipping refresh")
            return
        
        logger.info("Running scheduled market refresh...")
        try:
            dashboard_data = await prediction_engine_v2.refresh_data()
            
            for alert in dashboard_data.alerts:
                await alert_manager.process_alert(alert)
            
            nse_service.clear_cache()
            
            logger.info(f"Market refresh completed: {len(dashboard_data.alerts)} alerts generated")
        except Exception as e:
            logger.error(f"Market refresh error: {e}")
    
    async def morning_digest_job(self):
        logger.info("Running morning digest...")
        try:
            dashboard_data = await prediction_engine_v2.refresh_data()
            
            content = f"""
Good Morning! Here's your daily geo-political stock monitor update.

Total News: {len(dashboard_data.latest_news)}
Active Alerts: {len(dashboard_data.alerts)}
Top Sectors: {', '.join([s.name for s in dashboard_data.sector_analysis[:3]])}

Markets: {'Open' if market_hours_service.is_market_open() else 'Closed'}
"""
            
            await alert_manager.send_morning_briefing(content, dashboard_data.alerts)
            
            logger.info("Morning digest completed")
        except Exception as e:
            logger.error(f"Morning digest error: {e}")
    
    async def eod_summary_job(self):
        logger.info("Running EOD summary...")
        try:
            dashboard_data = await prediction_engine_v2.refresh_data()
            
            content = f"""
End of Day Summary - {datetime.now().strftime('%Y-%m-%d')}

News Analyzed: {len(dashboard_data.latest_news)}
Alerts Generated: {len(dashboard_data.alerts)}

Sector Performance:
{chr(10).join([f"- {s.name}: {s.overall_sentiment.value} ({s.confidence:.0%})" for s in dashboard_data.sector_analysis[:5]])}

Top Predictions:
{chr(10).join([f"- {p.symbol}: {p.prediction.value} ({p.confidence:.0%})" for p in dashboard_data.top_predictions[:5]])}

Next market open: {market_hours_service.get_next_open_time()}
"""
            
            await alert_manager.send_eod_summary(content, dashboard_data.alerts)
            
            logger.info("EOD summary completed")
        except Exception as e:
            logger.error(f"EOD summary error: {e}")
    
    async def health_check_job(self):
        logger.info("Running health check...")
        
        is_open = market_hours_service.is_market_open()
        next_open = market_hours_service.get_next_open_time()
        
        logger.info(f"Health check - Market: {is_open}, Next open: {next_open}")
    
    def start(self):
        self.setup_jobs()
        scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self):
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def get_jobs(self):
        return [{'id': job.id, 'next_run': job.next_run_time} for job in scheduler.get_jobs()]


market_hours_scheduler = MarketHoursScheduler()