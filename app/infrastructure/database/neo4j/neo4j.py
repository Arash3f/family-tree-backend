import asyncio
import logging
from typing import Any, LiteralString

from neo4j import AsyncGraphDatabase, AsyncManagedTransaction

from app.core.config import settings
from app.infrastructure.database.neo4j.neo4j_queries import CONSTRAINT_PERSON_ID

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    High-level client wrapper for interacting with the Neo4j database.

    This class encapsulates the async Neo4j driver and provides simplified
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
        Initialize the Neo4j async driver.

        Configuration values are loaded from application settings.

        Note:
            Driver construction itself is synchronous (it does not open a
            connection eagerly), but database constraint setup requires an
            awaited call and therefore cannot happen inside ``__init__``.
            Callers must await :meth:`setup_database` separately (see
            ``Neo4jClient.create`` / ``_LazyNeo4jClient._get``).

        Raises:
            neo4j.exceptions.Neo4jError:
                If the driver fails to initialize.
        """

        self._driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=1000,
            connection_timeout=5,
        )

    @classmethod
    async def create(cls) -> "Neo4jClient":
        """
        Async factory: build the client and ensure database constraints exist.

        ``__init__`` cannot be async, so the constraint-setup step (which
        needs to `await` a write transaction) is performed here instead.
        """

        client = cls()
        await client.setup_database()
        return client

    async def setup_database(self) -> None:
        """
        Initialize required database constraints and indexes.

        This method is called during client initialization to ensure
        the database schema prerequisites exist.

        Current constraints:
            - Person node unique ID constraint

        Errors are logged but do not stop application startup.
        """

        try:
            await self.execute_write(CONSTRAINT_PERSON_ID, params={})
            logger.info("Neo4j constraints initialized successfully.")
        except (RuntimeError, ConnectionError) as e:
            logger.error(f"Failed to initialize Neo4j constraints: {e}")

    async def close(self) -> None:
        """
        Close the underlying Neo4j driver.

        Should be called during application shutdown to properly release
        network resources and connection pools.
        """

        await self._driver.close()

    async def execute_write(self, query: LiteralString, **params):
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
            await neo4j_client.execute_write(
                "CREATE (p:Person {id: $id, name: $name}) RETURN p",
                params={"id": "123", "name": "Arash"}
            )
        """

        async with self._driver.session() as session:
            return await session.execute_write(self._run_query, query, **params)

    async def execute_read(self, query: LiteralString, **params):
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

        async with self._driver.session() as session:
            return await session.execute_read(self._run_query, query, **params)

    @staticmethod
    async def _run_query(
        tx: AsyncManagedTransaction, query: LiteralString, params: Any
    ):
        """
        Internal helper used by Neo4j transactions.

        This method is passed to the Neo4j session transaction executor
        (`execute_read` / `execute_write`) and is responsible for:

        - Normalizing query parameters
        - Executing the Cypher query
        - Transforming result records into dictionaries

        Args:
            tx:
                Active async Neo4j transaction.
            query:
                Cypher query string.
            params:
                Query parameters object. If a Pydantic model is provided,
                it will be converted to a dictionary using `model_dump()`.

        Returns:
            list[dict]:
                List of query result records.
        """

        # Convert Pydantic models to JSON-compatible dict (Neo4j rejects UUID objects)
        if hasattr(params, "model_dump"):
            query_params = params.model_dump(mode="json")
        elif params:
            query_params = params
        else:
            query_params = {}

        result = await tx.run(query, **query_params)

        # Convert Neo4j Record objects to plain dictionaries
        return [record.data() async for record in result]


class _LazyNeo4jClient:
    """Defer driver creation until first use; support close on shutdown.

    Driver/constraint initialization is async, so it cannot happen inside
    ``__getattr__`` directly (a sync dunder). Instead, every proxied
    attribute access resolves to a small async wrapper that awaits the
    lazily-created ``Neo4jClient`` (via ``_get()``) and then awaits the
    requested method on it. Callers still just do
    ``await neo4j_client.execute_read(...)`` as before.
    """

    def __init__(self) -> None:
        self._client: Neo4jClient | None = None
        self._init_lock = asyncio.Lock()

    async def _get(self) -> Neo4jClient:
        if self._client is not None:
            return self._client
        # Two concurrent first-callers (e.g. two requests racing right after
        # a cold start) would otherwise both see `_client is None`, each
        # construct its own driver, and one silently overwrite the other's
        # reference -- leaking that driver's connection pool since it's
        # never closed. The lock ensures only one construction wins.
        async with self._init_lock:
            if self._client is None:
                self._client = await Neo4jClient.create()
        return self._client

    def __getattr__(self, name: str):
        async def _proxy(*args, **kwargs):
            client = await self._get()
            attr = getattr(client, name)
            return await attr(*args, **kwargs)

        return _proxy

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


# Lazy singleton — connects on first query, closed in app lifespan
neo4j_client = _LazyNeo4jClient()
