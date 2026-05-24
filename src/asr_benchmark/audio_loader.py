from __future__ import annotations

import contextlib
import wave
from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def list_audio_files(recordings_dir: Path) -> list[Path]:
    if not recordings_dir.exists():
        raise FileNotFoundError(f"Recordings directory not found: {recordings_dir}")
    return sorted(
        path
        for path in recordings_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def wav_duration_seconds(path: Path) -> float | None:
    if path.suffix.lower() != ".wav":
        return None
    with contextlib.closing(wave.open(str(path), "rb")) as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate) if rate else None


def duration_seconds(path: Path) -> float | None:
    """Return duration for WAV files without heavy dependencies.

    Adapters may override this with model-specific duration metadata for MP3/M4A.
    """
    try:
        return wav_duration_seconds(path)
    except (wave.Error, OSError):
        return None


def validate_dataset(audio_files: list[Path], ground_truth_names: set[str]) -> list[str]:
    warnings: list[str] = []
    audio_names = {path.name for path in audio_files}

    missing_audio = sorted(ground_truth_names - audio_names)
    if missing_audio:
        warnings.append(f"{len(missing_audio)} ground-truth rows have no audio file.")

    missing_ground_truth = sorted(audio_names - ground_truth_names)
    if missing_ground_truth:
        warnings.append(f"{len(missing_ground_truth)} audio files have no ground truth.")

    for path in audio_files:
        if path.suffix.lower() == ".wav":
            dur = duration_seconds(path)
            if dur is not None and not 1.0 <= dur <= 30.0:
                warnings.append(f"{path.name} duration is {dur:.1f}s; target is 1-30s.")

    return warnings

