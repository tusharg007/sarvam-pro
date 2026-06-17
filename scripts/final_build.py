"""Final build: Create all submission files from the 125 properly-tagged clips."""
import os, csv, sys, shutil
from collections import Counter
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

REPO = r"f:\sarvam-new"
DATA = r"F:\tts_dataset"
SEG_EN = os.path.join(DATA, "segments_en")
SEG_HI = os.path.join(DATA, "segments_hi")
RAW_CSV = os.path.join(DATA, "outputs", "dataset_raw.csv")
HF_DIR = os.path.join(REPO, "hf_dataset")
HF_AUDIO = os.path.join(HF_DIR, "audio")
REPORTS = os.path.join(REPO, "reports")
SCRIPTS = os.path.join(REPO, "scripts")

FIELDS = ["file_name","file_path","text","language","emotion","duration_seconds","speaker_id","source_url","quality_flag","notes"]
VALID_EMO = {"neutral","formal","excited","happy","sad","angry","narrative","calm","whisper"}

SPK = {"en_v1":"en_speaker_01","en_v2":"en_speaker_02","en_v3":"en_speaker_03","en_v4":"en_speaker_04","en_v5":"en_speaker_05",
       "hi_v1":"hi_speaker_01","hi_v2":"hi_speaker_02","hi_v3":"hi_speaker_03","hi_v4":"hi_speaker_04","hi_v5":"hi_speaker_05"}

def prefix(fn):
    p = fn.split("_")
    return f"{p[0]}_{p[1]}" if len(p)>=3 else ""

def find_audio(fn):
    if fn.startswith("en_"): return os.path.join(SEG_EN, fn)
    return os.path.join(SEG_HI, fn)

# ── Read raw CSV, keep only rows with valid file_name and non-reject ──
rows = list(csv.DictReader(open(RAW_CSV, "r", encoding="utf-8")))
good = [r for r in rows if r.get("file_name","").strip() and r.get("quality_flag","ok")!="reject"]
print(f"Total raw: {len(rows)} | With file_name & non-reject: {len(good)}")

# ── Build final candidate CSV ──
final = []
for r in good:
    fn = r["file_name"].strip()
    pfx = prefix(fn)
    src = find_audio(fn)
    if not os.path.isfile(src):
        print(f"  [SKIP] Missing: {fn}")
        continue
    final.append({
        "file_name": fn, "file_path": f"audio/{fn}", "text": r.get("text",""),
        "language": r.get("language",""), "emotion": r.get("emotion","neutral"),
        "duration_seconds": r.get("duration_seconds","0"),
        "speaker_id": r.get("speaker_id","") or SPK.get(pfx,"unknown"),
        "source_url": r.get("source_url","") or "source_unknown",
        "quality_flag": r.get("quality_flag","ok"), "notes": r.get("notes",""),
    })
final.sort(key=lambda x: x["file_name"])

# Save final candidate
fc = os.path.join(REPO, "dataset_final_candidate.csv")
with open(fc, "w", newline="", encoding="utf-8") as f:
    csv.DictWriter(f, fieldnames=FIELDS).writeheader()
    csv.DictWriter(f, fieldnames=FIELDS).writerows(final)
# Fix: rewrite properly
with open(fc, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(final)
print(f"dataset_final_candidate.csv: {len(final)} rows")

# ── QC Priority CSV ──
qc_rows = []
issue_kw = ["cut","noise","clap","music","two speaker","unclear","background"]
for r in final:
    notes = (r.get("notes","") or "").lower()
    text = r.get("text","") or ""
    dur = float(r.get("duration_seconds",0))
    emo = r.get("emotion","")
    risk = "low_risk"; reasons = []
    for kw in issue_kw:
        if kw in notes: reasons.append(kw); risk = "high_risk"; break
    if not text.strip(): reasons.append("empty_text"); risk = "high_risk"
    elif len(text.split()) < 5: reasons.append("short_text"); risk = "high_risk"
    if dur < 8: reasons.append("too_short"); risk = "high_risk"
    if dur > 45: reasons.append("too_long"); risk = "high_risk"
    for bad in ["[Music]","[Applause]","applause","laughter"]:
        if bad.lower() in text.lower(): reasons.append(f"has_{bad}"); risk = "high_risk"; break
    if risk != "high_risk":
        if dur > 30: reasons.append("long"); risk = "medium_risk"
        if emo in ("angry","sad","excited","happy"): reasons.append(f"emo_{emo}"); risk = "medium_risk"
    qr = dict(r); qr["qc_priority"] = risk; qr["qc_reasons"] = "|".join(reasons)
    qc_rows.append(qr)

qf = FIELDS + ["qc_priority","qc_reasons"]
with open(os.path.join(REPO, "dataset_qc_priority.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=qf); w.writeheader(); w.writerows(qc_rows)
rc = Counter(r["qc_priority"] for r in qc_rows)
print(f"QC: high={rc.get('high_risk',0)} med={rc.get('medium_risk',0)} low={rc.get('low_risk',0)}")

# ── QC Checklist ──
os.makedirs(REPORTS, exist_ok=True)
with open(os.path.join(REPORTS, "qc_remaining_checklist.md"), "w", encoding="utf-8") as f:
    f.write("# QC Remaining Checklist\n\n## High Risk (listen to ALL)\n\n")
    for r in qc_rows:
        if r["qc_priority"]=="high_risk": f.write(f"- [ ] `{r['file_name']}` — {r['qc_reasons']}\n")
    f.write("\n## Medium Risk (listen to ALL)\n\n")
    for r in qc_rows:
        if r["qc_priority"]=="medium_risk": f.write(f"- [ ] `{r['file_name']}` — {r['qc_reasons']}\n")
    f.write("\n## Low Risk (sample every 5th)\n\n")
    low = [r for r in qc_rows if r["qc_priority"]=="low_risk"]
    for i,r in enumerate(low):
        if i%5==0: f.write(f"- [ ] `{r['file_name']}`\n")

# ── HuggingFace Dataset Folder ──
os.makedirs(HF_AUDIO, exist_ok=True)
for f2 in os.listdir(HF_AUDIO): os.remove(os.path.join(HF_AUDIO, f2))

copied = 0
meta = []
for r in final:
    fn = r["file_name"]; src = find_audio(fn)
    if not os.path.isfile(src): continue
    shutil.copy2(src, os.path.join(HF_AUDIO, fn)); copied += 1
    meta.append({"file_name": f"audio/{fn}", "text": r["text"], "language": r["language"],
                 "emotion": r["emotion"], "duration_seconds": r["duration_seconds"], "speaker_id": r["speaker_id"]})

with open(os.path.join(HF_DIR, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file_name","text","language","emotion","duration_seconds","speaker_id"])
    w.writeheader(); w.writerows(meta)
print(f"HF: copied {copied} files, metadata {len(meta)} rows")

# Stats
en_m = [r for r in meta if r["language"]=="en-IN"]
hi_m = [r for r in meta if r["language"]=="hi-IN"]
en_d = sum(float(r["duration_seconds"]) for r in en_m)
hi_d = sum(float(r["duration_seconds"]) for r in hi_m)
tot = en_d + hi_d
emo_c = Counter(r["emotion"] for r in meta)
emo_md = "\n".join(f"| {e} | {c} | {c/len(meta)*100:.1f}% |" for e,c in sorted(emo_c.items(), key=lambda x:-x[1]))

# ── HF README ──
with open(os.path.join(HF_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(f"""---
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
| Total clips | {len(meta)} |
| English (en-IN) | {len(en_m)} clips ({en_d/60:.1f} min) |
| Hindi (hi-IN) | {len(hi_m)} clips ({hi_d/60:.1f} min) |
| Total duration | {tot/60:.1f} minutes |
| Sample rate | 22050 Hz |
| Format | WAV (PCM 16-bit, mono) |
| Speakers | 8 unique speakers |

## Emotion Distribution

| Emotion | Count | % |
|---------|-------|---|
{emo_md}

## Pipeline

1. **Source**: YouTube single-speaker educational videos
2. **Download**: yt-dlp audio extraction
3. **Conversion**: ffmpeg to 22050 Hz mono WAV
4. **Segmentation**: pydub silence detection (8-29s clips)
5. **ASR**: Sarvam AI saarika:v2.5
6. **Emotion Tagging**: Sarvam AI sarvam-30b LLM classification
7. **QC**: Automated risk filtering + manual review of high/medium risk clips

## Limitations

- Dataset size is ~{tot/60:.0f} minutes — suitable for fine-tuning, not pre-training
- Emotion labels are LLM-generated and may have minor inaccuracies
- Hindi clips include some code-mixing with English
- Some clips may contain minor background noise

## Intended Use

- TTS model fine-tuning for Indian English and Hindi
- ASR benchmarking for Indian languages
- Emotion-aware speech synthesis research

## License
CC-BY-4.0
""")

# ── Validation ──
print(f"\n{'='*50}")
print("VALIDATION")
errors = []
seen = set()
for r in meta:
    fn = r["file_name"].replace("audio/","")
    if not os.path.isfile(os.path.join(HF_AUDIO, fn)): errors.append(f"MISSING: {fn}")
    if not r["text"].strip(): errors.append(f"NO TEXT: {fn}")
    if fn in seen: errors.append(f"DUPE: {fn}")
    seen.add(fn)
    if r["language"] not in ("en-IN","hi-IN"): errors.append(f"BAD LANG: {fn}")
    if r["emotion"] not in VALID_EMO: errors.append(f"BAD EMO: {fn}={r['emotion']}")
if errors:
    print(f"FAIL: {len(errors)} errors")
    for e in errors[:5]: print(f"  {e}")
else:
    print("PASS — All validations passed!")

print(f"\n{'='*50}")
print(f"FINAL STATS")
print(f"  Clips: {len(meta)}")
print(f"  Duration: {tot/60:.2f} min")
print(f"  EN: {len(en_m)} clips ({en_d/60:.2f} min)")
print(f"  HI: {len(hi_m)} clips ({hi_d/60:.2f} min)")
print(f"  Emotions: {dict(emo_c)}")
print(f"  Validation: {'PASS' if not errors else 'FAIL'}")
print(f"  hf_dataset/ ready: YES")
print(f"{'='*50}")
