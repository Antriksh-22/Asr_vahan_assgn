from __future__ import annotations

import os
import time
from pathlib import Path

from ..audio_loader import duration_seconds
from ..schema import TranscriptionResult
from .base import BaseASRAdapter


class IndicAdapter(BaseASRAdapter):
    name = "indic"

    def __init__(self) -> None:
        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise ImportError("Install transformers and torch to use IndicAdapter.") from exc

        model_id = os.getenv("INDIC_MODEL_ID", "ai4bharat/indicwav2vec_v2_hi")
        requested_device = os.getenv("INDIC_DEVICE", "auto")
        if requested_device == "auto":
            device = 0 if torch.cuda.is_available() else -1
        else:
            device = int(requested_device)

        self.model_id = model_id
        self.pipeline = pipeline("automatic-speech-recognition", model=model_id, device=device)

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        started_at = time.perf_counter()
        try:
            payload = self.pipeline(str(audio_path))
            if isinstance(payload, dict):
                transcript = payload.get("text", "")
            else:
                transcript = str(payload)
            return TranscriptionResult(
                model_name=f"{self.name}:{self.model_id}",
                audio_file=audio_path.name,
                transcript=transcript.strip(),
                latency_ms=(time.perf_counter() - started_at) * 1000,
                audio_duration_s=duration_seconds(audio_path),
                raw_response=payload if isinstance(payload, dict) else {"text": transcript},
            )
        except Exception as exc:
            return self._timed_empty_result(audio_path, started_at, error=str(exc))

