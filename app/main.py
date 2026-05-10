from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path

from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.database.seed import seed_initial_permissions, seed_initial_user
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)
from app.infrastructure.utils.logging import configure_logging
from app.presentation.rest.errors.handlers import app_exception_handler
from app.presentation.rest.routers.auth_router import router as auth_router
from app.presentation.rest.routers.marriage_router import router as marriage_router
from app.presentation.rest.routers.permission_router import router as permission_router
from app.presentation.rest.routers.person_router import router as person_router
from app.presentation.rest.routers.role_router import router as role_router
from app.presentation.rest.routers.user_router import router as user_router
from app.presentation.rest.utils.dependencies import get_uow
from app.presentation.rest.utils.trace_id import TraceIDMiddleware
from app.utils.app_exception import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context.

    This function runs during application startup and shutdown.
    It is used to initialize required resources and perform startup tasks.

    Startup tasks:
        - Seed default permissions into the database if they do not exist.
        - Seed the initial administrative user.
    """
    uow = get_uow()
    password_hasher = Argon2PasswordHasher()

    await seed_initial_permissions(
        uow=uow,
    )

    await seed_initial_user(uow=uow, password_hasher=password_hasher)

    yield


app = FastAPI(
    lifespan=lifespan,
    title="Family Tree API",
    version="1.0.0",
    redoc_url="/redoc",
    openapi_version="3.0.3",
    openapi_url="/openapi.json",
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
def neo4j_health():
    """
    Health check endpoint for Neo4j database.

    Executes a minimal read query to verify connectivity with
    the Neo4j database instance.

    Returns:
        dict: Health status indicating whether Neo4j is reachable.
    """
    result = neo4j_client.execute_read("RETURN 1 AS ok", params={})
    return {"neo4j": result[0]["ok"]}


# Middleware for request tracing
app.add_middleware(TraceIDMiddleware)

# Global application exception handler
app.add_exception_handler(AppException, app_exception_handler)

# Register API routers
app.include_router(person_router)
app.include_router(marriage_router)
app.include_router(user_router)
app.include_router(permission_router)
app.include_router(role_router)
app.include_router(auth_router)

# Configure application logging
configure_logging()
