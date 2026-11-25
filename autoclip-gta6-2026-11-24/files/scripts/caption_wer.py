"""C4 on the caption text the app itself produced (input.srt, from its local Whisper base) vs OUR commentary text, per clip window.
usage: caption_wer.py <run_dir> <truth.json>  -> <run_dir>/caption_check.json"""
import json, re, sys
from pathlib import Path
import jiwer

run, truth = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
meta = json.loads((run / "clips_meta.json").read_text(encoding="utf-8"))
srt = (run / "meta" / "input.srt").read_text(encoding="utf-8")


def t(s):
    h, m, r = s.split(":"); sec, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


cues = []
for blk in re.split(r"\n\s*\n", srt.strip()):
    ln = blk.strip().splitlines()
    if len(ln) >= 3 and "-->" in ln[1]:
        a, b = ln[1].split("-->"); cues.append((t(a.strip()), t(b.strip()), " ".join(ln[2:])))
norm = lambda x: re.sub(r"[^a-z0-9 ]", "", x.lower().replace("-", " ")).split()
rows = []
for name, m in sorted(meta.items()):
    s0, s1 = m["start"], m["end"]
    ref = [w for x in truth["sentences"] if x["t"] >= s0 - 0.2 and x["t"] + x["dur"] <= s1 + 0.2 for w in norm(x["text"])]
    hyp = [w for a, b, tx in cues if a >= s0 - 0.5 and b <= s1 + 0.5 for w in norm(tx)]
    wer = None if not ref else round(jiwer.wer(" ".join(ref), " ".join(hyp) if hyp else ""), 3)
    rows.append({"clip": name, "ref_words": len(ref), "caption_words": len(hyp), "caption_wer": wer,
                 "C4_caption": None if wer is None else wer <= 0.15})
ok = sum(1 for r in rows if r["C4_caption"] is True)
json.dump({"cues_total": len(cues), "clips": len(rows), "C4_caption_pass": ok, "rows": rows},
          open(run / "caption_check.json", "w", encoding="utf-8"), indent=1)
print(run.name, "cues", len(cues), "pass", ok, "/", len(rows), [r["caption_wer"] for r in rows])
