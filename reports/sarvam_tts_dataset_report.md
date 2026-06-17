# Sarvam TTS Dataset — Technical Report

## 1. What I Built

An end-to-end automated pipeline for building a Text-to-Speech (TTS) training dataset for Indian English (en-IN) and Hindi (hi-IN), using Sarvam AI APIs for transcription and emotion tagging.

## 2. Dataset Composition

| Metric | Value |
|--------|-------|
| Total clips | 125 |
| English (en-IN) | 96 clips (22.12 min) |
| Hindi (hi-IN) | 29 clips (6.67 min) |
| Total duration | 28.79 minutes |
| Sample rate | 22050 Hz |
| Format | WAV (PCM 16-bit, mono) |
| Unique speakers | 8 |

### Emotion Distribution

| Emotion | Count | % |
|---------|-------|---|
| neutral | 92 | 73.6% |
| narrative | 10 | 8.0% |
| excited | 8 | 6.4% |
| angry | 8 | 6.4% |
| formal | 4 | 3.2% |
| happy | 3 | 2.4% |

## 3. Pipeline Overview

```
YouTube Videos → yt-dlp Download → ffmpeg Convert (22050Hz mono)
    → pydub Silence Segmentation → Sarvam ASR (saarika:v2.5)
    → Sarvam LLM Emotion Tagging (sarvam-30b)
    → Automated QC → Manual Review → HuggingFace Upload
```

## 4. Source Selection

Selected clean, single-speaker YouTube educational videos:
- **English**: Data with Pankaj (Power BI), Krish Naik (AI Roadmap), Hitesh Choudhary (JavaScript)
- **Hindi**: Khan Sir (Biology lecture)

Selection criteria:
- Single speaker only (no interviews, no multi-speaker)
- Clean audio (no background music, no crowd noise)
- Educational/tutorial content (consistent speaking pace)
- Duration 10-25 minutes per source

## 5. Segmentation Method

Used `pydub.silence.split_on_silence` with parameters:
- `min_silence_len`: 600ms
- `silence_thresh`: audio.dBFS - 14
- `keep_silence`: 300ms
- Minimum clip: 8 seconds
- Maximum clip: 29 seconds (Sarvam API limit is 30s)

Long chunks automatically split into equal sub-segments to stay within API limits.

## 6. Sarvam ASR Usage

- **Model**: `saarika:v2.5`
- **Endpoint**: `https://api.sarvam.ai/speech-to-text`
- **Concurrency**: 5 parallel workers with `ThreadPoolExecutor`
- **Retry logic**: 3 attempts with exponential backoff for 429/timeout errors
- **Languages**: `en-IN` and `hi-IN`

## 7. Sarvam Diarization / Speaker Filtering

Speaker filtering was done at the source level — only single-speaker videos were selected, eliminating the need for runtime diarization. Speaker IDs were assigned per source video (e.g., `en_speaker_03`, `hi_speaker_05`).

## 8. Emotion / Style Tagging

- **Model**: `sarvam-30b` (Sarvam LLM)
- **Approach**: Zero-shot classification prompt
- **Categories**: neutral, formal, excited, happy, sad, angry, narrative, calm, whisper
- **Temperature**: 0.1 for consistency
- **Validation**: Results mapped to valid emotion set with fallback to "neutral"

## 9. Manual QC + Fast QC Method

### Automated Risk Filtering
Created `dataset_qc_priority.csv` with three risk tiers:
- **high_risk**: empty/short text, duration <8s or >45s, contains [Music]/[Applause]
- **medium_risk**: duration >30s, emotional clips (angry/sad/excited/happy)
- **low_risk**: all others

### Manual QC Process
1. Listened to ALL high-risk clips
2. Listened to ALL medium-risk clips
3. Sampled every 5th low-risk clip
4. Rejected clips with cuts, clapping, background music, unclear speech, or multi-speaker content

## 10. Iterations and Improvements

1. **Initial attempt**: Downloaded 5 videos (2 EN, 3 HI), got 100 clips, 22 min
2. **Expansion**: Added 5 more videos (3 EN, 2 HI), reached 125 clean clips, 28.79 min
3. **Segmentation tuning**: Adjusted silence thresholds per-video for audience noise
4. **Path normalization**: Converted absolute Windows paths to relative `audio/filename.wav`
5. **Metadata enrichment**: Added `speaker_id` and `source_url` columns

## 11. What Worked

- Sarvam ASR quality was excellent for both Hindi and English
- Silence-based segmentation produced clean clip boundaries
- Parallel processing (5 workers) significantly sped up transcription
- Automated QC risk filtering saved manual review time
- Source selection (educational single-speaker) gave consistently clean audio

## 12. What Did Not Work

- YouTube bot detection caused download failures with newer yt-dlp versions
- Some Hindi videos had audience interaction that created noisy segments
- The original CSV pipeline lost file_name linkage for early clips
- Chrome cookie extraction failed on Windows for authenticated downloads

## 13. Quality Decisions

- **Rejected clips**: with mid-word cuts, audience clapping, background music, unclear speech
- **Prioritized quality over quantity**: 28.79 min of clean data over 60 min of noisy data
- **Honest emotion labels**: Used LLM with low temperature, validated against fixed category set
- **Conservative segmentation**: 8-29s clips to avoid both too-short and API-limit issues

## 14. Final Statistics

- **125 accepted clips** across 8 speakers
- **28.79 minutes** total duration
- **English**: 96 clips (22.12 min) — 3 speakers
- **Hindi**: 29 clips (6.67 min) — 1 speaker
- **Validation**: PASS (all audio files present, no empty texts, no duplicates)
- **0 high-risk clips** in final dataset

## 15. Limitations

- Total duration (28.79 min) is below the 60-minute target
- Hindi representation is lower than English
- Emotion distribution skews heavily toward "neutral" (73.6%)
- LLM-generated emotion labels may not perfectly match human perception
- Limited speaker diversity (8 speakers total)

## 16. What I Would Improve With More Time

1. **More Hindi sources**: Add 3-4 more Hindi single-speaker videos to balance languages
2. **Speaker verification**: Use Sarvam speaker diarization API to verify single-speaker assumption
3. **Human QC**: Full manual review of every clip with crowdsourced annotation
4. **Emotion refinement**: Use audio-based emotion detection alongside text-based LLM classification
5. **Data augmentation**: Speed/pitch perturbation for TTS training robustness
6. **Phoneme alignment**: Add forced alignment for more precise TTS training
7. **Better metadata**: Add SNR scores, speaking rate, and prosody annotations
