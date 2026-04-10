import time
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

from bookstore.config.security import decode_token, get_current_user

_RSA_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_RSA_PUBLIC_KEY = _RSA_PRIVATE_KEY.public_key()


def _create_test_token(payload: dict | None = None) -> str:
    default_payload = {
        "sub": "test-user",
        "aud": "bookstore-api",
        "iss": "test-issuer",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    if payload:
        default_payload.update(payload)
    return jwt.encode(default_payload, _RSA_PRIVATE_KEY, algorithm="RS256")


def _create_expired_token() -> str:
    payload = {
        "sub": "test-user",
        "aud": "bookstore-api",
        "exp": int(time.time()) - 3600,
        "iat": int(time.time()) - 7200,
    }
    return jwt.encode(payload, _RSA_PRIVATE_KEY, algorithm="RS256")


@pytest.mark.security
class TestJwtSecurity:
    async def test_missing_token_returns_401(self):
        async def require_auth_endpoint():
            pass

        from fastapi import Depends, FastAPI

        test_app = FastAPI()

        @test_app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user": user}

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/protected")
            assert response.status_code == 401

    @patch("bookstore.config.security.get_jwk_client")
    async def test_invalid_token_returns_401(self, mock_jwk_client):
        mock_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = _RSA_PUBLIC_KEY
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwk_client.return_value = mock_client

        from fastapi import Depends, FastAPI

        test_app = FastAPI()

        @test_app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user": user}

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/protected",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
            assert response.status_code == 401

    @patch("bookstore.config.security.get_jwk_client")
    async def test_expired_token_returns_401(self, mock_jwk_client):
        mock_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = _RSA_PUBLIC_KEY
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwk_client.return_value = mock_client

        from fastapi import Depends, FastAPI

        test_app = FastAPI()

        @test_app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user": user}

        token = _create_expired_token()
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 401

    @patch("bookstore.config.security.get_jwk_client")
    @patch("bookstore.config.security.get_settings")
    async def test_valid_token_returns_payload(
        self, mock_get_settings, mock_jwk_client
    ):
        mock_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = _RSA_PUBLIC_KEY
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwk_client.return_value = mock_client

        mock_settings = MagicMock()
        mock_settings.oauth2_audience = "bookstore-api"
        mock_settings.oauth2_issuer_uri = "test-issuer"
        mock_get_settings.return_value = mock_settings

        token = _create_test_token()
        payload = decode_token(token)

        assert payload["sub"] == "test-user"
        assert payload["aud"] == "bookstore-api"

    def test_decode_token_without_jwk_uri_raises(self):
        with patch("bookstore.config.security.get_jwk_client", return_value=None):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                decode_token("some-token")
            assert exc_info.value.status_code == 503
