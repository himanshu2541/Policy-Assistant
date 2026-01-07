import asyncio
import logging
from langchain_core.documents import Document
from rag_worker.interfaces import JobStatusReporter
from shared.config import config
from rag_worker.providers.splitter import TextSplitterFactory

from shared.providers.neo4j_client import Neo4jClient
from rag_worker.services.graph_processor import GraphProcessor

logger = logging.getLogger("RAG-Worker.Services.Ingestion")

class IngestionService:
    def __init__(self, vector_store, status_reporter: JobStatusReporter, llm):
        self.vector_store = vector_store
        self.reporter = status_reporter
        self.splitter = TextSplitterFactory.get_splitter(config)
        
        self.neo4j_client = Neo4jClient.get_instance()
        self.graph_processor = GraphProcessor(llm, self.neo4j_client)
        # Limit concurrent LLM calls to 5 to avoid Rate Limits
        self.semaphore = asyncio.Semaphore(5)

    async def ingest(self, doc_id: str, raw_text: str, filename: str = "Unknown"):
        if not raw_text:
            logger.warning(f"No text extracted for document {doc_id}")
            await self.reporter.report_failure(doc_id, filename, "No text extracted from document.")
            return
        try:
            # Split Text
            chunks = self.splitter.split_text(raw_text)

            # Vector Store Ingestion
            documents = [
                Document(
                    page_content=text, metadata={"doc_id": doc_id, "chunk_index": i}
                )
                for i, text in enumerate(chunks)
            ]

            if documents:
                self.vector_store.add_documents(documents)
                
                # We await it here to ensure the job is fully done before reporting success.
                # Since it uses asyncio.gather internally, it will be fast.
                logger.info(f"Starting Graph Extraction for {len(chunks)} chunks...")
                await self._process_graph_parallel(chunks)

                await self.reporter.report_success(doc_id, filename, len(documents))
            else:
                await self.reporter.report_failure(doc_id, filename, "No chunks created from text.")
                
        except Exception as e:
            logger.error(f"Failed to ingest document: {doc_id}: {e}")
            await self.reporter.report_failure(doc_id, filename, str(e))

    async def _process_graph_parallel(self, chunks: list[str]):
        """
        Helper method to process graph chunks in parallel with a semaphore.
        """
        tasks = []
        for chunk in chunks:
            tasks.append(self._bounded_graph_task(chunk))
        
        # Run all chunks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors (optional: you could fail the job if graph fails, 
        # but usually we want to keep the vector data even if graph fails partially)
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error(f"Graph ingestion encountered {len(errors)} errors. First error: {errors[0]}")

    async def _bounded_graph_task(self, chunk: str):
        """Acquire semaphore -> Process -> Release"""
        async with self.semaphore:
            await self.graph_processor.process_chunk(chunk)