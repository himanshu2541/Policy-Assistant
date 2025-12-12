import json
import time
import logging
import os
from redis import Redis

# Shared Providers
from shared.config import config, setup_logging
from shared.providers.embeddings import EmbeddingsProvider
from shared.providers.vector_database import VectorDatabase

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


def main():
    logger.info("Starting RAG Worker...")

    redis_client = Redis.from_url(config.REDIS_URL, decode_responses=True)

    # Initialize Providers
    logger.info("Loading Embeddings...")
    embeddings = EmbeddingsProvider(config).get_embeddings()
    vector_store = VectorDatabase(embeddings, config).get_store()

    # Initialize Ingestion Service
    ingestion_service = IngestionService(vector_store, redis_client)

    logger.info("Waiting for jobs...")

    while True:
        try:
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

                ingestion_service.ingest(doc_id, raw_text)
                logger.info(f"Completed processing for: {doc_id}")
        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
