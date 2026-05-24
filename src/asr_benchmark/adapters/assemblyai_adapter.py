from __future__ import annotations

import os
import time
from pathlib import Path

import requests

from ..audio_loader import duration_seconds
from ..env import required_env
from ..schema import TranscriptionResult
from .base import BaseASRAdapter


class AssemblyAIAdapter(BaseASRAdapter):
    name = "assemblyai"

    def __init__(self) -> None:
        self.api_key = required_env("ASSEMBLYAI_API_KEY")
        self.timeout_s = float(os.getenv("ASSEMBLYAI_TIMEOUT_S", "45"))
        self.poll_interval_s = float(os.getenv("ASSEMBLYAI_POLL_INTERVAL_S", "3"))
        self.max_poll_s = float(os.getenv("ASSEMBLYAI_MAX_POLL_S", "180"))
        self.base_url = "https://api.assemblyai.com/v2"

    @property
    def _headers(self) -> dict[str, str]:
        return {"authorization": self.api_key}

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        started_at = time.perf_counter()
        try:
            upload_url = self._upload(audio_path)
            transcript_id = self._create_transcript(upload_url)
            payload = self._poll_transcript(transcript_id)
            return TranscriptionResult(
                model_name=self.name,
                audio_file=audio_path.name,
                transcript=payload.get("text") or "",
                latency_ms=(time.perf_counter() - started_at) * 1000,
                audio_duration_s=duration_seconds(audio_path),
                confidence=payload.get("confidence"),
                raw_response=payload,
                error=payload.get("error"),
            )
        except Exception as exc:
            return self._timed_empty_result(audio_path, started_at, error=str(exc))

    def _upload(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio_file:
            response = requests.post(
                f"{self.base_url}/upload",
                headers=self._headers,
                data=audio_file,
                timeout=self.timeout_s,
            )
        response.raise_for_status()
        return response.json()["upload_url"]

    def _create_transcript(self, upload_url: str) -> str:
        response = requests.post(
            f"{self.base_url}/transcript",
            headers={**self._headers, "content-type": "application/json"},
            json={
                "audio_url": upload_url,
                "language_code": os.getenv("ASSEMBLYAI_LANGUAGE_CODE", "hi"),
                "speech_models": [os.getenv("ASSEMBLYAI_SPEECH_MODEL", "universal-2")],
            },
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        return response.json()["id"]

    def _poll_transcript(self, transcript_id: str) -> dict:
        deadline = time.perf_counter() + self.max_poll_s
        while time.perf_counter() < deadline:
            response = requests.get(
                f"{self.base_url}/transcript/{transcript_id}",
                headers=self._headers,
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") in {"completed", "error"}:
                return payload
            time.sleep(self.poll_interval_s)
        raise TimeoutError(f"AssemblyAI transcript {transcript_id} did not finish in {self.max_poll_s}s")
