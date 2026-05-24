from __future__ import annotations

from .base import BaseASRAdapter


ADAPTER_IMPORTS = {
    "deepgram": ("deepgram_adapter", "DeepgramAdapter"),
    "assemblyai": ("assemblyai_adapter", "AssemblyAIAdapter"),
    "whisper": ("whisper_adapter", "WhisperAdapter"),
    "hf-whisper": ("hf_inference_adapter", "HuggingFaceWhisperAdapter"),
    "indic": ("indic_adapter", "IndicAdapter"),
}


def build_adapters(model_names: list[str]) -> list[BaseASRAdapter]:
    adapters: list[BaseASRAdapter] = []
    for name in model_names:
        key = name.strip().lower()
        if not key:
            continue
        if key not in ADAPTER_IMPORTS:
            known = ", ".join(sorted(ADAPTER_IMPORTS))
            raise ValueError(f"Unknown model {name!r}. Known models: {known}")
        module_name, class_name = ADAPTER_IMPORTS[key]
        module = __import__(f"asr_benchmark.adapters.{module_name}", fromlist=[class_name])
        adapters.append(getattr(module, class_name)())
    return adapters
