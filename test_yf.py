import asyncio
from src.services.technical_analysis_service import technical_service

async def run():
    print("Fetching 52w highs...")
    await technical_service.fetch_52w_highs()
    print("Fetching intraday data...")
    res = await technical_service.fetch_all()
    print(f"Results length: {len(res)}")
    print("Nifty:", await technical_service.get_nifty())

asyncio.run(run())
