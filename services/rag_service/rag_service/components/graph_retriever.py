import re
import logging
from shared.providers.neo4j_client import Neo4jClient
from langchain_core.messages import HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

class GraphRetriever:
    def __init__(self, neo4j_client: Neo4jClient, llm: BaseChatModel):
        self.graph = neo4j_client
        self.llm = llm

    def get_context(self, question: str) -> str:
        """
        Orchestrates the Graph RAG retrieval:
        1. Extract Entities from Question.
        2. Map to Graph Nodes (Fuzzy Search).
        3. Retrieve Paths (Deep Search).
        """
        entities = self._extract_query_entities(question)
        if not entities:
            return ""

        valid_ids = []
        for entity in entities:
            node_id = self._fuzzy_search_node(entity)
            if node_id:
                valid_ids.append(node_id)

        if not valid_ids:
            return ""

        return self._retrieve_paths(valid_ids)

    def _extract_query_entities(self, question: str) -> list[str]:
        prompt = f"""
        Task: Identify the key **Graph Nodes** (Proper Nouns) to search for in the database.
        
        ### Critical Rules
        1. **Strip Roles**: If the user asks about a Job Title (e.g., "CEO of Apple"), extract **ONLY** the Company Name ("Apple"). The Graph will find the CEO.
        2. **Multi-Hop Queries**: If asking about a connection between A and B, extract **BOTH** A and B.
        3. **Precise Naming**: Extract exact names of Projects, Products, or Companies.

        ### Examples
        Input: "Why is Ironclad suing Nebula?"
        Output: Ironclad|Nebula

        Input: "Who transported the K-900 chips?"
        Output: K-900 chips

        Input: "How is the Vice President of Global Horizon Bank connected to Chimera?"
        Output: Global Horizon Bank|Chimera
        (Reason: 'Vice President' is a generic title. We search 'Global Horizon Bank' to find the person.)

        Input: "Connection between Sarah and the Director of Apex."
        Output: Sarah|Apex

        ### Current Question
        Question: "{question}"
        Output (Pipe separated):
        """
        content = self.llm.invoke([HumanMessage(content=prompt)]).content
        if isinstance(content, list):
            raw = "".join(str(x) for x in content).strip()
        else:
            raw = str(content).strip()

        # Cleaning: Remove "Output:" or "Entity:" prefixes
        clean = re.sub(r"(Output|Entity\d*)[:\s=]*", "", raw, flags=re.IGNORECASE)

        # Split and Filter
        parts = [p.strip() for p in re.split(r"[|,\n]", clean) if p.strip()]
        blacklist = ["output", "question", "answer", "unknown", "a", "b"]
        return [p for p in parts if p.lower() not in blacklist]

    def _fuzzy_search_node(self, text: str):
        clean_text = text.replace(":", "").replace(" ", " AND ") + "~"
        query = f"""
        CALL db.index.fulltext.queryNodes("entity_index", '{clean_text}') YIELD node, score
        RETURN node.id as id, score
        ORDER BY score DESC LIMIT 1
        """
        result = self.graph.execute_read(query)
        if result:
            return result[0]['id']
        return None

    def _retrieve_paths(self, entity_ids: list[str]) -> str:
        if len(entity_ids) == 1:
            # Neighborhood Search
            target = entity_ids[0]
            query = f"""
            MATCH (n)-[*1..2]-(m) 
            WHERE n.id = '{target}' 
            RETURN distinct n.id as source, m.id as target LIMIT 50
            """
            result = self.graph.execute_read(query)
            return str(result)
        
        elif len(entity_ids) >= 2:
            # Deep Path Search
            start, end = entity_ids[0], entity_ids[1]
            query = f"""
            MATCH p=(a)-[*1..4]-(b) 
            WHERE a.id = '{start}' AND b.id = '{end}' 
            RETURN p LIMIT 5
            """
            result = self.graph.execute_read(query)
            return str(result)
        return ""