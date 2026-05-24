from __future__ import annotations

import os
import time
from pathlib import Path

from ..audio_loader import duration_seconds
from ..schema import TranscriptionResult
from .base import BaseASRAdapter


LOCALITY_PROMPT = (
    "Bangalore locality names: Koramangala, Indiranagar, Whitefield, Electronic City, "
    "Marathahalli, Jayanagar, Rajajinagar, Hebbal, Yelahanka, Banashankari, HSR Layout, "
    "BTM Layout, Majestic, Silk Board, Bellandur, Sarjapur, Bommanahalli, KR Puram, "
    "Peenya, Yeshwanthpur, Byatarayanapura, Kadugondanahalli, Hesaraghatta, "
    "Chikkabanavara, Rajarajeshwarinagar, Kothanur Dinne, Thanisandra, Doddanekundi, "
    "Kengeri Upanagara, Thalaghattapura."
)


class WhisperAdapter(BaseASRAdapter):
    name = "whisper"

    def __init__(self) -> None:
        try:
            import torch
            import whisper
        except ImportError as exc:
            raise ImportError("Install openai-whisper and torch to use WhisperAdapter.") from exc

        model_size = os.getenv("WHISPER_MODEL", "medium")
        requested_device = os.getenv("WHISPER_DEVICE", "auto")
        if requested_device == "auto":
            requested_device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = requested_device
        self.model_size = model_size
        self.model = whisper.load_model(model_size, device=self.device)

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        started_at = time.perf_counter()
        try:
            payload = self.model.transcribe(
                str(audio_path),
                language=os.getenv("WHISPER_LANGUAGE", "hi"),
                initial_prompt=LOCALITY_PROMPT,
                fp16=self.device == "cuda",
            )
            return TranscriptionResult(
                model_name=f"{self.name}-{self.model_size}",
                audio_file=audio_path.name,
                transcript=payload.get("text", "").strip(),
                latency_ms=(time.perf_counter() - started_at) * 1000,
                audio_duration_s=duration_seconds(audio_path),
                raw_response={"language": payload.get("language"), "segments": payload.get("segments", [])[:3]},
            )
        except Exception as exc:
            return self._timed_empty_result(audio_path, started_at, error=str(exc))

