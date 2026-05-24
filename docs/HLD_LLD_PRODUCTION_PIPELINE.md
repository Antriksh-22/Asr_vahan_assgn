# ASR Locality Extraction Pipeline - HLD and LLD

## 1. What This Project Is Solving

The hiring platform needs to understand where a candidate lives from phone calls or WhatsApp voice notes.

Example audio:

```text
Haan bhai, main Koramangala mein rehta hoon.
```

The important output is not only the full transcript. The important output is:

```text
locality = Koramangala
```

This matters because jobs are matched by candidate location.

## 2. Basic Pipeline

```text
Audio recording
  -> ASR model
  -> Raw transcript
  -> Text normalization
  -> Locality dictionary matching
  -> Confidence score
  -> Final locality or review queue
```

## 3. Why Raw ASR Is Not Enough

Raw ASR often understands the sentence but damages the locality name.

Examples:

| Correct Locality | ASR Mistake |
| --- | --- |
| Koramangala | core bangla |
| Bellandur | belan door |
| Silk Board | silk road |
| Hebbal | Apple / Epal |
| Thanisandra | thana santra |

For normal transcription, these may look like small mistakes. For this product, they are serious because the job-matching location becomes wrong.

## 4. Final Production Recommendation

Use:

```text
Deepgram first-pass ASR
  -> Bangalore locality dictionary
  -> fuzzy/phonetic matching
  -> confidence threshold
  -> human review or second-pass ASR for low-confidence cases
```

This is better than using raw ASR alone.

## 5. High-Level Design (HLD)

### 5.1 Components

| Component | Responsibility |
| --- | --- |
| Audio Dataset | Stores 20 WAV recordings and metadata |
| Ground Truth Store | Stores correct transcript, locality, language, condition, style |
| ASR Adapter Layer | Sends audio to Deepgram / AssemblyAI / optional Whisper |
| Metric Engine | Computes WER, CER, raw LNA, corrected LNA, latency |
| Locality Matcher | Corrects locality using dictionary + fuzzy matching |
| Review Gate | Marks uncertain predictions for human review |
| Report Generator | Writes metrics CSV and markdown report |

### 5.2 Data Flow

```text
data/recordings/*.wav
  -> run_benchmark.py
  -> ASR adapters
  -> raw transcript
  -> metrics.evaluate()
  -> LocalityMatcher.match()
  -> results/metrics.csv
  -> results/report.md
```

### 5.3 Model Selection

| Model | Why Selected |
| --- | --- |
| Deepgram | Required baseline; production ASR API; lower latency |
| AssemblyAI | Second production ASR API for comparison |
| Hugging Face Whisper Adapter | Added as optional third path when local Whisper setup is blocked |
| Indic Adapter | Added as optional future Indic-language comparison |

Deepgram is recommended because it has better raw ASR quality and lower latency in this benchmark.

## 6. Low-Level Design (LLD)

### 6.1 Main Files

| File | Purpose |
| --- | --- |
| `run_benchmark.py` | Main entry point |
| `recompute_metrics.py` | Recomputes metrics from saved transcripts without rerunning APIs |
| `src/asr_benchmark/adapters/deepgram_adapter.py` | Deepgram API adapter |
| `src/asr_benchmark/adapters/assemblyai_adapter.py` | AssemblyAI API adapter |
| `src/asr_benchmark/locality_matcher.py` | Locality correction layer |
| `src/asr_benchmark/metrics.py` | WER, CER, LNA, normalization logic |
| `src/asr_benchmark/report.py` | Generates final report |
| `data/ground_truth.json` | Correct transcripts and metadata |
| `results/metrics.csv` | Final metrics |
| `results/report.md` | Final written report |

### 6.2 Core Data Objects

#### TranscriptionResult

Stores raw ASR output.

```text
model_name
audio_file
transcript
latency_ms
confidence
error
```

#### MetricResult

Stores evaluation output.

```text
model_name
audio_file
wer
cer
raw locality correctness
corrected locality correctness
predicted locality
confidence
needs_review
latency
condition
language
difficulty
```

#### LocalityMatch

Stores the post-processing output.

```text
predicted_locality
confidence
matched_text
needs_review
```

## 7. Metrics Explained

| Metric | Meaning | Why It Matters |
| --- | --- | --- |
| WER | Word Error Rate | Measures full transcript word mistakes |
| CER | Character Error Rate | Useful for spelling-heavy names |
| Raw LNA | Locality captured directly by ASR | Shows raw model performance |
| Corrected LNA | Locality recovered after dictionary matching | Shows final product pipeline performance |
| Auto-Accept LNA | Corrected locality accepted without review | Measures automation potential |
| Review Rate | Percent sent to human/second-pass review | Measures operational load |
| Latency | Time taken by ASR API | Important for phone/WhatsApp flows |

## 8. Final Results

| Model | Raw LNA | Corrected LNA | Auto-Accept Correct | Review Rate | Auto-Wrong | Avg WER | Avg CER | Avg Latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Deepgram | 25.0% | 80.0% | 11/20 | 45.0% | 0 | 64.8% | 33.9% | 4.8s |
| AssemblyAI | 15.0% | 75.0% | 14/20 | 30.0% | 0 | 91.4% | 49.8% | 12.2s |

## 9. Interpretation

Deepgram is better as the first-pass ASR because:

- It has lower WER.
- It has lower CER.
- It has higher raw LNA.
- It is much faster.

AssemblyAI becomes competitive after dictionary correction, but Deepgram still has stronger raw transcript quality and lower latency.

## 10. Final Production Pipeline

```text
1. Candidate sends voice note or speaks on phone.
2. Audio is stored as WAV/MP3.
3. Deepgram transcribes the audio.
4. Raw transcript is saved.
5. Text is normalized.
6. Devanagari output is converted to rough Latin text.
7. Transcript is matched against Bangalore locality dictionary.
8. A confidence score is calculated.
9. If confidence is high, locality is auto-accepted.
10. If confidence is low, send to human review or second-pass ASR.
11. Final locality is sent to job-matching system.
```

## 11. Why This Is Better Than Fine-Tuning

Fine-tuning is not suitable here because there are only 20 recordings. That is too little data and would overfit to one speaker.

Dictionary-based correction is better for this stage because:

- It is simple.
- It is explainable.
- It directly improves the business KPI.
- It does not require GPU training.
- It can be updated whenever new localities are added.

## 12. Limitations

- Only 20 recordings.
- Mostly one speaker.
- No completed open-source Whisper/Indic model run yet.
- Real production audio may have more noise and accents.
- Locality correction depends on a known locality dictionary.

## 13. Next Improvements

- Run Hugging Face Whisper as third model.
- Add more speakers.
- Add true phone-call compressed audio.
- Add phonetic algorithms such as Soundex/Metaphone.
- Add top-3 locality suggestions.
- Add manual review UI for low-confidence cases.

