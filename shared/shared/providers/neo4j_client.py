# shared/shared/providers/neo4j_client.py
from neo4j import GraphDatabase, Driver
from shared.config import config
import logging
from typing import cast
try:
    from typing import LiteralString
except Exception:
    from typing_extensions import LiteralString 

logger = logging.getLogger(__name__)


class Neo4jClient:
    _instance = None

    def __init__(self):
        self._driver: Driver = GraphDatabase.driver(
            config.NEO4J_URI, auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def close(self):
        if self._driver:
            self._driver.close()

    def verify_connectivity(self):
        try:
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def execute_query(self, query: str, parameters: dict = {}):
        """
        Executes a write transaction.
        """
        with self._driver.session() as session:
            result = session.execute_write(
                lambda tx: tx.run(cast(LiteralString, query), parameters or {}).data()
            )
            return result

    def execute_read(self, query: str, parameters: dict = {}):
        """
        Executes a read transaction.
        """
        with self._driver.session() as session:
            result = session.execute_read(
                lambda tx: tx.run(cast(LiteralString, query), parameters or {}).data()
            )
            return result

    def setup_indexes(self):
        """
        Creates Full-Text Search index for fuzzy matching.
        """
        index_query = """
            CREATE FULLTEXT INDEX entity_index IF NOT EXISTS
            FOR (n:Person|Organization|Company|Product|Project|Location|Event|Role|Policy)
            ON EACH [n.id]
        """
        try:
            self.execute_query(index_query)
            logger.info("Neo4j Full-Text Search Indexes configured.")
        except Exception as e:
            logger.warning(f"Index setup skipped or failed: {e}")
