from rag_service.app.server import serve
from shared.config import setup_logging


def main():
    import asyncio

    setup_logging()
    asyncio.run(serve())
