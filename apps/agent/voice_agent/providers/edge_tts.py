from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace

import edge_tts
from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APITimeoutError,
    tts,
    utils,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS

# Edge neural voices typically synthesize at 24 kHz mono MP3.
SAMPLE_RATE = 24000
NUM_CHANNELS = 1
DEFAULT_VOICE = "en-US-JennyNeural"


@dataclass
class _TTSOptions:
    voice: str


class EdgeTTS(tts.TTS):
    """Microsoft Edge online TTS — free, no API key, good local-dev fallback."""

    def __init__(self, *, voice: str = DEFAULT_VOICE) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        self._opts = _TTSOptions(voice=voice)

    @property
    def model(self) -> str:
        return "edge-tts"

    @property
    def provider(self) -> str:
        return "edge"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return _EdgeChunkedStream(tts=self, input_text=text, conn_options=conn_options)


class _EdgeChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: EdgeTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts = tts
        self._opts = replace(tts._opts)

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        try:
            communicate = edge_tts.Communicate(self._input_text, self._opts.voice)
            output_emitter.initialize(
                request_id=utils.shortuuid(),
                sample_rate=SAMPLE_RATE,
                num_channels=NUM_CHANNELS,
                mime_type="audio/mp3",
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    output_emitter.push(chunk["data"])
            output_emitter.flush()
        except asyncio.TimeoutError:
            raise APITimeoutError() from None
        except Exception as exc:  # noqa: BLE001
            raise APIConnectionError() from exc
