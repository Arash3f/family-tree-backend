"""OAuth 2.1 endpoints for ChatGPT MCP connectors (+ panel consent)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.application.services.mcp_oauth_service import McpOAuthService
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.mcp_exceptions import McpDisabledException
from app.domain.exceptions.oauth_exceptions import OAuthError
from app.presentation.dependencies import get_request_uow, get_token_service
from app.presentation.rest.dependencies.auth_dependencies import get_current_user

router = APIRouter(tags=["OAuth"], include_in_schema=False)


def _oauth(uow=Depends(get_request_uow), token_service=Depends(get_token_service)):
    return McpOAuthService(uow.session, token_service)


@router.get("/.well-known/oauth-protected-resource")
@router.get("/.well-known/oauth-protected-resource/mcp")
async def protected_resource_metadata(
    oauth: McpOAuthService = Depends(_oauth),
) -> dict[str, Any]:
    if not settings.MCP_ENABLED:
        raise McpDisabledException()
    return oauth.resource_metadata()


@router.get("/.well-known/oauth-authorization-server")
async def authorization_server_metadata(
    oauth: McpOAuthService = Depends(_oauth),
) -> dict[str, Any]:
    if not settings.MCP_ENABLED:
        raise McpDisabledException()
    return oauth.authorization_server_metadata()


@router.post("/oauth/register")
async def register_client(
    body: dict[str, Any],
    oauth: McpOAuthService = Depends(_oauth),
    uow=Depends(get_request_uow),
) -> JSONResponse:
    if not settings.MCP_ENABLED:
        raise McpDisabledException()
    redirect_uris = body.get("redirect_uris") or []
    if not isinstance(redirect_uris, list):
        raise OAuthError(
            oauth_error="invalid_client_metadata",
            description="redirect_uris must be an array",
        )
    payload = await oauth.register_client(
        redirect_uris=[str(u) for u in redirect_uris],
        client_name=body.get("client_name"),
        token_endpoint_auth_method=str(
            body.get("token_endpoint_auth_method") or "none"
        ),
    )
    await uow.commit()
    return JSONResponse(payload, status_code=201)


@router.get("/oauth/authorize")
async def authorize(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query("S256"),
    resource: str | None = Query(None),
    scope: str | None = Query(None),
    state: str | None = Query(None),
    oauth: McpOAuthService = Depends(_oauth),
    uow=Depends(get_request_uow),
) -> RedirectResponse:
    consent_url = await oauth.start_authorization(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        resource=resource,
        scope=scope,
        state=state,
        response_type=response_type,
    )
    await uow.commit()
    return RedirectResponse(url=consent_url, status_code=302)


class ConsentDecisionRequest(BaseModel):
    approve: bool = True


class ConsentRequestResponse(BaseModel):
    id: UUID
    client_id: str
    client_name: str
    redirect_uri: str
    resource: str
    scope: str
    expires_at: str


class ConsentRedirectResponse(BaseModel):
    redirect_to: str


@router.get("/oauth/consent-requests/{request_id}", response_model=ConsentRequestResponse)
async def read_consent_request(
    request_id: UUID,
    _user: User = Depends(get_current_user),
    oauth: McpOAuthService = Depends(_oauth),
) -> ConsentRequestResponse:
    view = await oauth.get_consent_request(request_id)
    return ConsentRequestResponse(
        id=view.id,
        client_id=view.client_id,
        client_name=view.client_name,
        redirect_uri=view.redirect_uri,
        resource=view.resource,
        scope=view.scope,
        expires_at=view.expires_at.isoformat(),
    )


@router.post(
    "/oauth/consent-requests/{request_id}",
    response_model=ConsentRedirectResponse,
)
async def decide_consent(
    request_id: UUID,
    body: ConsentDecisionRequest,
    user: User = Depends(get_current_user),
    oauth: McpOAuthService = Depends(_oauth),
    uow=Depends(get_request_uow),
) -> ConsentRedirectResponse:
    if body.approve:
        redirect_to = await oauth.approve_consent(
            request_id=request_id, user_id=user.safe_id
        )
    else:
        redirect_to = await oauth.deny_consent(request_id=request_id)
    await uow.commit()
    return ConsentRedirectResponse(redirect_to=redirect_to)


@router.post("/oauth/token")
async def token(
    request: Request,
    grant_type: str = Form(...),
    oauth: McpOAuthService = Depends(_oauth),
    uow=Depends(get_request_uow),
) -> JSONResponse:
    if not settings.MCP_ENABLED:
        raise McpDisabledException()

    form = await request.form()
    client_id = str(form.get("client_id") or "")
    resource = form.get("resource")
    resource_value = str(resource) if resource is not None else None

    if grant_type == "authorization_code":
        bundle = await oauth.exchange_authorization_code(
            code=str(form.get("code") or ""),
            redirect_uri=str(form.get("redirect_uri") or ""),
            client_id=client_id,
            code_verifier=str(form.get("code_verifier") or ""),
            resource=resource_value,
        )
    elif grant_type == "refresh_token":
        bundle = await oauth.exchange_refresh_token(
            refresh_token=str(form.get("refresh_token") or ""),
            client_id=client_id,
            resource=resource_value,
        )
    else:
        raise OAuthError(
            oauth_error="unsupported_grant_type",
            description="Only authorization_code and refresh_token are supported",
        )

    await uow.commit()
    return JSONResponse(
        {
            "access_token": bundle.access_token,
            "token_type": bundle.token_type,
            "expires_in": bundle.expires_in,
            "refresh_token": bundle.refresh_token,
            "scope": bundle.scope,
        }
    )


@router.post("/oauth/revoke")
async def revoke(
    token: str = Form(...),
    oauth: McpOAuthService = Depends(_oauth),
    uow=Depends(get_request_uow),
) -> JSONResponse:
    await oauth.revoke_refresh_token(token)
    await uow.commit()
    return JSONResponse({"revoked": True})
