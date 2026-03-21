import asyncio
import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.prediction_engine_v2 import prediction_engine_v2
from src.models.models import SentimentType

class CLIMonitor:
    def __init__(self):
        self.engine = prediction_engine_v2
        
    async def run(self):
        parser = argparse.ArgumentParser(description='Geo-Political Stock Monitor CLI')
        parser.add_argument('--refresh', '-r', action='store_true', help='Refresh data and show summary')
        parser.add_argument('--news', '-n', type=int, default=10, help='Number of news to show')
        parser.add_argument('--sectors', '-s', action='store_true', help='Show sector analysis')
        parser.add_argument('--alerts', '-a', action='store_true', help='Show alerts')
        parser.add_argument('--watch', '-w', action='store_true', help='Watch mode - continuous monitoring')
        
        args = parser.parse_args()
        
        if args.watch:
            await self.watch_mode()
        else:
            await self.show_summary(args)
    
    async def show_summary(self, args):
        print("\n" + "="*60)
        print("  📊 Geo-Political Stock Monitor - India")
        print("  Fetching latest data...")
        print("="*60 + "\n")
        
        data = await self.engine.refresh_data()
        
        print(f"📰 Latest News ({len(data.latest_news)} articles)")
        print("-"*60)
        for i, news in enumerate(data.latest_news[:args.news], 1):
            emoji = "🟢" if "bullish" in news.sentiment_label.value else "🔴" if "bearish" in news.sentiment_label.value else "⚪"
            breaking = " 🔴 BREAKING" if news.is_breaking else ""
            print(f"{i}. {emoji} {news.title[:70]}...")
            print(f"   Source: {news.source} | Sentiment: {news.sentiment_label.value}{breaking}")
            print()
        
        if args.sectors:
            print(f"\n📈 Sector Analysis")
            print("-"*60)
            for sector in data.sector_analysis:
                emoji = "📈" if "bullish" in sector.overall_sentiment.value else "📉" if "bearish" in sector.overall_sentiment.value else "➡️"
                print(f"{emoji} {sector.name}: {sector.overall_sentiment.value} ({sector.confidence:.0%} confidence)")
                print(f"   News: {sector.news_count} | Stocks: {', '.join([s.symbol for s in sector.affected_stocks[:3]])}")
                print()
        
        if args.alerts:
            print(f"\n🚨 Active Alerts ({len(data.alerts)})")
            print("-"*60)
            for alert in data.alerts[:10]:
                severity = "🔴" if alert.severity == "high" else "🟡" if alert.severity == "medium" else "⚪"
                print(f"{severity} [{alert.severity.upper()}] {alert.title}")
                print(f"   Time: {alert.timestamp.strftime('%H:%M:%S')}")
                print()
        
        print(f"\n⏰ Last Updated: {data.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
    
    async def watch_mode(self):
        print("\n🔄 Watch Mode - Press Ctrl+C to exit\n")
        while True:
            try:
                await self.show_summary(argparse.Namespace(news=5, sectors=True, alerts=True, watch=False, refresh=True))
                await asyncio.sleep(60)
                print("\n" + "─"*60 + "\n")
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                break

if __name__ == "__main__":
    cli = CLIMonitor()
    asyncio.run(cli.run())
