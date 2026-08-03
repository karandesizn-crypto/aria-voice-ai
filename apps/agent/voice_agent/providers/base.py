from __future__ import annotations

from typing import Protocol


class RealtimeModelProvider(Protocol):
    """Abstraction over speech-to-speech realtime model backends."""

    def create(self):  # noqa: ANN201
        """Return a LiveKit-compatible realtime model instance."""
        ...
