---
license: cc-by-4.0
task_categories:
  - text-to-speech
  - automatic-speech-recognition
language:
  - en
  - hi
tags:
  - audio
  - tts
  - indian-english
  - hindi
  - speech
  - sarvam
pretty_name: Indian English + Hindi TTS Dataset
size_categories:
  - n<1K
---

# Indian English + Hindi TTS Dataset

A curated TTS training dataset with transcriptions and emotion labels for **Indian English** and **Hindi**, built using Sarvam AI APIs.

## Dataset Summary

| Metric | Value |
|--------|-------|
| Total clips | 125 |
| English (en-IN) | 96 clips (22.1 min) |
| Hindi (hi-IN) | 29 clips (6.7 min) |
| Total duration | 28.8 minutes |
| Sample rate | 22050 Hz |
| Format | WAV (PCM 16-bit, mono) |
| Speakers | 8 unique speakers |

## Emotion Distribution

| Emotion | Count | % |
|---------|-------|---|
| neutral | 92 | 73.6% |
| narrative | 10 | 8.0% |
| excited | 8 | 6.4% |
| angry | 8 | 6.4% |
| formal | 4 | 3.2% |
| happy | 3 | 2.4% |

## Pipeline

1. **Source**: YouTube single-speaker educational videos
2. **Download**: yt-dlp audio extraction
3. **Conversion**: ffmpeg to 22050 Hz mono WAV
4. **Segmentation**: pydub silence detection (8-29s clips)
5. **ASR**: Sarvam AI saarika:v2.5
6. **Emotion Tagging**: Sarvam AI sarvam-30b LLM classification
7. **QC**: Automated risk filtering + manual review of high/medium risk clips

## Limitations

- Dataset size is ~29 minutes — suitable for fine-tuning, not pre-training
- Emotion labels are LLM-generated and may have minor inaccuracies
- Hindi clips include some code-mixing with English
- Some clips may contain minor background noise

## Intended Use

- TTS model fine-tuning for Indian English and Hindi
- ASR benchmarking for Indian languages
- Emotion-aware speech synthesis research

## License
CC-BY-4.0
