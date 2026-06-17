"""Step 1: Inspect existing dataset and print full status."""
import os, csv, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

DATA = r"F:\tts_dataset"
CLEAN = os.path.join(DATA, "outputs", "dataset_clean.csv")
RAW = os.path.join(DATA, "outputs", "dataset_raw.csv")
SEG_EN = os.path.join(DATA, "segments_en")
SEG_HI = os.path.join(DATA, "segments_hi")

# Use raw if clean is locked
csv_path = CLEAN if os.path.isfile(CLEAN) else RAW
print(f"Reading: {csv_path}")
rows = []
with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"\n{'='*60}")
print(f"  DATASET INSPECTION REPORT")
print(f"{'='*60}")
print(f"  Total rows: {len(rows)}")

# Quality flags
flags = Counter(r.get("quality_flag","ok") for r in rows)
for k,v in sorted(flags.items()): print(f"  quality_flag={k}: {v}")

accepted = [r for r in rows if r.get("quality_flag","ok") != "reject"]
print(f"  Accepted (non-reject): {len(accepted)}")

# Duration
total_dur = sum(float(r.get("duration_seconds",0)) for r in accepted)
en = [r for r in accepted if r.get("language")=="en-IN"]
hi = [r for r in accepted if r.get("language")=="hi-IN"]
en_dur = sum(float(r.get("duration_seconds",0)) for r in en)
hi_dur = sum(float(r.get("duration_seconds",0)) for r in hi)
print(f"\n  Total accepted duration: {total_dur/60:.2f} min")
print(f"  English: {len(en)} clips | {en_dur/60:.2f} min")
print(f"  Hindi:   {len(hi)} clips | {hi_dur/60:.2f} min")

# Emotions
emo = Counter(r.get("emotion","") for r in accepted)
print(f"\n  Emotion distribution:")
for e,c in sorted(emo.items(), key=lambda x:-x[1]):
    print(f"    {e:<12} {c:4d} ({c/len(accepted)*100:.1f}%)")

# Issues
missing_text = [r for r in accepted if not r.get("text","").strip()]
print(f"\n  Missing text rows: {len(missing_text)}")

# Missing audio
missing_audio = []
for r in accepted:
    fn = r.get("file_name","")
    if fn.startswith("en_"):
        p = os.path.join(SEG_EN, fn)
    else:
        p = os.path.join(SEG_HI, fn)
    if not os.path.isfile(p):
        missing_audio.append(fn)
print(f"  Missing audio files: {len(missing_audio)}")
for m in missing_audio[:5]: print(f"    {m}")

# Duplicates
fnames = [r.get("file_name","") for r in rows]
dupes = [fn for fn,c in Counter(fnames).items() if c>1]
print(f"  Duplicate file_name: {len(dupes)}")

# Absolute paths
abs_paths = [r for r in rows if "F:\\" in r.get("file_path","") or "C:\\" in r.get("file_path","")]
print(f"  Rows with absolute Windows paths: {len(abs_paths)}")

# Notes with issues
issue_keywords = ["cut","noise","clap","music","two speaker","unclear","background"]
issue_rows = []
for r in accepted:
    notes = (r.get("notes","") or "").lower()
    for kw in issue_keywords:
        if kw in notes:
            issue_rows.append((r.get("file_name",""), kw, r.get("notes","")))
            break
print(f"  Rows with issue notes: {len(issue_rows)}")
for fn,kw,n in issue_rows[:10]: print(f"    {fn}: [{kw}] {n}")

# Missing columns
sample = rows[0] if rows else {}
for col in ["speaker_id","source_url"]:
    has = sum(1 for r in rows if r.get(col,"").strip())
    print(f"  Rows with {col}: {has}/{len(rows)}")

print(f"\n{'='*60}")
print(f"  DECISION: {'NO new data needed' if total_dur/60>=45 else 'May need more data'}")
print(f"{'='*60}")
