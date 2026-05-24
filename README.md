# ASR Benchmark - Indian Conversational Speech

This project benchmarks ASR systems on self-recorded Bangalore locality utterances for a blue-collar hiring workflow. The primary business metric is whether the locality name is transcribed correctly, not just aggregate WER.

## Model Plan

Required baseline:

- `deepgram`: Deepgram Nova, API-based production baseline.

Recommended comparison set:

- `assemblyai`: API-based production alternative for latency/cost comparison.
- `whisper`: local OpenAI Whisper, strong multilingual open-source baseline.
- `hf-whisper`: Hugging Face-hosted Whisper, useful when local torch/ffmpeg setup is blocked.
- `indic`: Hugging Face Indic ASR model, useful for Indian-language coverage when compute allows.

Run at least `deepgram,assemblyai,whisper` for a strong submission. If local Whisper setup is blocked, use `deepgram,assemblyai,hf-whisper` and document the workaround honestly.

## API Keys Needed

- `DEEPGRAM_API_KEY` - required.
- `ASSEMBLYAI_API_KEY` - recommended as the second API benchmark.
- `HF_TOKEN` - optional for local runs; required for `hf-whisper` or gated Hugging Face models.
- `OPENAI_API_KEY` - not needed for the default local Whisper path.

## Quick Start

```powershell
cd asr_benchmark
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Put the 20 recordings in `data/recordings/`, then edit `data/ground_truth.json` with the exact sentence spoken in each file.

Run a small smoke test with metrics only:

```powershell
python -m unittest discover -s tests
```

Run the benchmark:

```powershell
python run_benchmark.py --models deepgram,assemblyai,hf-whisper
```

Outputs:

- `results/raw_transcripts.csv`
- `results/metrics.csv`
- `results/report.md`

## Recording Guidance

Use natural phone-call style sentences. Do not record all clips in the same tone and room. The report is stronger when the dataset includes quiet, noisy, phone-like, rushed, and whispered samples.

The included `data/recording_manifest.csv` gives a balanced 20-sample plan.

## Report Positioning

Keep `results/report.md` under three pages. Lead with:

1. Which model should be used and under what constraint.
2. Locality Name Accuracy, then WER/CER.
3. Three concrete failures with ground truth vs model output.
4. Caveats: single speaker, small sample size, limited noise profiles, compute/API constraints.



(<img width="1540" height="1100" alt="image" src="https://github.com/user-attachments/assets/3e64e505-1958-4c63-91bb-e01eeee449a4" />)

(<img width="1540" height="1100" alt="image" src="https://github.com/user-attachments/assets/215c2a5a-623d-4024-9f86-106dc9045587" />)
