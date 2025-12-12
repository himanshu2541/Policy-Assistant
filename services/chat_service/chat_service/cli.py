import sys

from chat_service.app.main import serve

import logging

logger = logging.getLogger("Chat-Service.CLI")


def run():
    """
    Entry point to start the RAG Worker.
    """
    logger.info(f"Starting Chat Service...")

    try:
        serve()
    except KeyboardInterrupt:
        logger.info("Chat Service stopped manually.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Chat Service crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
