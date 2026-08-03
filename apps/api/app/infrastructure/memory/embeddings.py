from __future__ import annotations

import hashlib
from typing import Any

import httpx


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._http = http_client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._http.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "input": texts,
                "dimensions": self._dimensions,
            },
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        data = sorted(payload["data"], key=lambda row: row["index"])
        return [row["embedding"] for row in data]


class HashEmbeddingProvider:
    """Deterministic local embeddings for tests / offline fallback."""

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vals = [
                ((digest[i % len(digest)] / 255.0) * 2.0 - 1.0)
                for i in range(self._dimensions)
            ]
            norm = sum(v * v for v in vals) ** 0.5 or 1.0
            vectors.append([v / norm for v in vals])
        return vectors
