import logging
from typing import Any, LiteralString

from neo4j import GraphDatabase

from app.core.config import settings
from app.infrastructure.database.neo4j.neo4j_queries import CONSTRAINT_PERSON_ID

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    High-level client wrapper for interacting with the Neo4j database.

    This class encapsulates the Neo4j driver and provides simplified
    methods for executing read and write queries using managed sessions.

    Responsibilities:
        - Initialize Neo4j driver
        - Ensure database constraints exist
        - Provide helper methods for read/write transactions
        - Normalize query parameter handling
        - Convert Neo4j records into Python dictionaries
    """

    def __init__(self):
        """
        Initialize the Neo4j driver and ensure database constraints exist.

        Configuration values are loaded from application settings.

        Raises:
            neo4j.exceptions.Neo4jError:
                If the driver fails to initialize.
        """

        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=1000,
            connection_timeout=5,
        )

        # Ensure required database constraints exist
        self.setup_database()

    def setup_database(self) -> None:
        """
        Initialize required database constraints and indexes.

        This method is called during client initialization to ensure
        the database schema prerequisites exist.

        Current constraints:
            - Person node unique ID constraint

        Errors are logged but do not stop application startup.
        """

        try:
            self.execute_write(CONSTRAINT_PERSON_ID, params={})
            logger.info("Neo4j constraints initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j constraints: {e}")

    def close(self) -> None:
        """
        Close the underlying Neo4j driver.

        Should be called during application shutdown to properly release
        network resources and connection pools.
        """

        self._driver.close()

    def execute_write(self, query: LiteralString, **params):
        """
        Execute a write transaction against the database.

        This method opens a session and executes the provided Cypher query
        within a write transaction.

        Args:
            query:
                Cypher query string to execute.
            **params:
                Query parameters passed to the transaction.

        Returns:
            list[dict]:
                List of result records converted to dictionaries.

        Example:
            neo4j_client.execute_write(
                "CREATE (p:Person {id: $id, name: $name}) RETURN p",
                params={"id": "123", "name": "Arash"}
            )
        """

        with self._driver.session() as session:
            return session.execute_write(self._run_query, query, **params)

    def execute_read(self, query: LiteralString, **params):
        """
        Execute a read transaction against the database.

        Args:
            query:
                Cypher query string to execute.
            **params:
                Query parameters passed to the transaction.

        Returns:
            list[dict]:
                Query results as a list of dictionaries.

        Notes:
            If no parameters are provided, an empty parameter object is used
            to maintain consistent query execution behavior.
        """

        if params == {}:
            params = {"params": {}}

        logger.debug("Neo4j read query params: %s", params)

        with self._driver.session() as session:
            return session.execute_read(self._run_query, query, **params)

    @staticmethod
    def _run_query(tx, query: LiteralString, params: Any):
        """
        Internal helper used by Neo4j transactions.

        This method is passed to the Neo4j session transaction executor
        (`execute_read` / `execute_write`) and is responsible for:

        - Normalizing query parameters
        - Executing the Cypher query
        - Transforming result records into dictionaries

        Args:
            tx:
                Active Neo4j transaction.
            query:
                Cypher query string.
            params:
                Query parameters object. If a Pydantic model is provided,
                it will be converted to a dictionary using `model_dump()`.

        Returns:
            list[dict]:
                List of query result records.
        """

        # Convert Pydantic models to dictionary if necessary
        query_params = params.model_dump() if params else {"params": {}}

        result = tx.run(query, **query_params)

        # Convert Neo4j Record objects to plain dictionaries
        return [record.data() for record in result]


# Singleton instance used across the application
neo4j_client = Neo4jClient()
