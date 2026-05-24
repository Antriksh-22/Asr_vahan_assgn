from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from asr_benchmark.adapters import build_adapters
from asr_benchmark.audio_loader import list_audio_files, validate_dataset
from asr_benchmark.env import load_dotenv_file
from asr_benchmark.ground_truth import load_ground_truth
from asr_benchmark.locality_matcher import LocalityMatcher
from asr_benchmark.metrics import evaluate
from asr_benchmark.report import generate_report, write_metrics_csv, write_transcripts_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark ASR models on Bangalore locality recordings.")
    parser.add_argument("--models", default=None, help="Comma-separated models: deepgram,assemblyai,whisper,indic")
    parser.add_argument("--recordings-dir", default="data/recordings")
    parser.add_argument("--ground-truth", default="data/ground_truth.json")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--allow-missing-audio", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Validate files and config without calling any model.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv_file(PROJECT_ROOT / ".env")

    recordings_dir = PROJECT_ROOT / args.recordings_dir
    ground_truth_path = PROJECT_ROOT / args.ground_truth
    results_dir = PROJECT_ROOT / args.results_dir

    ground_truth = load_ground_truth(ground_truth_path)
    locality_matcher = LocalityMatcher([sample.locality for sample in ground_truth.values()])
    audio_files = list_audio_files(recordings_dir)
    warnings = validate_dataset(audio_files, set(ground_truth))
    for warning in warnings:
        print(f"WARNING: {warning}")

    if args.dry_run:
        print(f"Ground-truth rows: {len(ground_truth)}")
        print(f"Audio files found: {len(audio_files)}")
        print("Dry run complete; no model adapters were loaded.")
        return 0

    if not audio_files and not args.allow_missing_audio:
        print(f"No audio files found in {recordings_dir}. Add recordings or pass --allow-missing-audio.")
        return 2

    selected_names = args.models or os.getenv("BENCHMARK_MODELS", "deepgram,assemblyai,whisper")
    model_names = [name.strip() for name in selected_names.split(",") if name.strip()]
    adapters = build_adapters(model_names)

    transcript_results = []
    metric_results = []
    for adapter in adapters:
        print(f"\n== {adapter.name} ==")
        for audio_path in audio_files:
            sample = ground_truth.get(audio_path.name)
            if sample is None:
                print(f"Skipping {audio_path.name}: no ground truth row.")
                continue

            result = adapter.transcribe(audio_path)
            locality_match = locality_matcher.match(result.transcript) if not result.error else None
            metric = evaluate(result, sample, locality_match=locality_match)
            transcript_results.append(result)
            metric_results.append(metric)
            print(
                f"{audio_path.name}: WER={metric.wer:.2f}, CER={metric.cer:.2f}, "
                f"LNA={metric.locality_correct}, fuzzy={metric.fuzzy_locality_match}"
            )

    if not metric_results:
        print("No metrics produced. Check audio files, ground truth, and selected models.")
        return 3

    write_transcripts_csv(transcript_results, results_dir / "raw_transcripts.csv")
    write_metrics_csv(metric_results, results_dir / "metrics.csv")
    generate_report(metric_results, results_dir / "report.md")
    print(f"\nWrote {results_dir / 'raw_transcripts.csv'}")
    print(f"Wrote {results_dir / 'metrics.csv'}")
    print(f"Wrote {results_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
