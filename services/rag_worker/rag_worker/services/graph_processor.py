import asyncio
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from shared.providers.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphProcessor:
    def __init__(self, llm: BaseChatModel, neo4j_client: Neo4jClient):
        self.llm = llm
        self.graph = neo4j_client
        # Executor for blocking DB operations
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def process_chunk(self, text_chunk: str):
        """
        Asynchronously extracts relations and ingests them.
        Uses native async LLM calls and threaded DB writes.
        """
        try:
            # Non-blocking LLM Call (Native LangChain Async)
            # This yields control to the event loop while waiting for OpenAI
            relations_content = await self._extract_relations(text_chunk)

            # Blocking DB Call (Offloaded to Thread)
            # Neo4j driver is sync, so we run it in a thread to keep loop responsive
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.executor, self._ingest_relations, relations_content
            )

        except Exception as e:
            logger.error(f"Error processing graph chunk: {e}")

    async def _extract_relations(self, text: str) -> str:
        """
        Uses LangChain's ainvoke for async generation.
        """
        prompt = f"""
        You are an expert Knowledge Graph extractor. 
        Task: Convert the unstructured text below into a strict list of relationships.
        Format: Subject|SubjectType|RELATION|Object|ObjectType

        ### 1. Examples (Follow these patterns closely)
        
        Input: "Apple CEO Tim Cook announced the iPhone 15 in California."
        Output:
        Tim Cook|Person|CEO_OF|Apple|Company
        Apple|Company|ANNOUNCED|iPhone 15|Product
        iPhone 15|Product|UNVEILED_AT|California|Location

        Input: "Obsidian Trust funneled $200 million to Zenith AI."
        Output:
        Obsidian Trust|Company|FUNDED_WITH|$200 million|Money
        Obsidian Trust|Company|SENT_MONEY_TO|Zenith AI|Company

        Input: "Sarah Vane is the VP of Global Horizon Bank."
        Output:
        Sarah Vane|Person|HAS_TITLE|VP|Role
        Sarah Vane|Person|WORKS_AT|Global Horizon Bank|Company

        ### 2. Rules (Critical)
        1. **NO MARKDOWN**: Do not use code blocks (```), tables, or bold text. Just raw text lines.
        2. **RELATION Style**: MUST be UPPER_CASE_WITH_UNDERSCORES. No spaces. Max 25 chars.
           - CORRECT: LOCATED_IN, FILED_LAWSUIT_AGAINST, HAS_SISTER
           - WRONG: Located in, filed lawsuit, sister of
        3. **Entity Types**: Use PascalCase (e.g., Person, Company, Product, Project).
        4. **Granularity**: Extract hidden connections (family, financial flows, legal disputes).
        5. **One relationship per line**.

        ### 3. Text to Process
        {text}
        """
        # invoke/ainvoke expects a list of messages
        messages = [HumanMessage(content=prompt)]

        # Native async call supported by ChatOpenAI
        response = await self.llm.ainvoke(messages)
        if isinstance(response, list):
            return "".join(str(x) for x in response).strip()
        return str(response).strip()

    def _ingest_relations(self, raw_output: str):
        """
        Synchronous logic for DB insertion (run in thread).
        """
        for line in raw_output.split("\n"):
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue

            subj, subj_type, rel, obj, obj_type = parts[:5]

            # Sanitize inputs
            subj = subj.replace("'", "\\'")
            obj = obj.replace("'", "\\'")
            rel = re.sub(r"[^a-zA-Z0-9_]", "_", rel).upper().strip("_")
            subj_type = re.sub(r"[^a-zA-Z0-9]", "", subj_type).capitalize()
            obj_type = re.sub(r"[^a-zA-Z0-9]", "", obj_type).capitalize()

            if not rel or not subj_type or not obj_type:
                continue

            cypher = (
                f"MERGE (a:{subj_type} {{id: '{subj}'}}) "
                f"MERGE (b:{obj_type} {{id: '{obj}'}}) "
                f"MERGE (a)-[:{rel}]->(b)"
            )
            self.graph.execute_query(cypher)
