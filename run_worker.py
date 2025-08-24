#!/usr/bin/env python3

import asyncio
import signal
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.workers.daily_sync import DailySyncWorker
from app.config import DEBUG

async def main():
    worker = DailySyncWorker()
    
    def signal_handler(signum, frame):
        print("\nWorker interrupted by user")
        worker.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("Starting Daily Sync Worker...")
        await worker.run()
        print("Worker completed successfully!")
    except KeyboardInterrupt:
        print("\nWorker interrupted by user")
        worker.stop()
    except Exception as e:
        print(f"Worker failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if DEBUG:
        print("Running in DEBUG mode")
    
    asyncio.run(main())
