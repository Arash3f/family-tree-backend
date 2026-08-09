"""The Bruno collection is hand-written, so nothing stops it from drifting away
from the routes the app actually serves. These tests compare the two.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from graphql import build_schema, parse
from graphql import validate as validate_document

from app.main import app
from app.presentation.graphql.schema import schema as graphql_schema

BRUNO_DIR = Path(__file__).resolve().parents[3] / "bruno"
ENVIRONMENT_FILE = BRUNO_DIR / "environments" / "Local.bru"

# Served by FastAPI itself or exercised through the GraphQL folder's query bodies.
ROUTES_WITHOUT_BRUNO_REQUEST = {
    ("GET", "/api_docs"),
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
    ("POST", "/graphql"),
    ("GET", "/graphql"),
}

METHOD_LINE = re.compile(
    r"^\s*(get|post|put|patch|delete|head|options)\s*\{", re.IGNORECASE
)
URL_LINE = re.compile(r"^\s*url:\s*(\S+)")
PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}")
PATH_PARAM = re.compile(r"\{[^}]+\}")
SEQ_LINE = re.compile(r"^\s*seq:\s*(\d+)\s*$", re.MULTILINE)
VARIABLE_USE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
GRAPHQL_QUERY = re.compile(r"^\s*query:\s*'''(.*?)'''", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class BrunoRequest:
    file: Path
    method: str
    url: str

    @property
    def path(self) -> str:
        """The URL as a route template: `/users/{{user_id}}` -> `/users/{}`."""
        path = self.url.replace("{{base_url}}", "")
        path = PLACEHOLDER.sub("{}", path)
        # Bruno also supports `:name` path params, declared in a params:path block.
        path = re.sub(r":[A-Za-z_][A-Za-z0-9_]*", "{}", path)
        return path or "/"


def _parse(file: Path) -> BrunoRequest | None:
    method: str | None = None
    for line in file.read_text(encoding="utf-8").splitlines():
        if method is None:
            match = METHOD_LINE.match(line)
            if match:
                method = match.group(1).upper()
            continue
        url_match = URL_LINE.match(line)
        if url_match:
            return BrunoRequest(file=file, method=method, url=url_match.group(1))
    return None


def _bruno_requests() -> list[BrunoRequest]:
    requests = []
    for file in sorted(BRUNO_DIR.rglob("*.bru")):
        if file.parent.name == "environments" or file.name == "collection.bru":
            continue
        parsed = _parse(file)
        assert parsed is not None, f"{file.name} declares no HTTP method and url"
        requests.append(parsed)
    return requests


def _app_routes() -> set[tuple[str, str]]:
    routes = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        template = PATH_PARAM.sub("{}", route.path)
        for method in route.methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.add((method, template))
    return routes


def _request_files() -> list[Path]:
    return [
        file
        for file in sorted(BRUNO_DIR.rglob("*.bru"))
        if file.parent.name != "environments" and file.name != "collection.bru"
    ]


def _defined_variables() -> set[str]:
    names = set()
    for raw in ENVIRONMENT_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line in {"vars {", "}"} or ":" not in line:
            continue
        names.add(line.split(":", 1)[0].strip())
    return names


BRUNO_REQUESTS = _bruno_requests()


def test_the_collection_is_not_empty():
    assert len(BRUNO_REQUESTS) > 30


@pytest.mark.parametrize(
    "request_",
    BRUNO_REQUESTS,
    ids=lambda request_: str(request_.file.relative_to(BRUNO_DIR)),
)
def test_every_bruno_request_hits_a_real_route(request_: BrunoRequest):
    assert (request_.method, request_.path) in _app_routes(), (
        f"{request_.method} {request_.path} is not served by the app; "
        "the collection is stale"
    )


def test_every_route_has_a_bruno_request():
    covered = {(request_.method, request_.path) for request_ in BRUNO_REQUESTS}
    missing = _app_routes() - covered - ROUTES_WITHOUT_BRUNO_REQUEST
    assert not missing, f"endpoints with no Bruno request: {sorted(missing)}"


def test_graphql_bodies_are_valid_against_the_schema():
    """Catches queries left behind by a schema change, such as a resolver that
    gained a required `treeId` argument."""
    sdl = build_schema(graphql_schema.as_str())
    problems = []
    for file in _request_files():
        match = GRAPHQL_QUERY.search(file.read_text(encoding="utf-8"))
        if not match:
            continue
        for error in validate_document(sdl, parse(match.group(1))):
            problems.append(f"{file.name}: {error.message}")
    assert not problems, problems


def test_sequence_numbers_are_unique_within_a_folder():
    """Bruno orders a folder by `seq`; duplicates make the order arbitrary."""
    by_folder: dict[Path, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    for file in _request_files():
        match = SEQ_LINE.search(file.read_text(encoding="utf-8"))
        assert match is not None, f"{file.name} declares no seq"
        by_folder[file.parent][int(match.group(1))].append(file.name)

    clashes = {
        f"{folder.name}/{seq}": names
        for folder, seqs in by_folder.items()
        for seq, names in seqs.items()
        if len(names) > 1
    }
    assert not clashes, f"duplicate seq numbers: {clashes}"


def test_requests_only_use_variables_the_environment_defines():
    defined = _defined_variables()
    undefined = {}
    for file in _request_files():
        used = set(VARIABLE_USE.findall(file.read_text(encoding="utf-8")))
        if used - defined:
            undefined[file.name] = sorted(used - defined)
    assert not undefined, f"{ENVIRONMENT_FILE.name} is missing: {undefined}"


def test_tree_scoped_requests_use_the_tree_id_variable():
    """Persons and marriages are tenant-scoped; a request without `tree_id`
    would silently exercise the wrong URL shape."""
    for request_ in BRUNO_REQUESTS:
        folder = request_.file.parent.name
        if folder in {"Persons", "Marriages"}:
            assert "{{tree_id}}" in request_.url, f"{request_.file.name} drops tree_id"
