import sys
import asyncio

from shared.config import config
from rag_worker.worker import main as start_worker

import logging

logger = logging.getLogger("RAG-Worker-CLI")


def run():
    """
    Entry point to start the RAG Worker.
    """
    logger.info(f"Starting RAG Worker...")
    logger.info(
        f"Embedding Provider: {config.EMBEDDING_PROVIDER}, Embedding Model: {config.EMBEDDING_MODEL_NAME}"
    )
    logger.info(f"Listening to Queue: rag_jobs")

    try:
        asyncio.run(start_worker())
    except asyncio.CancelledError:
        logger.info("RAG Worker Cancelled. Shutting down...")
    except KeyboardInterrupt:
        logger.info("RAG Worker stopped manually.")
    except Exception as e:
        logger.error(f"RAG Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
