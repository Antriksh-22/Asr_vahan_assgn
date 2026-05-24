from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from asr_benchmark.env import load_dotenv_file
from asr_benchmark.ground_truth import load_ground_truth
from asr_benchmark.locality_matcher import LocalityMatcher
from asr_benchmark.metrics import evaluate
from asr_benchmark.report import generate_report, write_metrics_csv, write_transcripts_csv
from asr_benchmark.schema import TranscriptionResult


def repair_mojibake(text: str) -> str:
    if "à¤" not in text and "à¥" not in text:
        return text
    try:
        return text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recompute metrics from saved transcript CSV files.")
    parser.add_argument("--transcripts", nargs="+", required=True)
    parser.add_argument("--ground-truth", default="data/ground_truth.json")
    parser.add_argument("--results-dir", default="results")
    return parser.parse_args()


def load_transcripts(paths: list[Path]) -> list[TranscriptionResult]:
    rows: dict[tuple[str, str], TranscriptionResult] = {}
    for path in paths:
        with path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                result = (
                    TranscriptionResult(
                        model_name=row["model_name"],
                        audio_file=row["audio_file"],
                        transcript=repair_mojibake(row.get("transcript", "")),
                        latency_ms=float(row["latency_ms"]) if row.get("latency_ms") else None,
                        audio_duration_s=float(row["audio_duration_s"]) if row.get("audio_duration_s") else None,
                        confidence=float(row["confidence"]) if row.get("confidence") else None,
                        raw_response=None,
                        error=row.get("error") or None,
                    )
                )
                rows[(result.model_name, result.audio_file)] = result
    return list(rows.values())


def main() -> int:
    args = parse_args()
    load_dotenv_file(PROJECT_ROOT / ".env")
    ground_truth = load_ground_truth(PROJECT_ROOT / args.ground_truth)
    locality_matcher = LocalityMatcher([sample.locality for sample in ground_truth.values()])
    transcript_results = load_transcripts([PROJECT_ROOT / path for path in args.transcripts])

    metric_results = []
    for result in transcript_results:
        sample = ground_truth.get(result.audio_file)
        if sample is None:
            print(f"Skipping {result.audio_file}: no ground truth.")
            continue
        locality_match = locality_matcher.match(result.transcript) if not result.error else None
        metric_results.append(evaluate(result, sample, locality_match=locality_match))

    results_dir = PROJECT_ROOT / args.results_dir
    write_transcripts_csv(transcript_results, results_dir / "raw_transcripts.csv")
    write_metrics_csv(metric_results, results_dir / "metrics.csv")
    generate_report(metric_results, results_dir / "report.md")
    print(f"Recomputed {len(metric_results)} metric rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
