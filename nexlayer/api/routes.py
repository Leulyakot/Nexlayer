"""API route definitions for the Nexlayer gateway."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from nexlayer.auth.dependencies import AuthenticatedUser, get_current_user
from nexlayer.auth.rbac import has_model_access, get_max_tokens
from nexlayer.audit.logger import AuditEntry, AuditLogger
from nexlayer.config.policy_loader import PolicyConfig, load_policies
from nexlayer.config.settings import get_settings
from nexlayer.core.schemas import AIRequest, AIResponse, ErrorResponse, HealthResponse, PolicyAction
from nexlayer.detection.detector import build_detection_engine
from nexlayer.policy.engine import PolicyEngine
from nexlayer.providers.router import get_provider
from nexlayer.telemetry.setup import get_tracer

router = APIRouter()
audit_logger = AuditLogger()
tracer = get_tracer()


def _load_policy() -> PolicyConfig:
    settings = get_settings()
    return load_policies(settings.policy_config_path)


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    from nexlayer import __version__

    return HealthResponse(status="ok", version=__version__)


@router.post(
    "/v1/ai/request",
    response_model=AIResponse,
    responses={
        403: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    tags=["ai"],
)
async def ai_request(
    body: AIRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AIResponse:
    """Primary AI gateway endpoint.

    1. Authenticate the caller
    2. Enforce RBAC model access
    3. Run policy & detection engines
    4. Route to the AI provider
    5. Write audit log
    6. Return response
    """
    request_id = uuid.UUID(getattr(request.state, "request_id", str(uuid.uuid4())))
    policy = _load_policy()

    with tracer.start_as_current_span("ai_request") as span:
        span.set_attribute("user.id", user.user_id)
        span.set_attribute("model.provider", body.model.value)

        # --- RBAC check ---
        if not has_model_access(user.role, body.model.value, policy):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' does not have access to model '{body.model.value}'",
            )

        # --- Policy enforcement (before AI invocation) ---
        detection_engine = build_detection_engine(policy)
        policy_engine = PolicyEngine(policy, detection_engine)
        enforcement = policy_engine.evaluate(body.prompt, role=user.role)

        if not enforcement.allowed:
            # Log blocked request
            entry = AuditEntry(
                request_id=request_id,
                user_id=user.user_id,
                model_provider=body.model.value,
                prompt=body.prompt,
                policy_actions=enforcement.actions,
                classification_results=enforcement.classifications,
                response_status="blocked",
                metadata=body.metadata,
            )
            await audit_logger.log(entry)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request blocked by policy",
            )

        # --- Route to AI provider ---
        provider = get_provider(body.model)
        max_tokens = get_max_tokens(user.role, policy)

        try:
            provider_resp = await provider.generate(
                enforcement.modified_prompt,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            entry = AuditEntry(
                request_id=request_id,
                user_id=user.user_id,
                model_provider=body.model.value,
                prompt=body.prompt,
                policy_actions=enforcement.actions,
                classification_results=enforcement.classifications,
                response_status="provider_error",
                metadata=body.metadata,
            )
            await audit_logger.log(entry)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI provider error: {exc}",
            )

        # --- Audit log ---
        entry = AuditEntry(
            request_id=request_id,
            user_id=user.user_id,
            model_provider=body.model.value,
            prompt=body.prompt,
            policy_actions=enforcement.actions,
            classification_results=enforcement.classifications,
            response_status="success",
            metadata=body.metadata,
        )
        await audit_logger.log(entry)

        return AIResponse(
            request_id=request_id,
            model_provider=body.model.value,
            response_text=provider_resp.text,
            policy_actions=enforcement.actions,
            classification_results=enforcement.classifications,
            timestamp=datetime.now(timezone.utc),
        )


@router.post("/v1/auth/token", tags=["auth"])
async def create_token(username: str, role: str = "viewer") -> dict[str, str]:
    """Dev-only endpoint to generate a JWT for testing.

    In production, replace with a proper login flow or SSO integration.
    """
    settings = get_settings()
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404)

    from nexlayer.auth.jwt_handler import create_access_token

    token = create_access_token({"sub": username, "role": role})
    return {"access_token": token, "token_type": "bearer"}
