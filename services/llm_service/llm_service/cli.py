import sys
import logging

logger = logging.getLogger("LLM-Service-CLI")


def run():
    from llm_service.app.main import serve

    logger.info(f"Starting LLM Service...")

    try:
        serve()
    except KeyboardInterrupt:
        logger.info("LLM Service stopped manually.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"LLM Service crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
