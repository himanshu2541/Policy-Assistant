import json
import time
import logging
import os

# Shared Providers
from shared.config import config, setup_logging
from shared.providers.embeddings import EmbeddingFactory
from shared.providers.vector_database import VectorDBFactory
from shared.providers.redis import RedisFactory

from rag_worker.processors.pdf_processor import PdfProcessor
from rag_worker.processors.text_processor import TextProcessor

from rag_worker.services.ingestion import IngestionService

setup_logging()
logger = logging.getLogger("RAG-Worker")


def get_processor(file_path: str):
    """Factory function to select the right processor based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".pdf":
        return PdfProcessor()
    elif ext in [".txt", ".md", ".json"]:  # Added support for md/json as text
        return TextProcessor()
    else:
        return None


async def main():
    logger.info("Starting RAG Worker...")

    redis_client = RedisFactory.get_client(config)

    # Initialize Providers
    logger.info("Loading Embeddings...")
    embeddings = EmbeddingFactory.get_embeddings(config)
    vector_store = VectorDBFactory.get_vector_store(embeddings, config)

    # Initialize Ingestion Service
    ingestion_service = IngestionService(vector_store, redis_client)

    logger.info("Waiting for jobs...")

    try:
        while True:
            result = redis_client.brpop(["rag_jobs"], timeout=1)
            if result:
                _, job_data_str = result  # type: ignore
                job = json.loads(job_data_str)
                doc_id = job.get("doc_id")
                file_path = job.get("file_path")

                logger.info(f"Processing: {doc_id} ({file_path})")

                processor = get_processor(file_path)
                if not processor:
                    logger.error(f"Unsupported file format: {file_path}")
                    continue

                raw_text = processor.process(file_path) or ""
                logger.info(f"Extracted {len(raw_text)} characters from {doc_id}")

                await ingestion_service.ingest(doc_id, raw_text)
                logger.info(f"Completed processing for: {doc_id}")
    except Exception as e:
        logger.error(f"Worker Loop encountered an error: {e}")
        time.sleep(1) 
    finally:
        logger.info("Closing Redis connection...")
        await RedisFactory.close()
