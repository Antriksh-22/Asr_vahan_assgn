# ASR Shootout Report

## Executive Summary

Across the completed benchmark, **deepgram is the better deployment candidate**, but neither API is production-ready for locality extraction without downstream correction. Deepgram wins on both Locality Name Accuracy and latency; AssemblyAI is cheaper on the current rate card but misses too many Bangalore locality names to justify using it as the primary ASR. The surprising finding is that several errors were not generic transcription failures: models often understood the sentence but distorted the exact locality, which is the only entity the product truly needs.

## Model Selection

Deepgram Nova-2 is the required baseline and represents a production API with streaming support. AssemblyAI Universal-2 was selected as a second production API to compare cost, latency, and ease of deployment against Deepgram. A Whisper/Hugging Face adapter is included in the codebase as the open-source-style comparison path; local Whisper could not be run in this environment because the active Python lacked pip/torch/ffmpeg, so the runnable workaround is Hugging Face-hosted Whisper if external upload is approved.

The key tradeoff is API reliability versus locality fidelity. APIs are easy to deploy and measure for latency, but both struggled with rare Indian place names. Whisper/Indic models are still important next steps because they may improve multilingual robustness, but they carry more setup and compute risk.

## Model Overview

| Model | N | Avg WER | Avg CER | Raw LNA | Corrected LNA | Auto-Accept LNA | Review Rate | Fuzzy LNA | Avg Latency | Avg RTF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| assemblyai | 20 | 91.4% | 49.8% | 15.0% | 75.0% | 70.0% | 30.0% | 10.0% | 12163.52 ms | 2.00 |
| deepgram | 20 | 64.8% | 33.9% | 25.0% | 80.0% | 55.0% | 45.0% | 25.0% | 4834.89 ms | 0.79 |

## Cost Estimate

| Model | Estimated cost per 1000 calls |
| --- | --- |
| assemblyai | $0.26 |
| deepgram | $0.60 |

Cost assumes the observed average clip length and current published per-hour transcription rates configured in `.env`. This is only ASR cost; it excludes telephony, retries, storage, and downstream LLM/entity-matching costs.

## Locality Correction Layer

After raw ASR, I apply a deterministic Bangalore locality matcher. It normalizes Hindi native-script output to rough Latin text, compares the transcript against the known locality dictionary, and returns a predicted locality plus confidence. High-confidence matches can be auto-accepted; low-confidence matches are explicitly marked for human review or a second-pass model. This improves the business KPI without pretending the ASR transcript itself became better.

## Locality Name Accuracy Deep Dive

| Locality | Model Runs | Raw LNA | Corrected LNA | Models Missing Raw |
| --- | --- | --- | --- | --- |
| BTM Layout | 2 | 0.0% | 50.0% | assemblyai, deepgram |
| Bellandur | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Byatarayanapura | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Doddanekundi | 2 | 0.0% | 0.0% | assemblyai, deepgram |
| Electronic City | 2 | 50.0% | 50.0% | assemblyai |
| HSR Layout | 2 | 50.0% | 100.0% | assemblyai |
| Hebbal | 2 | 0.0% | 0.0% | assemblyai, deepgram |
| Indiranagar | 2 | 100.0% | 100.0% | - |
| Jayanagar | 2 | 100.0% | 100.0% | - |
| Kadugondanahalli | 2 | 0.0% | 50.0% | assemblyai, deepgram |
| Kengeri Upanagara | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Koramangala | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Kothanur Dinne | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Marathahalli | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Rajarajeshwarinagar | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Silk Board | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Thalaghattapura | 2 | 50.0% | 100.0% | deepgram |
| Thanisandra | 2 | 0.0% | 100.0% | assemblyai, deepgram |
| Whitefield | 2 | 50.0% | 50.0% | assemblyai |
| Yelahanka | 2 | 0.0% | 50.0% | assemblyai, deepgram |

## Condition Slice Analysis

| Model | Condition | N | Avg WER | Raw LNA | Corrected LNA | Review Rate |
| --- | --- | --- | --- | --- | --- | --- |
| assemblyai | noisy | 7 | 92.6% | 14.3% | 71.4% | 28.6% |
| assemblyai | phone | 2 | 95.5% | 0.0% | 100.0% | 0.0% |
| assemblyai | quiet | 11 | 89.8% | 18.2% | 72.7% | 36.4% |
| deepgram | noisy | 7 | 63.1% | 14.3% | 85.7% | 42.9% |
| deepgram | phone | 2 | 42.7% | 50.0% | 100.0% | 0.0% |
| deepgram | quiet | 11 | 69.8% | 27.3% | 72.7% | 54.5% |

## Language Slice Analysis

| Model | Language | N | Avg WER | Raw LNA | Corrected LNA | Review Rate |
| --- | --- | --- | --- | --- | --- | --- |
| assemblyai | hindi | 11 | 88.9% | 9.1% | 72.7% | 36.4% |
| assemblyai | hinglish | 9 | 94.3% | 22.2% | 77.8% | 22.2% |
| deepgram | hindi | 11 | 77.4% | 18.2% | 72.7% | 54.5% |
| deepgram | hinglish | 9 | 49.3% | 33.3% | 88.9% | 33.3% |

## Difficulty Slice Analysis

| Model | Difficulty | N | Avg WER | Raw LNA | Corrected LNA | Review Rate |
| --- | --- | --- | --- | --- | --- | --- |
| assemblyai | easy | 7 | 88.8% | 28.6% | 71.4% | 28.6% |
| assemblyai | hard | 7 | 92.9% | 14.3% | 71.4% | 42.9% |
| assemblyai | medium | 6 | 92.6% | 0.0% | 83.3% | 16.7% |
| deepgram | easy | 7 | 68.3% | 42.9% | 71.4% | 42.9% |
| deepgram | hard | 7 | 65.1% | 0.0% | 85.7% | 71.4% |
| deepgram | medium | 6 | 60.3% | 33.3% | 83.3% | 16.7% |

## Failure Analysis

- `bellandur_noisy_hindi_10.wav` / `assemblyai` / locality_miss: GT: "Bellandur mein ghar hai mera, night shift bhi chalega." | ASR: "वैसे बेलंदूर में घर है। मेरा नाइट शिफ्ट भी मेरे लिए काम करेगा।"
- `bellandur_noisy_hindi_10.wav` / `deepgram` / locality_miss: GT: "Bellandur mein ghar hai mera, night shift bhi chalega." | ASR: "वैसे बेलन दूर में घर है मेरा night shift भी मेरे लिए काम करेगा."
- `electronic_city_quiet_hinglish_04.wav` / `assemblyai` / locality_miss: GT: "Actually main Electronic City mein hoon, phase one ke aas paas." | ASR: "ऐक्चवली मैं ना इलेक्ट्रॉनिक सिटी में लोकेटेड हूं फेज वन के पास।"
- `hebbal_quiet_hindi_rushed_17.wav` / `assemblyai` / locality_miss: GT: "Hebbal mein rehta hoon bhai, jaldi job chahiye." | ASR: "एपल में रहता हूँ। भाई जल्दी जॉब चाहिए।"
- `kadugondanahalli_noisy_hinglish_12.wav` / `assemblyai` / locality_miss: GT: "Kadugondanahalli side mera room hai, location thoda confusing hai." | ASR: "का्डुवोर्डनलीसाइड मेरा घूमा लोकेशन थोड़ा कंक्लूजिंग।"
- `rajarajeshwarinagar_quiet_hindi_13.wav` / `assemblyai` / locality_miss: GT: "Rajarajeshwarinagar mein rehta hoon, wahan se commute kar lunga." | ASR: "राजा राजेश्वरी नगर में रहता हूँ। वहाँ से कमजोर कर लूंगा।"

Patterns observed:

- Rare or long locality names are the hardest. Byatarayanapura, Kadugondanahalli, Kengeri Upanagara, Kothanur Dinne, and Rajarajeshwarinagar were usually phonetically distorted.
- Code-switching is not always bad; Deepgram did better on Hinglish than pure Hindi in this small sample, probably because English words and Roman locality forms gave stronger anchors.
- Short/rushed speech can create confident wrong entities, e.g. Hebbal became Apple/Epal-like output.
- Native-script output must be normalized before scoring. Without Devanagari-to-Roman normalization, WER and LNA understate useful matches like Indiranagar/Jayanagar.

## Recommendation

Use **Deepgram + locality correction** as the first production candidate for live phone/WhatsApp flows because Deepgram is faster and has the best raw ASR score, while the correction layer lifts locality recovery from 25% raw LNA to 80% corrected LNA. Do not ship raw ASR output directly into job matching. Auto-accept only high-confidence dictionary matches and route low-confidence cases to human review or a second-pass ASR/checker. If another run is allowed, benchmark Hugging Face Whisper or IndicWhisper next; that is the most useful missing comparison because the current API-only results show the business problem is entity fidelity, not just generic transcription.

## Limitations

This is a 20-clip, mostly single-speaker benchmark, so it is enough to choose the next experiment but not enough to make a final production decision. The run did not include a completed open-source/Indic model result yet; the adapter exists, but the local environment blocked Whisper setup. Next iteration should add more speakers, true phone-channel audio, and a small open-source Hindi/Hinglish slice such as Kathbath, Common Voice, FLEURS, IndicVoices, or MUCS.
