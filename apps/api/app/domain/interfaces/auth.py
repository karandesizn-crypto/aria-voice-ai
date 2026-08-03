from __future__ import annotations

from typing import Any, Protocol


class AuthUser(Protocol):
    """Authenticated principal extracted from a verified Clerk JWT."""

    @property
    def user_id(self) -> str: ...

    @property
    def session_id(self) -> str | None: ...

    @property
    def claims(self) -> dict[str, Any]: ...


class AuthProvider(Protocol):
    """Verifies bearer tokens and returns an authenticated user."""

    async def verify_token(self, token: str) -> AuthUser: ...
