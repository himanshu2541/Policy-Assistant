import json
import time
import logging
from redis import Redis
from pypdf import PdfReader

# LangChain Utilities
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Shared Providers
from shared.config import config, setup_logging
from shared.providers.embeddings import EmbeddingsProvider
from shared.providers.vector_database import VectorDatabase

setup_logging()
logger = logging.getLogger("RAG-Worker")


def process_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        return "".join([page.extract_text() or "" for page in reader.pages])
    except Exception:
        return None


def main():
    logger.info("Starting RAG Worker...")

    redis_client = Redis.from_url(config.REDIS_URL, decode_responses=True)

    # Initialize Providers
    logger.info("Loading Embeddings...")
    embeddings = EmbeddingsProvider(config).get_embeddings()
    vector_store = VectorDatabase(embeddings, config).get_store()

    logger.info("Waiting for jobs...")

    while True:
        try:
            result = redis_client.brpop(["rag_jobs"], timeout=1)
            if result:
                _, job_data_str = result # type: ignore
                job = json.loads(job_data_str)
                logger.info(f"Processing: {job.get('doc_id')}")

                raw_text = process_pdf(job.get("file_path"))
                if not raw_text:
                    continue

                # Split Text
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
                )
                chunks = splitter.split_text(raw_text)

                # Convert to LangChain Documents
                documents = []
                for i, text in enumerate(chunks):
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={"doc_id": job["doc_id"], "chunk_index": i},
                        )
                    )

                vector_store.add_documents(documents)

                logger.info(f"Indexed {len(documents)} chunks for {job['doc_id']}")

        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
