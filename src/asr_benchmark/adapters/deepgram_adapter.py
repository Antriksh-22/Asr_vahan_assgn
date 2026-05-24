from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

from ..audio_loader import duration_seconds
from ..env import required_env
from ..schema import TranscriptionResult
from .base import BaseASRAdapter


class DeepgramAdapter(BaseASRAdapter):
    name = "deepgram"

    def __init__(self) -> None:
        self.api_key = required_env("DEEPGRAM_API_KEY")
        self.model = os.getenv("DEEPGRAM_MODEL", "nova-2")
        self.language = os.getenv("DEEPGRAM_LANGUAGE", "hi")
        self.timeout_s = float(os.getenv("DEEPGRAM_TIMEOUT_S", "45"))

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        started_at = time.perf_counter()
        params = {
            "model": self.model,
            "language": self.language,
            "punctuate": "true",
            "smart_format": "false",
        }
        url = f"https://api.deepgram.com/v1/listen?{urlencode(params)}"
        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            with audio_path.open("rb") as audio_file:
                response = requests.post(url, headers=headers, data=audio_file, timeout=self.timeout_s)
            response.raise_for_status()
            payload = response.json()
            alt = payload["results"]["channels"][0]["alternatives"][0]
            transcript = alt.get("transcript", "")
            confidence = alt.get("confidence")
            return TranscriptionResult(
                model_name=self.name,
                audio_file=audio_path.name,
                transcript=transcript,
                latency_ms=(time.perf_counter() - started_at) * 1000,
                audio_duration_s=duration_seconds(audio_path),
                confidence=confidence,
                raw_response=payload,
            )
        except Exception as exc:
            return self._timed_empty_result(audio_path, started_at, error=str(exc))

