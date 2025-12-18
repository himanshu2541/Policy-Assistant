import logging
from langchain_core.documents import Document
from rag_worker.interfaces import JobStatusReporter
from shared.config import config
from rag_worker.providers.splitter import TextSplitterFactory

logger = logging.getLogger("RAG-Worker.Services.Ingestion")

class IngestionService:
    def __init__(self, vector_store, status_reporter: JobStatusReporter):
        self.vector_store = vector_store
        self.reporter = status_reporter
        self.splitter = TextSplitterFactory.get_splitter(config)

    async def ingest(self, doc_id: str, raw_text: str, filename: str = "Unknown"):
        if not raw_text:
            logger.warning(f"No text extracted for document {doc_id}")
            await self.reporter.report_failure(doc_id, filename, "No text extracted from document.")
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
                await self.reporter.report_success(doc_id, filename, len(documents))
            else:
                await self.reporter.report_failure(doc_id, filename, "No chunks created from text.")
        except Exception as e:
            logger.error(f"Failed to ingest document: {doc_id}: {e}")
            await self.reporter.report_failure(doc_id, filename, str(e))