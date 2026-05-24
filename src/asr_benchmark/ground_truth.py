from __future__ import annotations

import json
from pathlib import Path

from .schema import AudioSample


def load_ground_truth(path: Path) -> dict[str, AudioSample]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples: dict[str, AudioSample] = {}
    for audio_file, row in data.items():
        samples[audio_file] = AudioSample(audio_file=audio_file, **row)
    return samples

