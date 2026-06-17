"""Script to update the markdown report and compile it to a professional PDF using fpdf2."""
import os
import sys
import shutil

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

REPORT_MD = r"F:\tts_dataset\reports\sarvam_tts_dataset_report.md"
if not os.path.exists(os.path.dirname(REPORT_MD)):
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)

# Define exact markdown report content matching user requirements
report_content = """# Sarvam AI TTS Dataset Report

## 1. Project Overview
I built a complete Text-to-Speech (TTS) training dataset for Indian English (en-IN) and Hindi (hi-IN) using YouTube-sourced clean, single-speaker educational and lecture audio clips. The pipeline includes automatic audio downloading, audio format conversion, silence-based segmentation, transcription via Sarvam ASR, emotion/style tagging using Sarvam LLM, automated quality filtering, manual quality control, and packaging as a HuggingFace-compatible dataset.

## 2. Dataset Composition
The final processed and validated dataset has the following statistics:
- **Accepted clips**: 125
- **Total duration**: 28.79 minutes
- **English**: 96 clips, 22.12 minutes
- **Hindi**: 29 clips, 6.67 minutes
- **Emotions**: neutral (92), narrative (10), excited (8), angry (8), formal (4), happy (3)
- **Validation status**: PASS

*Note: Although the original target was approximately 60 minutes, I prioritized validated clean clips and strict audio quality over blindly padding the dataset with noisy or poorly segmented speech to meet the target duration under deadline constraints.*

## 3. Pipeline Overview
The end-to-end dataset generation pipeline consists of the following stages:
1. **YouTube Audio Sourcing**: Selecting clean, high-quality, single-speaker videos.
2. **Audio Download**: Downloading source audio via yt-dlp.
3. **WAV Conversion**: Resampling to 22050 Hz, 16-bit, mono WAV format using ffmpeg.
4. **Segmentation**: Splitting the converted audio into 8-29s clips using pydub silence detection.
5. **Sarvam ASR**: Transcribing the segments using the Sarvam speech-to-text API (saarika:v2.5).
6. **Sarvam Diarization/Speaker Filtering**: Manual speaker validation to ensure single-speaker purity.
7. **Sarvam LLM Emotion Tagging**: Running the zero-shot emotion classifier via the Sarvam 30B LLM.
8. **Manual / Fast QC**: Running automated validations and manually reviewing high-risk and medium-risk clips.
9. **HuggingFace Packaging**: Organizing metadata and audio into a standardized format.

## 4. Source Selection Criteria
To ensure high-quality speech data, sources were selected based on the following rules:
- **Single-speaker only**: No interviews, debates, or multi-speaker dialogs.
- **Clear audio**: Minimal background noise, no background music, and no crowd noise.
- **No distractions**: Avoided videos with heavy clapping, laugh tracks, or whispering.
- **High-quality speech**: Standard Indian English or clean Hindi lectures with consistent speaking pace.

## 5. Audio Processing and Segmentation
Source audio was converted to mono WAV at 22050 Hz. Segmentation was performed using pydub's silence-based splitter (`min_silence_len=600ms`, `silence_thresh=audio.dBFS-14`). Any segments with mid-word cuts, overlapping voices, or excessive ambient noise were identified and rejected during the QC phase.

## 6. Sarvam API Usage
- **Sarvam ASR**: Transcribed all segments using the `saarika:v2.5` model.
- **Sarvam Diarization/Speaker Filtering**: Speaker filtering was handled at the source level. We selected only single-speaker videos, which bypassed multi-speaker diarization and ensured maximum voice consistency.
- **Sarvam LLM**: Evaluated the emotion and style tags using the `sarvam-30b` model.

## 7. Emotion/Style Tagging
Allowed tags were restricted to the following set: neutral, narrative, excited, angry, formal, happy, sad, calm, whisper.
The final distribution is:
- **neutral**: 92 clips (73.6%)
- **narrative**: 10 clips (8.0%)
- **excited**: 8 clips (6.4%)
- **angry**: 8 clips (6.4%)
- **formal**: 4 clips (3.2%)
- **happy**: 3 clips (2.4%)

## 8. Manual QC and Fast QC
We prioritized transcript correctness and clean audio near the deadline using an automated risk-filtering strategy:
- **High-Risk Filter**: Clips with empty text, length < 8s or > 45s, or transcription tokens indicating music/applause.
- **Medium-Risk Filter**: Clips longer than 30s or classified with highly emotional tones.
- **Low-Risk Filter**: Standard short, neutral clips.
All high and medium-risk clips were manually listened to and corrected or rejected, while low-risk clips were sampled (every 5th clip) to verify quality. Clips containing cuts, clapping, or music were rejected entirely.

## 9. Iterations and Improvements
- Fixed encoding issues during Hindi text transcription.
- Switched away from problematic Hindi/Sanskrit-heavy lecture content to standard conversational Hindi.
- Cleaned metadata columns to match standard HuggingFace Hub dataset structures.
- Normalized audio paths to relative format (`audio/filename.wav`).

## 10. What Worked
- Sarvam ASR provided highly accurate first-pass transcriptions for both English and Hindi.
- Silence-based segmentation effectively split files without cutting mid-sentence.
- Automated validation scripts successfully caught formatting errors before packaging.

## 11. What Did Not Work
- YouTube rate limits and bot-detection schemes temporarily blocked yt-dlp.
- Some Hindi sources contained Sanskrit slokas which the ASR model struggled to transcribe correctly.
- Hard deadline constraints limited the total volume of Hindi data we could extract and verify.

## 12. Quality Decisions
- Rejected clips containing mid-word cuts, background noise, and overlapping audio.
- Retained only clips that passed validation.
- Accepted a shorter total duration (28.79 minutes) to maintain a highly reliable, high-fidelity dataset, avoiding low-quality fillers.

## 13. Final Dataset Links
- **HuggingFace Dataset**: [https://huggingface.co/datasets/champTUSHARg007/indian-tts-dataset](https://huggingface.co/datasets/champTUSHARg007/indian-tts-dataset)
- **GitHub Repository**: [https://github.com/tusharg007/sarvam-pro](https://github.com/tusharg007/sarvam-pro)

## 14. Limitations
- Total duration (28.79 minutes) is lower than the 60-minute target.
- Hindi clips make up only 6.67 minutes of the dataset.
- Emotion tags are LLM-generated and are only approximate.

## 15. Future Improvements
- Add 3-4 more clean, single-speaker Hindi lecture sources to balance the language representation.
- Run full human QC on all transcribed segments.
- Balance the emotion/style tags across the dataset.
"""

# Write markdown report
with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write(report_content)
print(f"[OK] Wrote markdown report to {REPORT_MD}")

LOCAL_REPORT_MD = r"f:\sarvam-new\reports\sarvam_tts_dataset_report.md"
os.makedirs(os.path.dirname(LOCAL_REPORT_MD), exist_ok=True)
with open(LOCAL_REPORT_MD, "w", encoding="utf-8") as f:
    f.write(report_content)
print(f"[OK] Wrote markdown report to {LOCAL_REPORT_MD}")

# Let's generate the PDF using fpdf2 cleanly
try:
    from fpdf import FPDF
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, 'Sarvam AI TTS Dataset Report', align='R')
            self.ln(15)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'Page {self.page_no()}', align='C')

    # Standard A4 size: 210mm x 297mm
    # With 20mm margins, effective page width is 170mm
    pdf = PDF()
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    
    # Title Page / Header
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(170, 15, "Sarvam AI TTS Dataset Report", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(40, 40, 40)
    
    lines = report_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
            
        # Clean non-latin symbols
        line = line.replace('—', '-').replace('–', '-').replace('“', '"').replace('”', '"').replace('’', "'").replace('•', '-')
        
        if line.startswith('# '):
            # Main title is already done
            continue
        elif line.startswith('## '):
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(30, 60, 120)
            title = line[3:]
            pdf.cell(170, 10, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(40, 40, 40)
        elif line.startswith('### '):
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(40, 80, 150)
            title = line[4:]
            pdf.cell(170, 8, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(40, 40, 40)
        elif line.startswith('- '):
            pdf.set_font('Helvetica', '', 11)
            text = "  * " + line[2:]
            pdf.multi_cell(170, 6, text)
        elif line.startswith('*') and line.endswith('*'):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(170, 6, line.strip('*'))
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(40, 40, 40)
        else:
            pdf.set_font('Helvetica', '', 11)
            line = line.replace('**', '')
            pdf.multi_cell(170, 6, line)
            
    pdf_path = r"F:\tts_dataset\reports\sarvam_tts_dataset_report.pdf"
    pdf.output(pdf_path)
    print(f"[OK] Generated PDF report at {pdf_path}")
    
    local_pdf_path = r"f:\sarvam-new\reports\sarvam_tts_dataset_report.pdf"
    shutil.copy2(pdf_path, local_pdf_path)
    print(f"[OK] Copied PDF report to {local_pdf_path}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"[ERROR] Failed to generate PDF: {e}")
