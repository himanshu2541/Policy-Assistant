import asyncio
import sys
from shared.config import config as settings


def run():
    from stt_service.app.main import serve

    if asyncio.iscoroutinefunction(serve):
        try:
            asyncio.run(serve())
        except KeyboardInterrupt:
            print("shutting down (KeyboardInterrupt)", file=sys.stderr)
    else:
        serve() # type: ignore


if __name__ == "__main__":
    run()
