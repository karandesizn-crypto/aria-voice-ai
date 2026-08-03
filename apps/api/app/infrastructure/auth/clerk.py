from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.backends.base import Key
from jose.exceptions import JWKError
from jose.jwk import construct

from app.domain.models import ClerkUser


class ClerkAuthProvider:
    """Validates Clerk session JWTs using the tenant JWKS endpoint."""

    def __init__(
        self,
        *,
        jwks_url: str,
        issuer: str,
        audience: str | None = None,
        http_client: Any,
    ) -> None:
        self._jwks_url = jwks_url
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._http = http_client
        self._keys: dict[str, Key] = {}

    async def verify_token(self, token: str) -> ClerkUser:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key id",
                )

            key = await self._get_key(kid)
            decode_kwargs: dict[str, Any] = {
                "algorithms": ["RS256"],
                "issuer": self._issuer,
                "options": {"verify_aud": bool(self._audience)},
            }
            if self._audience:
                decode_kwargs["audience"] = self._audience

            claims = jwt.decode(token, key, **decode_kwargs)
        except (JWTError, JWKError, HTTPException) as exc:
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            ) from exc

        user_id = claims.get("sub")
        if not user_id or not isinstance(user_id, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )

        session_id = claims.get("sid")
        return ClerkUser(
            user_id=user_id,
            session_id=session_id if isinstance(session_id, str) else None,
            claims=claims,
        )

    async def _get_key(self, kid: str) -> Key:
        if kid in self._keys:
            return self._keys[kid]

        response = await self._http.get(self._jwks_url)
        response.raise_for_status()
        payload = response.json()
        for jwk in payload.get("keys", []):
            if jwk.get("kid") == kid:
                key = construct(jwk)
                self._keys[kid] = key
                return key

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find matching signing key",
        )
