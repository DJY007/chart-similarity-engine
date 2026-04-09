import asyncio
import sys
import os

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.data_manager import HistoricalDataManager

# 预加载清单
INIT_PAIRS = [
    ("BTC/USDT", ["1h", "4h", "1d"]),
    ("ETH/USDT", ["1h", "4h", "1d"]),
    ("SOL/USDT", ["1h", "4h", "1d"]),
]

async def main():
    print("🚀 Starting data initialization...")
    manager = HistoricalDataManager()
    
    for symbol, timeframes in INIT_PAIRS:
        print(f"\n📊 Processing {symbol}...")
        for tf in timeframes:
            print(f"  - Syncing {tf} data...")
            try:
                await manager.ensure_data(symbol, tf)
                print(f"  ✅ {symbol} {tf} sync complete.")
            except Exception as e:
                print(f"  ❌ Error syncing {symbol} {tf}: {e}")
                
    print("\n✨ Data initialization finished!")

if __name__ == "__main__":
    asyncio.run(main())
