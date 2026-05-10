import logging
from typing import Any, LiteralString

from neo4j import GraphDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=1000,
            connection_timeout=5,
        )

        self.setup_database()

    def setup_database(self) -> None:
        query = """
        CREATE CONSTRAINT person_id_unique IF NOT EXISTS
        FOR (p:Person)
        REQUIRE p.id IS UNIQUE
        """
        try:
            self.execute_write(query, params={})
            logger.info("Neo4j constraints initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j constraints: {e}")

    def close(self):
        self._driver.close()

    def execute_write(self, query: LiteralString, **params):
        with self._driver.session() as session:
            return session.execute_write(self._run_query, query, **params)

    def execute_read(self, query: LiteralString, **params):
        if params == {}:
            params = {"params": {}}
        print("params", params)
        with self._driver.session() as session:
            return session.execute_read(self._run_query, query, **params)

    @staticmethod
    def _run_query(tx, query: LiteralString, params: Any):
        query_params = params.model_dump() if params else {"params": {}}
        result = tx.run(query, **query_params)
        return [record.data() for record in result]


neo4j_client = Neo4jClient()
