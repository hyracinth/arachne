import asyncio
from app.honeytrap.engine import ArachneTrap

if __name__ == '__main__':
    trap = ArachneTrap(port=2323)
    try:
        asyncio.run(trap.start())
    except KeyboardInterrupt:
        print("\nHoneytrap shutting down...")