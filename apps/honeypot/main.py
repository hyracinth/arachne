import asyncio
from apps.honeypot.engine import ArachneTrap

if __name__ == '__main__':
    trap = ArachneTrap(ports=[2323])
    try:
        asyncio.run(trap.start())
    except KeyboardInterrupt:
        print("\nHoneytrap shutting down...")