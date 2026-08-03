from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ClerkUser:
    user_id: str
    session_id: str | None
    claims: dict[str, Any]
