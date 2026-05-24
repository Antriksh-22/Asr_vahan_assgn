from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AudioSample:
    audio_file: str
    transcript: str
    locality: str
    condition: str
    language: str
    style: str
    difficulty: str = "unknown"


@dataclass
class TranscriptionResult:
    model_name: str
    audio_file: str
    transcript: str
    latency_ms: float | None = None
    audio_duration_s: float | None = None
    confidence: float | None = None
    raw_response: dict[str, Any] | None = None
    error: str | None = None

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["raw_response"] = "" if self.raw_response is None else str(self.raw_response)[:1000]
        return row


@dataclass
class MetricResult:
    model_name: str
    audio_file: str
    reference: str
    hypothesis: str
    locality: str
    wer: float
    cer: float
    locality_correct: bool
    fuzzy_locality_match: bool
    partial_locality_match: bool
    predicted_locality: str | None
    locality_match_confidence: float | None
    locality_match_text: str | None
    locality_correct_after_correction: bool
    needs_review: bool
    latency_ms: float | None
    audio_duration_s: float | None
    rtf: float | None
    condition: str
    language: str
    style: str
    difficulty: str
    error: str | None = None

    def to_row(self) -> dict[str, Any]:
        return asdict(self)
