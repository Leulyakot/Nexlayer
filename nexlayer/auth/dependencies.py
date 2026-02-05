"""FastAPI authentication dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError

from nexlayer.auth.jwt_handler import decode_access_token
from nexlayer.config.settings import get_settings

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticatedUser:
    """Represents a verified caller."""

    def __init__(self, user_id: str, role: str = "viewer"):
        self.user_id = user_id
        self.role = role


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)] = None,
    api_key: Annotated[str | None, Security(api_key_header)] = None,
) -> AuthenticatedUser:
    """Resolve the current user from JWT bearer token or API key.

    Raises 401 if neither method succeeds.
    """
    # Try JWT first
    if credentials is not None:
        try:
            payload = decode_access_token(credentials.credentials)
            user_id: str | None = payload.get("sub")
            role: str = payload.get("role", "viewer")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject",
                )
            return AuthenticatedUser(user_id=user_id, role=role)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            )

    # Fallback to API key
    if api_key is not None:
        settings = get_settings()
        if api_key in settings.valid_api_keys:
            # API key users get analyst role by default
            return AuthenticatedUser(user_id=f"apikey:{api_key[:8]}...", role="analyst")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a Bearer token or X-API-Key header.",
    )
