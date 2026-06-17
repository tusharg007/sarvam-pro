"""Validate the final HuggingFace dataset folder."""
import os, csv, sys
from collections import Counter
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

HF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hf_dataset")
AUDIO = os.path.join(HF, "audio")
META = os.path.join(HF, "metadata.csv")
VALID_EMO = {"neutral","formal","excited","happy","sad","angry","narrative","calm","whisper"}
VALID_LANG = {"en-IN","hi-IN"}

errors = []
rows = list(csv.DictReader(open(META, "r", encoding="utf-8")))
seen = set()

for r in rows:
    fn = r["file_name"].replace("audio/","")
    fp = os.path.join(AUDIO, fn)
    if not os.path.isfile(fp): errors.append(f"MISSING AUDIO: {fn}")
    if not r.get("text","").strip(): errors.append(f"EMPTY TEXT: {fn}")
    if fn in seen: errors.append(f"DUPLICATE: {fn}")
    seen.add(fn)
    if "F:\\" in r["file_name"] or "C:\\" in r["file_name"]: errors.append(f"ABS PATH: {fn}")
    if r.get("language","") not in VALID_LANG: errors.append(f"BAD LANG: {fn}={r['language']}")
    if r.get("emotion","") not in VALID_EMO: errors.append(f"BAD EMO: {fn}={r['emotion']}")
    try: float(r["duration_seconds"])
    except: errors.append(f"BAD DURATION: {fn}")

en = [r for r in rows if r["language"]=="en-IN"]
hi = [r for r in rows if r["language"]=="hi-IN"]
en_d = sum(float(r["duration_seconds"]) for r in en)
hi_d = sum(float(r["duration_seconds"]) for r in hi)
tot = en_d + hi_d
emo = Counter(r["emotion"] for r in rows)

print("="*50)
print("DATASET VALIDATION")
print("="*50)
if errors:
    print(f"FAIL — {len(errors)} errors:")
    for e in errors: print(f"  {e}")
else:
    print("PASS — All checks passed!")
print(f"\nTotal: {len(rows)} clips | {tot/60:.2f} min")
print(f"EN: {len(en)} ({en_d/60:.2f} min) | HI: {len(hi)} ({hi_d/60:.2f} min)")
print(f"Emotions: {dict(emo)}")
print("="*50)
