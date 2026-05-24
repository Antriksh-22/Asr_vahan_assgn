from __future__ import annotations

import re
from difflib import SequenceMatcher

from .schema import AudioSample, MetricResult, TranscriptionResult


_PUNCT_RE = re.compile(r"[^a-z0-9 ]+")

_DEVANAGARI_VOWELS = {
    "अ": "a",
    "आ": "aa",
    "इ": "i",
    "ई": "ee",
    "उ": "u",
    "ऊ": "oo",
    "ए": "e",
    "ऐ": "ai",
    "ओ": "o",
    "औ": "au",
}
_DEVANAGARI_MATRAS = {
    "ा": "aa",
    "ि": "i",
    "ी": "ee",
    "ु": "u",
    "ू": "oo",
    "े": "e",
    "ै": "ai",
    "ो": "o",
    "ौ": "au",
    "ृ": "ri",
}
_DEVANAGARI_CONSONANTS = {
    "क": "k",
    "ख": "kh",
    "ग": "g",
    "घ": "gh",
    "च": "ch",
    "छ": "chh",
    "ज": "j",
    "झ": "jh",
    "ट": "t",
    "ठ": "th",
    "ड": "d",
    "ढ": "dh",
    "ण": "n",
    "त": "t",
    "थ": "th",
    "द": "d",
    "ध": "dh",
    "न": "n",
    "प": "p",
    "फ": "ph",
    "ब": "b",
    "भ": "bh",
    "म": "m",
    "य": "y",
    "र": "r",
    "ल": "l",
    "व": "v",
    "श": "sh",
    "ष": "sh",
    "स": "s",
    "ह": "h",
    "ळ": "l",
}
_DEVANAGARI_SIGNS = {"ं": "n", "ँ": "n", "ः": "h", "़": "", "्": ""}


def normalize_text(text: str) -> str:
    text = transliterate_devanagari(text).lower()
    text = text.replace("&", " and ")
    text = _PUNCT_RE.sub(" ", text)
    return " ".join(text.split())


def transliterate_devanagari(text: str) -> str:
    """Convert Devanagari ASR output into rough Latin text for fair comparison.

    This is intentionally simple and deterministic. It is not meant to be a
    perfect Hindi transliterator; it keeps locality matching from failing only
    because one API emits native script and the labels are Romanized.
    """
    out: list[str] = []
    i = 0
    while i < len(text):
        char = text[i]
        if char in _DEVANAGARI_CONSONANTS:
            base = _DEVANAGARI_CONSONANTS[char]
            next_char = text[i + 1] if i + 1 < len(text) else ""
            if next_char in _DEVANAGARI_MATRAS:
                out.append(base + _DEVANAGARI_MATRAS[next_char])
                i += 2
                continue
            if next_char == "्":
                out.append(base)
                i += 2
                continue
            out.append(base + "a")
        elif char in _DEVANAGARI_VOWELS:
            out.append(_DEVANAGARI_VOWELS[char])
        elif char in _DEVANAGARI_MATRAS:
            out.append(_DEVANAGARI_MATRAS[char])
        elif char in _DEVANAGARI_SIGNS:
            out.append(_DEVANAGARI_SIGNS[char])
        else:
            out.append(char)
        i += 1
    return "".join(out)


def edit_distance(left: list[str] | str, right: list[str] | str) -> int:
    rows = len(left) + 1
    cols = len(right) + 1
    dp = [[0] * cols for _ in range(rows)]

    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            substitution_cost = 0 if left[i - 1] == right[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + substitution_cost,
            )
    return dp[-1][-1]


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(hypothesis).split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    return edit_distance(ref_words, hyp_words) / len(ref_words)


def char_error_rate(reference: str, hypothesis: str) -> float:
    ref = normalize_text(reference).replace(" ", "")
    hyp = normalize_text(hypothesis).replace(" ", "")
    if not ref:
        return 0.0 if not hyp else 1.0
    return edit_distance(ref, hyp) / len(ref)


def locality_correct(hypothesis: str, locality: str) -> bool:
    normalized_loc = normalize_text(locality)
    normalized_hyp = normalize_text(hypothesis)
    if normalized_loc in normalized_hyp:
        return True
    return compact_key(normalized_loc) in compact_key(normalized_hyp)


def compact_key(text: str) -> str:
    normalized = normalize_text(text)
    return re.sub(r"[aeiou ]+", "", normalized)


def partial_locality_match(hypothesis: str, locality: str) -> bool:
    locality_words = normalize_text(locality).split()
    if len(locality_words) <= 1:
        return False
    hyp_words = set(normalize_text(hypothesis).split())
    return any(word in hyp_words for word in locality_words)


def fuzzy_locality_match(hypothesis: str, locality: str, threshold: float = 0.82) -> bool:
    normalized_loc = normalize_text(locality)
    normalized_hyp = normalize_text(hypothesis)
    if not normalized_loc or not normalized_hyp:
        return False
    if normalized_loc in normalized_hyp:
        return True

    loc_words = normalized_loc.split()
    hyp_words = normalized_hyp.split()
    window_size = max(1, len(loc_words))
    candidates = [" ".join(hyp_words[i : i + window_size]) for i in range(len(hyp_words))]
    candidates.extend(hyp_words)
    return any(SequenceMatcher(None, normalized_loc, candidate).ratio() >= threshold for candidate in candidates)


def evaluate(result: TranscriptionResult, sample: AudioSample, locality_match=None) -> MetricResult:
    hypothesis = result.transcript or ""
    rtf = None
    if result.latency_ms is not None and result.audio_duration_s:
        rtf = (result.latency_ms / 1000.0) / result.audio_duration_s

    corrected_locality = locality_match.predicted_locality if locality_match else None
    correction_confidence = locality_match.confidence if locality_match else None
    correction_text = locality_match.matched_text if locality_match else None
    corrected = corrected_locality == sample.locality if locality_match else False
    needs_review = locality_match.needs_review if locality_match else True

    return MetricResult(
        model_name=result.model_name,
        audio_file=result.audio_file,
        reference=sample.transcript,
        hypothesis=hypothesis,
        locality=sample.locality,
        wer=word_error_rate(sample.transcript, hypothesis) if not result.error else 1.0,
        cer=char_error_rate(sample.transcript, hypothesis) if not result.error else 1.0,
        locality_correct=locality_correct(hypothesis, sample.locality) if not result.error else False,
        fuzzy_locality_match=fuzzy_locality_match(hypothesis, sample.locality) if not result.error else False,
        partial_locality_match=partial_locality_match(hypothesis, sample.locality) if not result.error else False,
        predicted_locality=corrected_locality,
        locality_match_confidence=correction_confidence,
        locality_match_text=correction_text,
        locality_correct_after_correction=corrected,
        needs_review=needs_review,
        latency_ms=result.latency_ms,
        audio_duration_s=result.audio_duration_s,
        rtf=rtf,
        condition=sample.condition,
        language=sample.language,
        style=sample.style,
        difficulty=sample.difficulty,
        error=result.error,
    )
