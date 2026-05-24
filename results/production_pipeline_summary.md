# Production Pipeline Results

## Final Recommended Pipeline

```text
Audio
  -> Deepgram first-pass ASR
  -> raw transcript
  -> text normalization
  -> Bangalore locality dictionary matching
  -> confidence score
  -> auto-accept or review
```

## Final Numbers

| Model | Raw LNA | Corrected LNA | Auto-Accept Correct | Review Rate | Auto-Wrong | Avg WER | Avg CER | Avg Latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Deepgram | 25.0% | 80.0% | 11/20 | 45.0% | 0 | 64.8% | 33.9% | 4.8s |
| AssemblyAI | 15.0% | 75.0% | 14/20 | 30.0% | 0 | 91.4% | 49.8% | 12.2s |

## Simple Interpretation

Raw ASR alone is weak for Bangalore locality names. Deepgram directly captured only 5 out of 20 locality names, and AssemblyAI captured only 3 out of 20.

After adding the locality correction layer, Deepgram recovered 16 out of 20 locality names and AssemblyAI recovered 15 out of 20.

Deepgram is still the recommended first-pass ASR because it is faster and has better raw transcript quality.

## What Improved

| Model | Raw Correct | Correct After Pipeline | Improvement |
| --- | ---: | ---: | ---: |
| Deepgram | 5/20 | 16/20 | +11 |
| AssemblyAI | 3/20 | 15/20 | +12 |

## Final Recommendation

Use Deepgram for first-pass transcription, then use the locality dictionary matcher to recover place names from noisy or phonetically distorted ASR output.

Auto-accept only high-confidence predictions. Send low-confidence predictions to a human reviewer or second-pass ASR model.

