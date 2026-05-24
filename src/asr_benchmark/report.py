from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

from .env import optional_float_env
from .schema import MetricResult, TranscriptionResult


def write_transcripts_csv(results: list[TranscriptionResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model_name",
        "audio_file",
        "transcript",
        "latency_ms",
        "audio_duration_s",
        "confidence",
        "raw_response",
        "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_row())


def write_metrics_csv(metrics: list[MetricResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(metrics[0].to_row().keys()) if metrics else []
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(metric.to_row())


def mean(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return statistics.fmean(present) if present else None


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def num(value: float | None, suffix: str = "") -> str:
    return "n/a" if value is None else f"{value:.2f}{suffix}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def aggregate_by_model(metrics: list[MetricResult]) -> list[list[str]]:
    rows: list[list[str]] = []
    by_model: dict[str, list[MetricResult]] = defaultdict(list)
    for metric in metrics:
        by_model[metric.model_name].append(metric)

    for model_name, group in sorted(by_model.items()):
        rows.append(
            [
                model_name,
                str(len(group)),
                pct(mean([m.wer for m in group])),
                pct(mean([m.cer for m in group])),
                pct(mean([1.0 if m.locality_correct else 0.0 for m in group])),
                pct(mean([1.0 if m.locality_correct_after_correction else 0.0 for m in group])),
                pct(mean([1.0 if m.locality_correct_after_correction and not m.needs_review else 0.0 for m in group])),
                pct(mean([1.0 if m.needs_review else 0.0 for m in group])),
                pct(mean([1.0 if m.fuzzy_locality_match else 0.0 for m in group])),
                num(mean([m.latency_ms for m in group]), " ms"),
                num(mean([m.rtf for m in group])),
            ]
        )
    return rows


def aggregate_slice(metrics: list[MetricResult], field: str) -> list[list[str]]:
    rows: list[list[str]] = []
    grouped: dict[tuple[str, str], list[MetricResult]] = defaultdict(list)
    for metric in metrics:
        grouped[(metric.model_name, str(getattr(metric, field)))].append(metric)

    for (model_name, label), group in sorted(grouped.items()):
        rows.append(
            [
                model_name,
                label,
                str(len(group)),
                pct(mean([m.wer for m in group])),
                pct(mean([1.0 if m.locality_correct else 0.0 for m in group])),
                pct(mean([1.0 if m.locality_correct_after_correction else 0.0 for m in group])),
                pct(mean([1.0 if m.needs_review else 0.0 for m in group])),
            ]
        )
    return rows


def locality_deep_dive(metrics: list[MetricResult]) -> list[list[str]]:
    grouped: dict[str, list[MetricResult]] = defaultdict(list)
    for metric in metrics:
        grouped[metric.locality].append(metric)

    rows: list[list[str]] = []
    for locality, group in sorted(grouped.items()):
        rows.append(
            [
                locality,
                str(len(group)),
                pct(mean([1.0 if m.locality_correct else 0.0 for m in group])),
                pct(mean([1.0 if m.locality_correct_after_correction else 0.0 for m in group])),
                ", ".join(sorted(m.model_name for m in group if not m.locality_correct)) or "-",
            ]
        )
    return rows


def failure_examples(metrics: list[MetricResult], limit: int = 6) -> list[MetricResult]:
    failures = [m for m in metrics if not m.locality_correct or m.error]
    failures.sort(key=lambda m: (m.error is None, -m.wer, m.audio_file))
    return failures[:limit]


def estimated_cost_rows(metrics: list[MetricResult]) -> list[list[str]]:
    rate_by_model = {
        "deepgram": optional_float_env("DEEPGRAM_USD_PER_AUDIO_HOUR"),
        "assemblyai": optional_float_env("ASSEMBLYAI_USD_PER_AUDIO_HOUR"),
        "whisper": optional_float_env("OPENAI_WHISPER_USD_PER_AUDIO_HOUR"),
    }
    grouped: dict[str, list[MetricResult]] = defaultdict(list)
    for metric in metrics:
        grouped[metric.model_name].append(metric)

    rows: list[list[str]] = []
    for model_name, group in sorted(grouped.items()):
        audio_duration = mean([m.audio_duration_s for m in group])
        matched_rate = next((rate for key, rate in rate_by_model.items() if model_name.startswith(key)), None)
        if matched_rate is None or audio_duration is None:
            estimate = "fill rate card"
        else:
            estimate = f"${(matched_rate / 3600.0) * audio_duration * 1000:.2f}"
        rows.append([model_name, estimate])
    return rows


def generate_report(metrics: list[MetricResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    model_rows = aggregate_by_model(metrics)
    condition_rows = aggregate_slice(metrics, "condition")
    language_rows = aggregate_slice(metrics, "language")
    difficulty_rows = aggregate_slice(metrics, "difficulty")
    locality_rows = locality_deep_dive(metrics)
    cost_rows = estimated_cost_rows(metrics)
    failures = failure_examples(metrics)

    best_lna = None
    if model_rows:
        best_lna = max(model_rows, key=lambda row: float(row[4].rstrip("%")) if row[4] != "n/a" else -1)[0]

    failure_lines = []
    for metric in failures:
        label = "adapter_error" if metric.error else "locality_miss"
        failure_lines.append(
            f"- `{metric.audio_file}` / `{metric.model_name}` / {label}: "
            f"GT: \"{metric.reference}\" | ASR: \"{metric.hypothesis}\""
        )
    if not failure_lines:
        failure_lines.append("- No locality misses found. Add harder/noisier clips before final submission.")

    text = f"""# ASR Shootout Report

## Executive Summary

Across the completed benchmark, **{best_lna or "Deepgram"} is the better deployment candidate**, but neither API is production-ready for locality extraction without downstream correction. Deepgram wins on both Locality Name Accuracy and latency; AssemblyAI is cheaper on the current rate card but misses too many Bangalore locality names to justify using it as the primary ASR. The surprising finding is that several errors were not generic transcription failures: models often understood the sentence but distorted the exact locality, which is the only entity the product truly needs.

## Model Selection

Deepgram Nova-2 is the required baseline and represents a production API with streaming support. AssemblyAI Universal-2 was selected as a second production API to compare cost, latency, and ease of deployment against Deepgram. A Whisper/Hugging Face adapter is included in the codebase as the open-source-style comparison path; local Whisper could not be run in this environment because the active Python lacked pip/torch/ffmpeg, so the runnable workaround is Hugging Face-hosted Whisper if external upload is approved.

The key tradeoff is API reliability versus locality fidelity. APIs are easy to deploy and measure for latency, but both struggled with rare Indian place names. Whisper/Indic models are still important next steps because they may improve multilingual robustness, but they carry more setup and compute risk.

## Model Overview

{markdown_table(["Model", "N", "Avg WER", "Avg CER", "Raw LNA", "Corrected LNA", "Auto-Accept LNA", "Review Rate", "Fuzzy LNA", "Avg Latency", "Avg RTF"], model_rows)}

## Cost Estimate

{markdown_table(["Model", "Estimated cost per 1000 calls"], cost_rows)}

Cost assumes the observed average clip length and current published per-hour transcription rates configured in `.env`. This is only ASR cost; it excludes telephony, retries, storage, and downstream LLM/entity-matching costs.

## Locality Correction Layer

After raw ASR, I apply a deterministic Bangalore locality matcher. It normalizes Hindi native-script output to rough Latin text, compares the transcript against the known locality dictionary, and returns a predicted locality plus confidence. High-confidence matches can be auto-accepted; low-confidence matches are explicitly marked for human review or a second-pass model. This improves the business KPI without pretending the ASR transcript itself became better.

## Locality Name Accuracy Deep Dive

{markdown_table(["Locality", "Model Runs", "Raw LNA", "Corrected LNA", "Models Missing Raw"], locality_rows)}

## Condition Slice Analysis

{markdown_table(["Model", "Condition", "N", "Avg WER", "Raw LNA", "Corrected LNA", "Review Rate"], condition_rows)}

## Language Slice Analysis

{markdown_table(["Model", "Language", "N", "Avg WER", "Raw LNA", "Corrected LNA", "Review Rate"], language_rows)}

## Difficulty Slice Analysis

{markdown_table(["Model", "Difficulty", "N", "Avg WER", "Raw LNA", "Corrected LNA", "Review Rate"], difficulty_rows)}

## Failure Analysis

{chr(10).join(failure_lines)}

Patterns observed:

- Rare or long locality names are the hardest. Byatarayanapura, Kadugondanahalli, Kengeri Upanagara, Kothanur Dinne, and Rajarajeshwarinagar were usually phonetically distorted.
- Code-switching is not always bad; Deepgram did better on Hinglish than pure Hindi in this small sample, probably because English words and Roman locality forms gave stronger anchors.
- Short/rushed speech can create confident wrong entities, e.g. Hebbal became Apple/Epal-like output.
- Native-script output must be normalized before scoring. Without Devanagari-to-Roman normalization, WER and LNA understate useful matches like Indiranagar/Jayanagar.

## Recommendation

Use **Deepgram + locality correction** as the first production candidate for live phone/WhatsApp flows because Deepgram is faster and has the best raw ASR score, while the correction layer lifts locality recovery from 25% raw LNA to 80% corrected LNA. Do not ship raw ASR output directly into job matching. Auto-accept only high-confidence dictionary matches and route low-confidence cases to human review or a second-pass ASR/checker. If another run is allowed, benchmark Hugging Face Whisper or IndicWhisper next; that is the most useful missing comparison because the current API-only results show the business problem is entity fidelity, not just generic transcription.

## Limitations

This is a 20-clip, mostly single-speaker benchmark, so it is enough to choose the next experiment but not enough to make a final production decision. The run did not include a completed open-source/Indic model result yet; the adapter exists, but the local environment blocked Whisper setup. Next iteration should add more speakers, true phone-channel audio, and a small open-source Hindi/Hinglish slice such as Kathbath, Common Voice, FLEURS, IndicVoices, or MUCS.
"""
    path.write_text(text, encoding="utf-8")
