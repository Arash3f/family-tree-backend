"""OAuth 2.1 authorization server bits required by ChatGPT remote MCP."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.token_service import TokenService
from app.core.config import settings
from app.domain.exceptions.oauth_exceptions import (
    OAuthConsentNotFoundException,
    OAuthError,
)
from app.infrastructure.database.models.oauth_model import (
    OAuthAuthorizationCodeModel,
    OAuthClientModel,
    OAuthConsentRequestModel,
    OAuthRefreshTokenModel,
)
from app.presentation.oauth.constants import (
    AUTH_CODE_TTL_MINUTES,
    CIMD_ALLOWED_HOST_SUFFIXES,
    CONSENT_TTL_MINUTES,
    MCP_ACCESS_TOKEN_TYPE,
    MCP_ACCESS_TTL_MINUTES,
    MCP_REFRESH_TTL_DAYS,
    MCP_SCOPE,
)


@dataclass(frozen=True)
class ConsentRequestView:
    id: UUID
    client_id: str
    client_name: str
    redirect_uri: str
    resource: str
    scope: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenBundle:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str
    token_type: str = "Bearer"


def _b64url_sha256(value: str) -> str:
    digest = hashlib.sha256(value.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _host_allowed(host: str) -> bool:
    host = host.lower().strip(".")
    for suffix in CIMD_ALLOWED_HOST_SUFFIXES:
        if host == suffix or host.endswith("." + suffix):
            return True
    return False


class McpOAuthService:
    def __init__(self, session: AsyncSession, token_service: TokenService):
        self.session = session
        self.token_service = token_service

    # --- discovery helpers -------------------------------------------------

    def resource_metadata(self) -> dict[str, Any]:
        resource = settings.mcp_resource_url
        return {
            "resource": resource,
            "authorization_servers": [settings.oauth_issuer],
            "scopes_supported": [MCP_SCOPE],
            "bearer_methods_supported": ["header"],
            "resource_documentation": settings.mcp_docs_url or None,
        }

    def authorization_server_metadata(self) -> dict[str, Any]:
        issuer = settings.oauth_issuer
        return {
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/oauth/authorize",
            "token_endpoint": f"{issuer}/oauth/token",
            "registration_endpoint": f"{issuer}/oauth/register",
            "revocation_endpoint": f"{issuer}/oauth/revoke",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
            "scopes_supported": [MCP_SCOPE],
            "client_id_metadata_document_supported": True,
            "authorization_response_iss_parameter_supported": True,
        }

    def www_authenticate(self) -> str:
        meta = f"{settings.oauth_issuer}/.well-known/oauth-protected-resource"
        return f'Bearer resource_metadata="{meta}", scope="{MCP_SCOPE}"'

    # --- clients (DCR + CIMD) ----------------------------------------------

    async def register_client(
        self,
        *,
        redirect_uris: list[str],
        client_name: str | None = None,
        token_endpoint_auth_method: str = "none",
    ) -> dict[str, Any]:
        if not redirect_uris:
            raise OAuthError(
                oauth_error="invalid_client_metadata",
                description="redirect_uris is required",
            )
        for uri in redirect_uris:
            self._assert_redirect_uri_shape(uri)

        client_id = str(uuid4())
        client_secret: str | None = None
        secret_hash: str | None = None
        if token_endpoint_auth_method != "none":
            client_secret = secrets.token_urlsafe(32)
            secret_hash = self.token_service.hash_token(client_secret)

        model = OAuthClientModel(
            id=client_id,
            name=(client_name or "MCP client").strip()[:200] or "MCP client",
            client_secret_hash=secret_hash,
            redirect_uris=list(redirect_uris),
            token_endpoint_auth_method=token_endpoint_auth_method,
            is_cimd=False,
        )
        self.session.add(model)
        await self.session.flush()

        payload: dict[str, Any] = {
            "client_id": client_id,
            "client_id_issued_at": int(datetime.now(UTC).timestamp()),
            "redirect_uris": list(redirect_uris),
            "token_endpoint_auth_method": token_endpoint_auth_method,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "client_name": model.name,
        }
        if client_secret:
            payload["client_secret"] = client_secret
        return payload

    async def resolve_client(self, client_id: str) -> OAuthClientModel:
        stmt = select(OAuthClientModel).where(OAuthClientModel.id == client_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        if client_id.startswith("https://"):
            return await self._resolve_cimd_client(client_id)

        raise OAuthError(
            oauth_error="invalid_client",
            description="Unknown client_id",
            status_code=401,
        )

    async def _resolve_cimd_client(self, client_id_url: str) -> OAuthClientModel:
        parsed = urlparse(client_id_url)
        if parsed.scheme != "https" or not parsed.hostname or not _host_allowed(parsed.hostname):
            raise OAuthError(
                oauth_error="invalid_client",
                description="CIMD client_id host is not allowed",
                status_code=401,
            )

        def _fetch() -> tuple[int, str]:
            req = Request(
                client_id_url,
                headers={"Accept": "application/json"},
                method="GET",
            )
            with urlopen(req, timeout=5) as resp:  # noqa: S310 — host allowlisted above
                return int(getattr(resp, "status", 200)), resp.read().decode("utf-8")

        try:
            status_code, body = await asyncio.to_thread(_fetch)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise OAuthError(
                oauth_error="invalid_client",
                description="Failed to fetch CIMD document",
                status_code=401,
            ) from exc

        if status_code != 200:
            raise OAuthError(
                oauth_error="invalid_client",
                description="CIMD document not found",
                status_code=401,
            )
        try:
            doc = json.loads(body)
        except json.JSONDecodeError as exc:
            raise OAuthError(
                oauth_error="invalid_client",
                description="CIMD document is not JSON",
                status_code=401,
            ) from exc

        redirect_uris = doc.get("redirect_uris") or []
        if not isinstance(redirect_uris, list) or not redirect_uris:
            raise OAuthError(
                oauth_error="invalid_client",
                description="CIMD document missing redirect_uris",
                status_code=401,
            )

        model = OAuthClientModel(
            id=client_id_url,
            name=str(doc.get("client_name") or "ChatGPT")[:200],
            client_secret_hash=None,
            redirect_uris=[str(u) for u in redirect_uris],
            token_endpoint_auth_method="none",
            is_cimd=True,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    # --- authorize / consent -----------------------------------------------

    async def start_authorization(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        resource: str | None,
        scope: str | None,
        state: str | None,
        response_type: str,
    ) -> str:
        """Validate the authorize request and return the frontend consent URL."""
        if not settings.MCP_ENABLED:
            raise OAuthError(
                oauth_error="temporarily_unavailable",
                description="MCP is disabled",
                status_code=503,
            )
        if not settings.oauth_consent_url:
            raise OAuthError(
                oauth_error="server_error",
                description="OAUTH_CONSENT_URL is not configured",
                status_code=503,
            )
        if response_type != "code":
            raise OAuthError(
                oauth_error="unsupported_response_type",
                description="Only response_type=code is supported",
            )
        if code_challenge_method != "S256":
            raise OAuthError(
                oauth_error="invalid_request",
                description="code_challenge_method must be S256",
            )
        if not code_challenge:
            raise OAuthError(
                oauth_error="invalid_request",
                description="code_challenge is required",
            )

        client = await self.resolve_client(client_id)
        if redirect_uri not in (client.redirect_uris or []):
            raise OAuthError(
                oauth_error="invalid_request",
                description="redirect_uri is not registered for this client",
            )

        resource_value = (resource or settings.mcp_resource_url).rstrip("/")
        if resource_value.rstrip("/") != settings.mcp_resource_url.rstrip("/"):
            raise OAuthError(
                oauth_error="invalid_target",
                description="resource does not match this MCP server",
            )

        scope_value = (scope or MCP_SCOPE).strip() or MCP_SCOPE
        if MCP_SCOPE not in scope_value.split():
            raise OAuthError(
                oauth_error="invalid_scope",
                description=f"scope must include {MCP_SCOPE}",
            )

        request_id = uuid4()
        self.session.add(
            OAuthConsentRequestModel(
                id=request_id,
                client_id=client.id,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                resource=resource_value,
                scope=MCP_SCOPE,
                state=state,
                expires_at=datetime.now(UTC) + timedelta(minutes=CONSENT_TTL_MINUTES),
            )
        )
        await self.session.flush()

        consent = settings.oauth_consent_url
        sep = "&" if "?" in consent else "?"
        return f"{consent}{sep}{urlencode({'request': str(request_id)})}"

    async def get_consent_request(self, request_id: UUID) -> ConsentRequestView:
        pending = await self._get_pending(request_id)
        client = await self.resolve_client(pending.client_id)
        return ConsentRequestView(
            id=pending.id,
            client_id=pending.client_id,
            client_name=client.name,
            redirect_uri=pending.redirect_uri,
            resource=pending.resource,
            scope=pending.scope,
            expires_at=pending.expires_at,
        )

    async def approve_consent(self, *, request_id: UUID, user_id: UUID) -> str:
        pending = await self._get_pending(request_id)
        code = secrets.token_urlsafe(32)
        self.session.add(
            OAuthAuthorizationCodeModel(
                id=uuid4(),
                code_hash=self.token_service.hash_token(code),
                client_id=pending.client_id,
                user_id=user_id,
                redirect_uri=pending.redirect_uri,
                code_challenge=pending.code_challenge,
                resource=pending.resource,
                scope=pending.scope,
                expires_at=datetime.now(UTC) + timedelta(minutes=AUTH_CODE_TTL_MINUTES),
            )
        )
        pending.consumed_at = datetime.now(UTC)
        await self.session.flush()

        params = {
            "code": code,
            "iss": settings.oauth_issuer,
        }
        if pending.state:
            params["state"] = pending.state
        sep = "&" if "?" in pending.redirect_uri else "?"
        return f"{pending.redirect_uri}{sep}{urlencode(params)}"

    async def deny_consent(self, *, request_id: UUID) -> str:
        pending = await self._get_pending(request_id)
        pending.consumed_at = datetime.now(UTC)
        await self.session.flush()
        params = {
            "error": "access_denied",
            "error_description": "The user denied the request",
            "iss": settings.oauth_issuer,
        }
        if pending.state:
            params["state"] = pending.state
        sep = "&" if "?" in pending.redirect_uri else "?"
        return f"{pending.redirect_uri}{sep}{urlencode(params)}"

    async def _get_pending(self, request_id: UUID) -> OAuthConsentRequestModel:
        stmt = select(OAuthConsentRequestModel).where(
            OAuthConsentRequestModel.id == request_id
        )
        result = await self.session.execute(stmt)
        pending = result.scalar_one_or_none()
        if (
            pending is None
            or pending.consumed_at is not None
            or pending.expires_at <= datetime.now(UTC)
        ):
            raise OAuthConsentNotFoundException(detail=[f"request_id={request_id}"])
        return pending

    # --- token endpoint ----------------------------------------------------

    async def exchange_authorization_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        code_verifier: str,
        resource: str | None,
    ) -> TokenBundle:
        client = await self.resolve_client(client_id)
        code_hash = self.token_service.hash_token(code)
        stmt = select(OAuthAuthorizationCodeModel).where(
            OAuthAuthorizationCodeModel.code_hash == code_hash
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if (
            row is None
            or row.consumed_at is not None
            or row.expires_at <= now
            or row.client_id != client.id
            or row.redirect_uri != redirect_uri
        ):
            raise OAuthError(
                oauth_error="invalid_grant",
                description="Invalid authorization code",
            )

        if _b64url_sha256(code_verifier) != row.code_challenge:
            raise OAuthError(
                oauth_error="invalid_grant",
                description="PKCE verification failed",
            )

        resource_value = (resource or row.resource).rstrip("/")
        if resource_value.rstrip("/") != row.resource.rstrip("/"):
            raise OAuthError(
                oauth_error="invalid_target",
                description="resource mismatch",
            )

        row.consumed_at = now
        return await self._issue_tokens(
            user_id=row.user_id,
            client_id=client.id,
            resource=row.resource,
            scope=row.scope,
        )

    async def exchange_refresh_token(
        self,
        *,
        refresh_token: str,
        client_id: str,
        resource: str | None,
    ) -> TokenBundle:
        client = await self.resolve_client(client_id)
        token_hash = self.token_service.hash_token(refresh_token)
        stmt = select(OAuthRefreshTokenModel).where(
            OAuthRefreshTokenModel.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if (
            row is None
            or row.revoked_at is not None
            or row.expires_at <= now
            or row.client_id != client.id
        ):
            raise OAuthError(
                oauth_error="invalid_grant",
                description="Invalid refresh token",
            )

        resource_value = (resource or row.resource).rstrip("/")
        if resource_value.rstrip("/") != row.resource.rstrip("/"):
            raise OAuthError(
                oauth_error="invalid_target",
                description="resource mismatch",
            )

        row.revoked_at = now
        return await self._issue_tokens(
            user_id=row.user_id,
            client_id=client.id,
            resource=row.resource,
            scope=row.scope,
        )

    async def revoke_refresh_token(self, token: str) -> None:
        token_hash = self.token_service.hash_token(token)
        stmt = select(OAuthRefreshTokenModel).where(
            OAuthRefreshTokenModel.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            await self.session.flush()

    async def _issue_tokens(
        self,
        *,
        user_id: UUID,
        client_id: str,
        resource: str,
        scope: str,
    ) -> TokenBundle:
        access = self.create_mcp_access_token(
            user_id=user_id, resource=resource, scope=scope
        )
        refresh = secrets.token_urlsafe(48)
        self.session.add(
            OAuthRefreshTokenModel(
                id=uuid4(),
                token_hash=self.token_service.hash_token(refresh),
                client_id=client_id,
                user_id=user_id,
                resource=resource,
                scope=scope,
                expires_at=datetime.now(UTC) + timedelta(days=MCP_REFRESH_TTL_DAYS),
            )
        )
        await self.session.flush()
        return TokenBundle(
            access_token=access,
            refresh_token=refresh,
            expires_in=MCP_ACCESS_TTL_MINUTES * 60,
            scope=scope,
        )

    def create_mcp_access_token(
        self, *, user_id: UUID, resource: str, scope: str
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": MCP_ACCESS_TOKEN_TYPE,
            "iss": settings.oauth_issuer,
            "aud": resource,
            "scope": scope,
            "iat": now - timedelta(seconds=5),
            "exp": now + timedelta(minutes=MCP_ACCESS_TTL_MINUTES),
        }
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def decode_mcp_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.mcp_resource_url.rstrip("/"),
                issuer=settings.oauth_issuer,
                options={"require_exp": True, "require_sub": True, "require_aud": True},
            )
        except JWTError as exc:
            # Audience may be stored with/without trailing slash — retry stripped.
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={
                        "require_exp": True,
                        "require_sub": True,
                        "verify_aud": False,
                    },
                )
                aud = payload.get("aud")
                expected = settings.mcp_resource_url.rstrip("/")
                if isinstance(aud, str):
                    ok = aud.rstrip("/") == expected
                elif isinstance(aud, list):
                    ok = any(str(a).rstrip("/") == expected for a in aud)
                else:
                    ok = False
                if not ok or payload.get("iss") != settings.oauth_issuer:
                    raise OAuthError(
                        oauth_error="invalid_token",
                        description="Invalid MCP access token",
                        status_code=401,
                    ) from exc
            except JWTError as inner:
                raise OAuthError(
                    oauth_error="invalid_token",
                    description="Invalid MCP access token",
                    status_code=401,
                ) from inner

        if payload.get("type") != MCP_ACCESS_TOKEN_TYPE:
            raise OAuthError(
                oauth_error="invalid_token",
                description="Not an MCP access token",
                status_code=401,
            )
        scope = str(payload.get("scope") or "")
        if MCP_SCOPE not in scope.split():
            raise OAuthError(
                oauth_error="insufficient_scope",
                description=f"Missing scope {MCP_SCOPE}",
                status_code=403,
            )
        return payload

    @staticmethod
    def _assert_redirect_uri_shape(uri: str) -> None:
        parsed = urlparse(uri)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise OAuthError(
                oauth_error="invalid_redirect_uri",
                description="redirect_uri must be an absolute http(s) URL",
            )
        if parsed.scheme == "http" and parsed.hostname not in {
            "localhost",
            "127.0.0.1",
        }:
            raise OAuthError(
                oauth_error="invalid_redirect_uri",
                description="http redirect_uri is only allowed on localhost",
            )
