from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from swagger_ui_bundle import swagger_ui_path

from app.core.config import settings
from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.database.seed import seed_initial_permissions, seed_initial_user
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.storage.minio_bootstrap import ensure_minio_buckets
from app.infrastructure.utils.logging import configure_logging
from app.presentation.dependencies import get_uow
from app.presentation.graphql.schema import graphql_router
from app.presentation.rest.errors.handlers import app_exception_handler
from app.presentation.rest.routers.auth_router import router as auth_router
from app.presentation.rest.routers.family_tree_router import (
    router as family_tree_router,
)
from app.presentation.rest.routers.marriage_router import router as marriage_router
from app.presentation.rest.routers.media_router import (
    upload_router as media_upload_router,
)
from app.presentation.rest.routers.permission_router import router as permission_router
from app.presentation.rest.routers.person_router import router as person_router
from app.presentation.rest.routers.role_router import router as role_router
from app.presentation.rest.routers.ticket_router import router as ticket_router
from app.presentation.rest.routers.tree_excel_router import router as tree_excel_router
from app.presentation.rest.routers.user_router import router as user_router
from app.presentation.rest.utils.security_headers import SecurityHeadersMiddleware
from app.presentation.rest.utils.trace_id import TraceIDMiddleware
from app.utils.app_exception import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context.

    This function runs during application startup and shutdown.
    It is used to initialize required resources and perform startup tasks.

    Startup tasks:
        - Ensure configured MinIO buckets exist.
        - Seed default permissions into the database if they do not exist.
        - Seed the initial administrative user.
    """
    await ensure_minio_buckets()

    uow = get_uow()
    password_hasher = Argon2PasswordHasher()

    await seed_initial_permissions(
        uow=uow,
    )

    await seed_initial_user(uow=uow, password_hasher=password_hasher)

    yield

    await neo4j_client.close()


app = FastAPI(
    lifespan=lifespan,
    title="Family Tree API",
    version="0.1.0",
    docs_url=None,
    redoc_url="/redoc",
    openapi_version="3.0.3",
    openapi_url="/openapi.json",
    redirect_slashes=False,
)

# Serve Swagger UI static assets locally instead of using CDN
app.mount("/swagger", StaticFiles(directory=swagger_ui_path), name="swagger")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["openapi"] = "3.0.3"
    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/api_docs", include_in_schema=False)
async def custom_swagger_ui():
    """
    Custom Swagger UI endpoint.

    Serves the Swagger documentation using locally bundled
    Swagger UI assets instead of relying on external CDNs.

    Returns:
        HTMLResponse: Swagger UI interface for API documentation.
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Docs",
        swagger_js_url="/swagger/swagger-ui-bundle.js",
        swagger_css_url="/swagger/swagger-ui.css",
    )


@app.get("/health/neo4j")
async def neo4j_health():
    """
    Health check endpoint for Neo4j database.

    Executes a minimal read query to verify connectivity with
    the Neo4j database instance.

    Returns:
        dict: Health status indicating whether Neo4j is reachable.
    """
    try:
        await neo4j_client.execute_read("RETURN 1 AS ok", params={})
        return {"status": "ok"}
    except (ConnectionError, TimeoutError, RuntimeError):
        return JSONResponse(
            {"status": "error"},
            status_code=503,
            headers={"Content-Type": "application/json"},
        )


@app.get("/health")
async def health():
    """
    Liveness/readiness probe for Compose HEALTHCHECK and load balancers.

    Returns HTTP 200 only when Postgres and Neo4j both respond.
    Returns HTTP 503 with ``status: degraded`` when any dependency fails so
    ``curl -fsS`` / orchestrators treat the instance as unhealthy.
    """
    status: dict[str, str] = {}
    healthy = True

    try:
        uow = get_uow()
        async with uow:
            await uow.session.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except (ConnectionError, TimeoutError, RuntimeError):
        status["postgres"] = "error"
        healthy = False

    try:
        result = await neo4j_client.execute_read("RETURN 1 AS ok", params={})
        status["neo4j"] = "ok" if result and result[0].get("ok") == 1 else "error"
        if status["neo4j"] != "ok":
            healthy = False
    except (ConnectionError, TimeoutError, RuntimeError):
        status["neo4j"] = "error"
        healthy = False

    status["status"] = "ok" if healthy else "degraded"
    return JSONResponse(
        content=status,
        status_code=200 if healthy else 503,
    )


# Middleware for request tracing
app.add_middleware(TraceIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

# Global application exception handler
app.add_exception_handler(AppException, app_exception_handler)

# Register API routers
app.include_router(family_tree_router)
app.include_router(person_router, prefix="/family-trees/{tree_id}")
app.include_router(media_upload_router, prefix="/family-trees/{tree_id}")
app.include_router(marriage_router, prefix="/family-trees/{tree_id}")
app.include_router(tree_excel_router, prefix="/family-trees/{tree_id}")
app.include_router(user_router)
app.include_router(permission_router)
app.include_router(role_router)
app.include_router(ticket_router)
app.include_router(auth_router)
app.include_router(graphql_router)

# Configure application logging
configure_logging()
