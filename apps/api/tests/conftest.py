from __future__ import annotations

import os

# Must be set before app.main is imported by tests (module-level create_app).
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "CLERK_JWKS_URL",
    "https://example.clerk.accounts.dev/.well-known/jwks.json",
)
os.environ.setdefault("CLERK_ISSUER", "https://example.clerk.accounts.dev")
os.environ.setdefault("LIVEKIT_URL", "wss://example.livekit.cloud")
os.environ.setdefault("LIVEKIT_API_KEY", "APItestkey")
os.environ.setdefault(
    "LIVEKIT_API_SECRET",
    "testsecret_testsecret_testsecret12",
)
os.environ.setdefault("API_CORS_ORIGINS", "http://localhost:3000")

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def rsa_keypair() -> tuple[str, dict]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_numbers = private_key.public_key().public_numbers()

    def _b64url_uint(val: int) -> str:
        import base64

        length = (val.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(val.to_bytes(length, "big")).rstrip(b"=").decode()

    jwk = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "alg": "RS256",
        "n": _b64url_uint(public_numbers.n),
        "e": _b64url_uint(public_numbers.e),
    }
    return private_pem, jwk


@pytest.fixture
def make_clerk_token(rsa_keypair: tuple[str, dict]):
    private_pem, _jwk = rsa_keypair

    def _factory(
        *,
        sub: str = "user_123",
        issuer: str = "https://example.clerk.accounts.dev",
        kid: str = "test-key",
    ) -> str:
        return jwt.encode(
            {"sub": sub, "sid": "sess_123", "iss": issuer},
            private_pem,
            algorithm="RS256",
            headers={"kid": kid},
        )

    return _factory


@pytest.fixture
def jwks_payload(rsa_keypair: tuple[str, dict]) -> dict:
    _private_pem, jwk = rsa_keypair
    return {"keys": [jwk]}
