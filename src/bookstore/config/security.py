from functools import lru_cache
from typing import Any

import jwt
import structlog
import structlog.contextvars
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from bookstore.config.settings import get_settings

logger = structlog.get_logger()

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_jwk_client() -> PyJWKClient | None:
    settings = get_settings()
    if settings.oauth2_jwk_uri:
        return PyJWKClient(settings.oauth2_jwk_uri, cache_keys=True)
    return None


def decode_token(token: str) -> dict[str, Any]:
    jwk_client = get_jwk_client()
    if jwk_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth2 JWK URI not configured",
        )

    settings = get_settings()
    signing_key = jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.oauth2_audience,
        issuer=settings.oauth2_issuer_uri or None,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        # Bind validated user identity to structlog context (overwrites middleware peek)
        structlog.contextvars.bind_contextvars(user_id=payload.get("sub", "anonymous"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning("invalid_jwt_token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
