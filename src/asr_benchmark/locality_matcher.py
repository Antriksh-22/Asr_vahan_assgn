from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .metrics import compact_key, normalize_text


@dataclass(frozen=True)
class LocalityMatch:
    predicted_locality: str
    confidence: float
    matched_text: str
    needs_review: bool


class LocalityMatcher:
    """Dictionary-based locality correction for ASR transcripts.

    This layer does not change the ASR transcript. It predicts the most likely
    Bangalore locality from a known locality list and exposes a confidence score
    so uncertain cases can go to human review or a second-pass model.
    """

    def __init__(self, localities: list[str], review_threshold: float = 0.80) -> None:
        self.localities = sorted(set(localities))
        self.review_threshold = review_threshold

    def match(self, transcript: str) -> LocalityMatch:
        best_locality = ""
        best_score = 0.0
        best_candidate = ""

        for locality in self.localities:
            score, candidate = self._score_locality(transcript, locality)
            if score > best_score:
                best_locality = locality
                best_score = score
                best_candidate = candidate

        return LocalityMatch(
            predicted_locality=best_locality,
            confidence=round(best_score, 4),
            matched_text=best_candidate,
            needs_review=best_score < self.review_threshold,
        )

    def _score_locality(self, transcript: str, locality: str) -> tuple[float, str]:
        normalized_transcript = normalize_text(transcript)
        normalized_locality = normalize_text(locality)
        if not normalized_transcript or not normalized_locality:
            return 0.0, ""

        if normalized_locality in normalized_transcript:
            return 1.0, normalized_locality

        locality_words = normalized_locality.split()
        transcript_words = normalized_transcript.split()
        windows = self._candidate_windows(transcript_words, target_size=len(locality_words))
        compact_locality = compact_key(normalized_locality)

        best_score = 0.0
        best_candidate = ""
        for candidate in windows:
            compact_candidate = compact_key(candidate)
            sequence_score = SequenceMatcher(None, normalized_locality, candidate).ratio()
            compact_score = SequenceMatcher(None, compact_locality, compact_candidate).ratio()
            score = max(sequence_score, compact_score)

            if compact_locality and compact_locality in compact_candidate:
                score = max(score, 0.95)
            elif compact_candidate and compact_candidate in compact_locality and len(compact_candidate) >= 5:
                score = max(score, 0.78)

            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_score, best_candidate

    @staticmethod
    def _candidate_windows(words: list[str], target_size: int) -> list[str]:
        candidates: list[str] = []
        for size in range(max(1, target_size - 1), target_size + 3):
            if size > len(words):
                continue
            for start in range(0, len(words) - size + 1):
                candidates.append(" ".join(words[start : start + size]))
        candidates.extend(words)
        return candidates
