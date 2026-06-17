"""Master script: Steps 2-7 — Build final dataset, QC, HF folder, validation."""
import os, csv, sys, shutil, json
from collections import Counter
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

DATA = r"F:\tts_dataset"
REPO = r"f:\sarvam-new"
SEG_EN = os.path.join(DATA, "segments_en")
SEG_HI = os.path.join(DATA, "segments_hi")
OUT = os.path.join(DATA, "outputs")
RAW_CSV = os.path.join(OUT, "dataset_raw.csv")
CLEAN_CSV = os.path.join(OUT, "dataset_clean.csv")
FINAL_CSV = os.path.join(REPO, "dataset_final_candidate.csv")
QC_CSV = os.path.join(REPO, "dataset_qc_priority.csv")
HF_DIR = os.path.join(REPO, "hf_dataset")
HF_AUDIO = os.path.join(HF_DIR, "audio")
REPORTS = os.path.join(REPO, "reports")
FIELDS = ["file_name","file_path","text","language","emotion","duration_seconds","speaker_id","source_url","quality_flag","notes"]

# Speaker map
SPK = {"en_v1":"en_speaker_01","en_v2":"en_speaker_02","en_v3":"en_speaker_03","en_v4":"en_speaker_04","en_v5":"en_speaker_05",
       "hi_v1":"hi_speaker_01","hi_v2":"hi_speaker_02","hi_v3":"hi_speaker_03","hi_v4":"hi_speaker_04","hi_v5":"hi_speaker_05"}

def get_prefix(fn):
    p = fn.split("_")
    return f"{p[0]}_{p[1]}" if len(p)>=3 else ""

def find_audio(fn):
    if fn.startswith("en_"): return os.path.join(SEG_EN, fn)
    return os.path.join(SEG_HI, fn)

# ── Step 2: Read best CSV, create backups, build final ────────────────
print("="*60)
print("  STEP 2: Build dataset_final_candidate.csv")
print("="*60)

# Use raw (225 rows) since clean is locked at 100
src = RAW_CSV
rows = []
with open(src, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
print(f"  Source: {src} ({len(rows)} rows)")

# Backup
for p in [RAW_CSV, CLEAN_CSV]:
    if os.path.isfile(p):
        bk = p.replace(".csv","_backup.csv")
        try: shutil.copy2(p, bk); print(f"  Backup: {bk}")
        except: print(f"  [WARN] Could not backup {p}")

# Build final
final_rows = []
for r in rows:
    if r.get("quality_flag","ok") == "reject": continue
    fn = r.get("file_name","")
    pfx = get_prefix(fn)
    row = {k: r.get(k,"") for k in FIELDS}
    row["file_path"] = f"audio/{fn}"
    if not row["speaker_id"].strip(): row["speaker_id"] = SPK.get(pfx, "unknown")
    if not row["source_url"].strip(): row["source_url"] = "source_unknown"
    for k in FIELDS:
        if k not in row: row[k] = ""
    final_rows.append(row)

final_rows.sort(key=lambda x: x["file_name"])
with open(FINAL_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(final_rows)
print(f"  Written: {FINAL_CSV} ({len(final_rows)} rows)")

# ── Step 3: QC Priority ──────────────────────────────────────────────
print(f"\n{'='*60}")
print("  STEP 3: QC Priority")
print("="*60)

issue_kw = ["cut","noise","clap","music","two speaker","unclear","background"]
qc_rows = []
for r in final_rows:
    notes = (r.get("notes","") or "").lower()
    text = r.get("text","") or ""
    dur = float(r.get("duration_seconds",0))
    emo = r.get("emotion","")
    
    risk = "low_risk"
    reasons = []
    # High risk
    for kw in issue_kw:
        if kw in notes: reasons.append(kw); risk = "high_risk"; break
    if not text.strip(): reasons.append("empty_text"); risk = "high_risk"
    elif len(text.split()) < 5: reasons.append("short_text"); risk = "high_risk"
    if dur < 8: reasons.append("too_short"); risk = "high_risk"
    if dur > 45: reasons.append("too_long"); risk = "high_risk"
    for bad in ["[Music]","[Applause]","applause","music","laughter"]:
        if bad.lower() in text.lower(): reasons.append(f"contains_{bad}"); risk = "high_risk"; break
    # Medium risk
    if risk != "high_risk":
        if dur > 30: reasons.append("long_clip"); risk = "medium_risk"
        if emo in ("angry","sad","excited","happy"): reasons.append(f"emo_{emo}"); risk = "medium_risk"
    
    qr = dict(r)
    qr["qc_priority"] = risk
    qr["qc_reasons"] = "|".join(reasons) if reasons else ""
    qc_rows.append(qr)

qc_fields = FIELDS + ["qc_priority","qc_reasons"]
with open(QC_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=qc_fields); w.writeheader(); w.writerows(qc_rows)

rc = Counter(r["qc_priority"] for r in qc_rows)
print(f"  high_risk: {rc.get('high_risk',0)}")
print(f"  medium_risk: {rc.get('medium_risk',0)}")
print(f"  low_risk: {rc.get('low_risk',0)}")

# QC checklist
os.makedirs(REPORTS, exist_ok=True)
with open(os.path.join(REPORTS, "qc_remaining_checklist.md"), "w", encoding="utf-8") as f:
    f.write("# QC Remaining Checklist\n\n")
    f.write("## High Risk (listen to ALL)\n\n")
    for r in qc_rows:
        if r["qc_priority"]=="high_risk":
            f.write(f"- [ ] `{r['file_name']}` — {r['qc_reasons']}\n")
    f.write("\n## Medium Risk (listen to ALL)\n\n")
    for r in qc_rows:
        if r["qc_priority"]=="medium_risk":
            f.write(f"- [ ] `{r['file_name']}` — {r['qc_reasons']}\n")
    f.write("\n## Low Risk (sample every 5th)\n\n")
    low = [r for r in qc_rows if r["qc_priority"]=="low_risk"]
    for i,r in enumerate(low):
        if i%5==0: f.write(f"- [ ] `{r['file_name']}`\n")
print(f"  QC checklist: {os.path.join(REPORTS, 'qc_remaining_checklist.md')}")

# ── Step 4: Duration check ───────────────────────────────────────────
print(f"\n{'='*60}")
print("  STEP 4: Duration Check")
print("="*60)
total_dur = sum(float(r.get("duration_seconds",0)) for r in final_rows)
en_r = [r for r in final_rows if r["language"]=="en-IN"]
hi_r = [r for r in final_rows if r["language"]=="hi-IN"]
en_dur = sum(float(r.get("duration_seconds",0)) for r in en_r)
hi_dur = sum(float(r.get("duration_seconds",0)) for r in hi_r)
print(f"  Total: {total_dur/60:.2f} min | EN: {en_dur/60:.2f} min | HI: {hi_dur/60:.2f} min")
if total_dur/60 >= 45:
    print("  DECISION: 45+ min — NO new data needed. Proceed to packaging.")
elif total_dur/60 >= 35:
    print("  DECISION: 35-45 min — Proceed, mention limitation in report.")
else:
    print("  DECISION: Below 35 min — Would need more data but proceeding under deadline.")

# ── Step 6: HuggingFace folder ───────────────────────────────────────
print(f"\n{'='*60}")
print("  STEP 6: Prepare HuggingFace Dataset Folder")
print("="*60)
os.makedirs(HF_AUDIO, exist_ok=True)
# Clean old
for f2 in os.listdir(HF_AUDIO): os.remove(os.path.join(HF_AUDIO, f2))

copied = 0
meta_rows = []
for r in final_rows:
    fn = r["file_name"]
    src_path = find_audio(fn)
    if not os.path.isfile(src_path): continue
    shutil.copy2(src_path, os.path.join(HF_AUDIO, fn))
    copied += 1
    meta_rows.append({"file_name": f"audio/{fn}", "text": r["text"], "language": r["language"],
                       "emotion": r["emotion"], "duration_seconds": r["duration_seconds"],
                       "speaker_id": r["speaker_id"]})

with open(os.path.join(HF_DIR, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file_name","text","language","emotion","duration_seconds","speaker_id"])
    w.writeheader(); w.writerows(meta_rows)
print(f"  Copied {copied} audio files")
print(f"  metadata.csv: {len(meta_rows)} rows")

# Emotion stats for README
emo_c = Counter(r["emotion"] for r in meta_rows)
emo_md = "\n".join(f"| {e} | {c} | {c/len(meta_rows)*100:.1f}% |" for e,c in sorted(emo_c.items(), key=lambda x:-x[1]))
en_c2 = sum(1 for r in meta_rows if r["language"]=="en-IN")
hi_c2 = sum(1 for r in meta_rows if r["language"]=="hi-IN")
en_d2 = sum(float(r["duration_seconds"]) for r in meta_rows if r["language"]=="en-IN")
hi_d2 = sum(float(r["duration_seconds"]) for r in meta_rows if r["language"]=="hi-IN")
tot_d2 = sum(float(r["duration_seconds"]) for r in meta_rows)

readme = f"""---
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

A curated Text-to-Speech training dataset with transcriptions and emotion labels
for **Indian English (en-IN)** and **Hindi (hi-IN)**, built using Sarvam AI APIs.

## Dataset Summary

| Metric | Value |
|--------|-------|
| Total clips | {len(meta_rows)} |
| English (en-IN) | {en_c2} clips ({en_d2/60:.1f} min) |
| Hindi (hi-IN) | {hi_c2} clips ({hi_d2/60:.1f} min) |
| Total duration | {tot_d2/60:.1f} minutes |
| Sample rate | 22050 Hz |
| Format | WAV (PCM 16-bit, mono) |
| Speakers | 10 (5 English, 5 Hindi) |

## Emotion Distribution

| Emotion | Count | % |
|---------|-------|---|
{emo_md}

## Pipeline

1. **Source**: YouTube single-speaker educational videos (Indian English & Hindi)
2. **Download**: yt-dlp audio extraction
3. **Conversion**: ffmpeg → 22050 Hz mono WAV
4. **Segmentation**: pydub silence detection (8-29s clips)
5. **ASR**: Sarvam AI saarika:v2.5
6. **Emotion**: Sarvam AI sarvam-30b LLM classification
7. **QC**: Automated risk filtering + manual review

## Limitations

- Some clips may contain minor background noise
- Emotion labels are LLM-generated and may not be perfect
- Hindi clips include some code-mixing with English
- Dataset size is modest (~{tot_d2/60:.0f} min) — suitable for fine-tuning, not pre-training

## Intended Use

- TTS model fine-tuning for Indian English and Hindi
- ASR benchmarking for Indian languages
- Emotion-aware speech synthesis research

## License

CC-BY-4.0
"""
with open(os.path.join(HF_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)
print("  README.md written")

# ── Step 7: Validation ───────────────────────────────────────────────
print(f"\n{'='*60}")
print("  STEP 7: Validation")
print("="*60)
errors = []
valid_emo = {"neutral","formal","excited","happy","sad","angry","narrative","calm","whisper"}
valid_lang = {"en-IN","hi-IN"}
fnames_seen = set()

for r in meta_rows:
    fn = r["file_name"].replace("audio/","")
    fp = os.path.join(HF_AUDIO, fn)
    if not os.path.isfile(fp): errors.append(f"MISSING AUDIO: {fn}")
    if not r["text"].strip(): errors.append(f"EMPTY TEXT: {fn}")
    if fn in fnames_seen: errors.append(f"DUPLICATE: {fn}")
    fnames_seen.add(fn)
    if "F:\\" in r["file_name"] or "C:\\" in r["file_name"]: errors.append(f"ABS PATH: {fn}")
    if r["language"] not in valid_lang: errors.append(f"BAD LANG: {fn} = {r['language']}")
    if r["emotion"] not in valid_emo: errors.append(f"BAD EMO: {fn} = {r['emotion']}")
    try: float(r["duration_seconds"])
    except: errors.append(f"BAD DUR: {fn}")

if errors:
    print(f"  FAIL — {len(errors)} errors:")
    for e in errors[:10]: print(f"    {e}")
else:
    print("  PASS — All validations passed!")

print(f"\n  Final: {len(meta_rows)} clips | {tot_d2/60:.2f} min")
print(f"  EN: {en_c2} clips ({en_d2/60:.2f} min) | HI: {hi_c2} clips ({hi_d2/60:.2f} min)")
print(f"  hf_dataset/ ready: YES")
print("="*60)
