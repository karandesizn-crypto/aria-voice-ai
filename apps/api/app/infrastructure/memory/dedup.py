from __future__ import annotations

import hashlib
import re


def normalize_memory_text(content: str) -> str:
    collapsed = re.sub(r"\s+", " ", content.strip().lower())
    return collapsed


def content_hash(content: str) -> str:
    return hashlib.sha256(normalize_memory_text(content).encode("utf-8")).hexdigest()
