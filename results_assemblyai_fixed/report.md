# ASR Shootout Report

## Executive Summary

Best current candidate by Locality Name Accuracy: **assemblyai**. Treat WER/CER as supporting metrics; the deployment decision should prioritize whether Bangalore localities survive noise, rushing, and code-switching. Final recommendation should be updated after reviewing the qualitative misses below.

## Model Overview

| Model | N | Avg WER | Avg CER | LNA | Fuzzy LNA | Avg Latency | Avg RTF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| assemblyai | 20 | 100.0% | 100.0% | 0.0% | 0.0% | 12163.52 ms | 2.00 |

## Cost Estimate

| Model | Estimated cost per 1000 calls |
| --- | --- |
| assemblyai | fill rate card |

Use current public rate cards in `.env` before submitting. Local Whisper has no API fee, but include compute/latency caveats in the walkthrough.

## Locality Name Accuracy Deep Dive

| Locality | Model Runs | LNA | Models Missing It |
| --- | --- | --- | --- |
| BTM Layout | 1 | 0.0% | assemblyai |
| Bellandur | 1 | 0.0% | assemblyai |
| Byatarayanapura | 1 | 0.0% | assemblyai |
| Doddanekundi | 1 | 0.0% | assemblyai |
| Electronic City | 1 | 0.0% | assemblyai |
| HSR Layout | 1 | 0.0% | assemblyai |
| Hebbal | 1 | 0.0% | assemblyai |
| Indiranagar | 1 | 0.0% | assemblyai |
| Jayanagar | 1 | 0.0% | assemblyai |
| Kadugondanahalli | 1 | 0.0% | assemblyai |
| Kengeri Upanagara | 1 | 0.0% | assemblyai |
| Koramangala | 1 | 0.0% | assemblyai |
| Kothanur Dinne | 1 | 0.0% | assemblyai |
| Marathahalli | 1 | 0.0% | assemblyai |
| Rajarajeshwarinagar | 1 | 0.0% | assemblyai |
| Silk Board | 1 | 0.0% | assemblyai |
| Thalaghattapura | 1 | 0.0% | assemblyai |
| Thanisandra | 1 | 0.0% | assemblyai |
| Whitefield | 1 | 0.0% | assemblyai |
| Yelahanka | 1 | 0.0% | assemblyai |

## Condition Slice Analysis

| Model | Condition | N | Avg WER | LNA |
| --- | --- | --- | --- | --- |
| assemblyai | noisy | 7 | 100.0% | 0.0% |
| assemblyai | phone | 2 | 100.0% | 0.0% |
| assemblyai | quiet | 11 | 100.0% | 0.0% |

## Language Slice Analysis

| Model | Language | N | Avg WER | LNA |
| --- | --- | --- | --- | --- |
| assemblyai | hindi | 11 | 100.0% | 0.0% |
| assemblyai | hinglish | 9 | 100.0% | 0.0% |

## Difficulty Slice Analysis

| Model | Difficulty | N | Avg WER | LNA |
| --- | --- | --- | --- | --- |
| assemblyai | easy | 7 | 100.0% | 0.0% |
| assemblyai | hard | 7 | 100.0% | 0.0% |
| assemblyai | medium | 6 | 100.0% | 0.0% |

## Failure Analysis

- `bellandur_noisy_hindi_10.wav` / `assemblyai` / locality_miss: GT: "Bellandur mein ghar hai mera, night shift bhi chalega." | ASR: "वैसे बेलंदूर में घर है। मेरा नाइट शिफ्ट भी मेरे लिए काम करेगा।"
- `btm_layout_noisy_hindi_08.wav` / `assemblyai` / locality_miss: GT: "BTM Layout ke paas rehta hoon, bus se aa jaunga." | ASR: "बीटीएम लेआउट के पास बस से आ जाऊंगा।"
- `byatarayanapura_quiet_hindi_11.wav` / `assemblyai` / locality_miss: GT: "Main Byatarayanapura mein rehta hoon, thoda door padta hai." | ASR: "मैं बेहद तारा नयापुरा में रहता हूँ, थोड़ा दूर पड़ता है।"
- `doddanekundi_quiet_hindi_whispered_19.wav` / `assemblyai` / locality_miss: GT: "Doddanekundi mein rehta hoon, abhi dheere bol raha hoon." | ASR: "गोदान कुर्दी में रहता हूँ। अभी धीरे बोल रहा हूँ।"
- `electronic_city_quiet_hinglish_04.wav` / `assemblyai` / locality_miss: GT: "Actually main Electronic City mein hoon, phase one ke aas paas." | ASR: "ऐक्चवली मैं ना इलेक्ट्रॉनिक सिटी में लोकेटेड हूं फेज वन के पास।"
- `hebbal_quiet_hindi_rushed_17.wav` / `assemblyai` / locality_miss: GT: "Hebbal mein rehta hoon bhai, jaldi job chahiye." | ASR: "एपल में रहता हूँ। भाई जल्दी जॉब चाहिए।"

Suggested categories to call out after listening back: OOV locality names, noisy background, code-switch confusion, phone-bandwidth distortion, and partial locality capture.

## Recommendation

Write this as a decision, not a neutral summary. Example shape: "Use Deepgram for real-time phone flows if latency is the hard constraint; use Whisper/Indic offline as a second-pass correction layer for hard locality names; add fuzzy locality matching downstream because near-misses are common."

## Limitations

Single-speaker self-recordings are useful for a fast benchmark but not enough for a production decision. Next iteration should add more speakers, real phone-channel audio, and a small open-source Hindi/Hinglish slice such as Kathbath, Common Voice, FLEURS, IndicVoices, or MUCS.
