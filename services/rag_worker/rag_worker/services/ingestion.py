import logging
from datetime import datetime
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from shared.config import config

logger = logging.getLogger("rag_worker.services.ingestion")


class IngestionService:
    def __init__(self, vector_store, redis_client):
        self.vector_store = vector_store
        self.redis_client = redis_client
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )

    def ingest(self, doc_id: str, raw_text: str, filename: str = "Unknown"):
        if not raw_text:
            logger.warning(f"No text extracted for document {doc_id}")
            self._publish_update(doc_id, "failed", "No text extracted from document.")
            return
        try:
            chunks = self.splitter.split_text(raw_text)

            documents = [
                Document(
                    page_content=text, metadata={"doc_id": doc_id, "chunk_index": i}
                )
                for i, text in enumerate(chunks)
            ]

            if documents:
                self.vector_store.add_documents(documents)
                metadata = {
                    "doc_id": doc_id,
                    "filename": filename,
                    "status": "synced",
                    "timestamp": datetime.now().isoformat(),
                }
                self.redis_client.hset("rag_documents", doc_id, json.dumps(metadata))
                logger.info(f"Indexed {len(documents)} chunks for {doc_id}")
                self._publish_update(doc_id, "completed", "File synced successfully.")
        except Exception as e:
            metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }
            self.redis_client.hset("rag_documents", doc_id, json.dumps(metadata))
            logger.error(f"Failed to ingest document {doc_id}: {e}")
            self._publish_update(doc_id, "failed", str(e))

    def _publish_update(self, doc_id, status, msg):
        payload = json.dumps(
            {"type": "job_update", "doc_id": doc_id, "status": status, "message": msg}
        )
        self.redis_client.publish("job_updates", payload)
