from __future__ import annotations

import os
import time
from pathlib import Path

import requests

from ..audio_loader import duration_seconds
from ..env import required_env
from ..schema import TranscriptionResult
from .base import BaseASRAdapter


class HuggingFaceWhisperAdapter(BaseASRAdapter):
    name = "hf-whisper"

    def __init__(self) -> None:
        self.token = required_env("HF_TOKEN")
        self.model_id = os.getenv("HF_ASR_MODEL_ID", "openai/whisper-large-v3")
        self.timeout_s = float(os.getenv("HF_ASR_TIMEOUT_S", "120"))
        self.endpoint = os.getenv(
            "HF_ASR_ENDPOINT",
            f"https://api-inference.huggingface.co/models/{self.model_id}",
        )

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        started_at = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "audio/wav",
        }
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=audio_path.read_bytes(),
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            payload = response.json()
            transcript = payload.get("text", "") if isinstance(payload, dict) else str(payload)
            return TranscriptionResult(
                model_name=f"{self.name}:{self.model_id}",
                audio_file=audio_path.name,
                transcript=transcript.strip(),
                latency_ms=(time.perf_counter() - started_at) * 1000,
                audio_duration_s=duration_seconds(audio_path),
                raw_response=payload if isinstance(payload, dict) else {"response": payload},
            )
        except Exception as exc:
            return self._timed_empty_result(audio_path, started_at, error=str(exc))

