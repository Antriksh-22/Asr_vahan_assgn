from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path

from ..audio_loader import duration_seconds
from ..schema import TranscriptionResult


class BaseASRAdapter(ABC):
    name: str

    @abstractmethod
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        raise NotImplementedError

    def batch_transcribe(self, audio_paths: list[Path]) -> list[TranscriptionResult]:
        return [self.transcribe(path) for path in audio_paths]

    def _timed_empty_result(self, audio_path: Path, started_at: float, error: str) -> TranscriptionResult:
        return TranscriptionResult(
            model_name=self.name,
            audio_file=audio_path.name,
            transcript="",
            latency_ms=(time.perf_counter() - started_at) * 1000,
            audio_duration_s=duration_seconds(audio_path),
            error=error,
        )

