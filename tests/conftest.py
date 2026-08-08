"""Make host-side pytest work when .env uses Docker DNS names (db/neo4j)."""

import os
import socket
from pathlib import Path


def _host_resolves(hostname: str) -> bool:
    try:
        socket.getaddrinfo(hostname, None)
        return True
    except OSError:
        return False


def _dotenv_get(key: str) -> str | None:
    env_path = Path(".env")
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return None


def _effective(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key) or _dotenv_get(key) or default


def _remap_docker_dns_for_host():
    pg_host = _effective("POSTGRES_HOST_TEST") or _effective("POSTGRES_HOST", "db")
    if pg_host and not _host_resolves(pg_host):
        os.environ["POSTGRES_HOST"] = "127.0.0.1"
        os.environ["POSTGRES_HOST_TEST"] = "127.0.0.1"
        # Host-published Postgres port from docker/compose.yml
        publish = _effective("POSTGRES_PUBLISH_PORT", "5432") or "5432"
        os.environ.setdefault("POSTGRES_PORT", publish)
        os.environ.setdefault("POSTGRES_PORT_TEST", publish)
        os.environ.setdefault(
            "POSTGRES_DB_TEST",
            _effective("POSTGRES_DB_TEST", "family_tree_test") or "family_tree_test",
        )

    neo4j_uri = _effective("NEO4J_URI", "bolt://neo4j:7687") or "bolt://neo4j:7687"
    if "://" in neo4j_uri:
        neo_host = neo4j_uri.split("://", 1)[1].split(":", 1)[0]
        if neo_host and not _host_resolves(neo_host):
            bolt_port = _effective("NEO4J_BOLT_PORT", "7687") or "7687"
            os.environ["NEO4J_URI"] = f"bolt://127.0.0.1:{bolt_port}"


# Must run at import time so env is fixed before Settings / engines load.
_remap_docker_dns_for_host()


def pytest_configure():
    _remap_docker_dns_for_host()
