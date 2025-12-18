import json
import logging
from datetime import datetime
from rag_worker.interfaces import JobStatusReporter

logger = logging.getLogger("RAG-Worker.Services.Reporting")

class RedisJobStatusReporter(JobStatusReporter):
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def report_success(self, doc_id: str, filename: str, chunk_count: int):
        # 1. Update Document Metadata
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "status": "synced",
            "timestamp": datetime.now().isoformat(),
        }
        await self.redis_client.hset("rag_documents", doc_id, json.dumps(metadata))
        
        # 2. Publish Event
        await self._publish_update(doc_id, "completed", "File synced successfully.")
        logger.info(f"Reported success for {doc_id}: {chunk_count} chunks.")

    async def report_failure(self, doc_id: str, filename: str, error_message: str):
        # 1. Update Document Metadata
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
        }
        await self.redis_client.hset("rag_documents", doc_id, json.dumps(metadata))

        # 2. Publish Event
        await self._publish_update(doc_id, "failed", error_message)
        logger.error(f"Reported failure for {doc_id}: {error_message}")

    async def _publish_update(self, doc_id: str, status: str, msg: str):
        payload = json.dumps(
            {"type": "job_update", "doc_id": doc_id, "status": status, "message": msg}
        )
        await self.redis_client.publish("job_updates", payload)