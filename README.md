# Indian English + Hindi TTS Dataset Pipeline

An automated pipeline for building a production-grade Text-to-Speech training dataset using **Sarvam AI APIs**, featuring Indian English (en-IN) and Hindi (hi-IN) audio clips with transcriptions and emotion labels.

## Final Dataset Stats

| Metric | Value |
|--------|-------|
| Total clips | 125 |
| Total duration | 28.79 minutes |
| English (en-IN) | 96 clips (22.12 min) |
| Hindi (hi-IN) | 29 clips (6.67 min) |
| Sample rate | 22050 Hz mono WAV |
| Speakers | 8 unique |

## Folder Structure

```
sarvam-pro/
├── scripts/
│   ├── final_build.py          # Master build script (Steps 2-7)
│   ├── step1_inspect.py        # Dataset inspection
│   ├── build_submission.py     # Submission builder
│   ├── validate_dataset.py     # Validation script
│   └── upload_to_hf.py         # HuggingFace upload (requires approval)
├── hf_dataset/
│   ├── audio/                  # 125 WAV files (22050Hz, mono, 16-bit)
│   ├── metadata.csv            # Transcriptions + emotion labels
│   └── README.md               # HuggingFace dataset card
├── reports/
│   ├── sarvam_tts_dataset_report.md   # Full technical report
│   └── qc_remaining_checklist.md      # QC priority checklist
├── dataset_final_candidate.csv  # Final accepted rows
├── dataset_qc_priority.csv      # QC risk-annotated dataset
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites
- Python 3.10+
- ffmpeg in PATH

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Variables
```bash
export SARVAM_API_KEY=your_sarvam_api_key
export HF_TOKEN=your_huggingface_token
export HF_USERNAME=your_huggingface_username
```

## Pipeline Flow

```
1. Source Selection    → YouTube single-speaker educational videos
2. Download            → yt-dlp audio extraction
3. Convert             → ffmpeg → 22050 Hz mono WAV
4. Segment             → pydub silence detection (8-29s clips)
5. Transcribe          → Sarvam ASR (saarika:v2.5)
6. Emotion Tag         → Sarvam LLM (sarvam-30b)
7. QC                  → Automated risk filtering + manual review
8. Package             → HuggingFace dataset folder
9. Upload              → HuggingFace Hub
```

## How to Run

### Inspect existing dataset
```bash
python scripts/step1_inspect.py
```

### Build final submission (Steps 2-7)
```bash
python scripts/final_build.py
```

### Validate dataset
```bash
python scripts/validate_dataset.py
```

### Upload to HuggingFace (requires approval)
```bash
python scripts/upload_to_hf.py
```

## HuggingFace Dataset

**URL**: https://huggingface.co/datasets/champTUSHARg007/indian-english-hindi-tts-sarvam

## Report

See [reports/sarvam_tts_dataset_report.md](reports/sarvam_tts_dataset_report.md) for full technical documentation.

## License

CC-BY-4.0
