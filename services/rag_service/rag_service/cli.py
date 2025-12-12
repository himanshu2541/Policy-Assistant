import sys
from shared.config import config
import logging

logger = logging.getLogger("RAG-Service-CLI")


def run():
    from rag_service.app.main import main as serve

    logger.info(f"Starting RAG Service...")
    try:
        serve()
    except KeyboardInterrupt:
        logger.info("RAG Service stopped manually.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"RAG Service crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
