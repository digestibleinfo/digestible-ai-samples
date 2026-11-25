"""Our own checker for autoclip output clips (criteria C1-C5). Not the app's scores.
usage: check_clips.py <clips_dir> <truth.json> <out.json> [--meta clips_meta.json] [--sheet sheet.png]
truth.json: {"duration": s, "sentences": [{"t": start_s, "dur": s, "text": str}, ...], "window": [30, 90]}
meta (optional): {"<clip file name>": {"start": s, "end": s}} source offsets from the app's own metadata.
Runs on CPU (faster-whisper small, int8) so it never touches the GPU."""
import argparse, json, re, subprocess, sys
from pathlib import Path

FFMPEG = r"ffmpeg"
FFPROBE = r"ffprobe"


def probe(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", str(p)], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    st = d.get("streams", [])
    v = next((s for s in st if s.get("codec_type") == "video"), None)
    a = next((s for s in st if s.get("codec_type") == "audio"), None)
    return float(d.get("format", {}).get("duration", 0)), v, a


def decodes(p):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", str(p), "-f", "null", "-"], capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip()


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower().replace("-", " ")).split()


def wer(ref, hyp):
    import jiwer
    if not ref: return None
    return jiwer.wer(" ".join(ref), " ".join(hyp) if hyp else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips"); ap.add_argument("truth"); ap.add_argument("out")
    ap.add_argument("--meta"); ap.add_argument("--sheet")
    a = ap.parse_args()
    truth = json.loads(Path(a.truth).read_text(encoding="utf-8"))
    lo, hi = truth.get("window", [30, 90])
    sents = truth["sentences"]
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8")) if a.meta else {}
    clips = sorted(p for p in Path(a.clips).glob("*") if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm"))
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    rows = []
    for p in clips:
        dur, v, au = probe(p)
        row = {"clip": p.name, "duration": round(dur, 2), "size_mb": round(p.stat().st_size / 1e6, 1)}
        ok_play = decodes(p) and v is not None and au is not None
        row["C1_plays"] = ok_play
        row["C1_window"] = lo <= dur <= hi
        row["duration_without_outro"] = round(dur - 1.8, 2)
        row["C1_window_without_outro"] = lo <= dur - 1.8 <= hi
        row["C1"] = bool(ok_play and row["C1_window"])
        row["dims"] = f"{v['width']}x{v['height']}" if v else None
        row["C3_vertical"] = bool(v and int(v["height"]) > int(v["width"]) and abs(int(v["width"]) / int(v["height"]) - 9 / 16) < 0.02)
        # our own transcript of the clip audio
        words, hyp = [], []
        if au is not None:
            segs, _ = model.transcribe(str(p), language="en", word_timestamps=True, vad_filter=False)
            for s in segs:
                for w in (s.words or []):
                    words.append((w.start, w.end, w.word)); hyp.append(w.word)
        row["words_heard"] = len(words)
        row["transcript"] = " ".join(w[2].strip() for w in words)[:400]
        m = meta.get(p.name)
        if m:
            s0, s1 = float(m["start"]), float(m["end"])
            row["src_start"], row["src_end"] = s0, s1
            # C2: the cut must not fall inside one of our commentary sentences (0.15 s tolerance)
            def inside(t):
                return any(x["t"] + 0.15 < t < x["t"] + x["dur"] - 0.15 for x in sents)
            row["C2_start_clean"] = not inside(s0)
            row["C2_end_clean"] = not inside(s1)
            row["C2"] = row["C2_start_clean"] and row["C2_end_clean"]
            # truth text for the clip window: sentences fully inside
            ref = []
            for x in sents:
                if x["t"] >= s0 - 0.2 and x["t"] + x["dur"] <= s1 + 0.2:
                    ref += norm(x["text"])
            row["ref_words"] = len(ref)
            row["C4_wer_vs_truth"] = None if not ref else round(wer(ref, norm(" ".join(hyp))), 3)
            row["C4"] = None if not ref else row["C4_wer_vs_truth"] <= 0.15
        else:
            row["C2"] = None; row["C4"] = None
        rows.append(row)
    # C5 overlaps
    for i, r in enumerate(rows):
        r["C5"] = None
        if "src_start" not in r: continue
        worst = 0.0
        for j, q in enumerate(rows):
            if i == j or "src_start" not in q: continue
            worst = max(worst, min(r["src_end"], q["src_end"]) - max(r["src_start"], q["src_start"]))
        r["max_overlap_s"] = round(max(worst, 0), 2)
        r["C5"] = worst <= 3.0
    n = len(rows)
    summary = {k: sum(1 for r in rows if r.get(k) is True) for k in ("C1", "C2", "C3_vertical", "C4", "C5")}
    summary["clips"] = n
    json.dump({"summary": summary, "rows": rows}, open(a.out, "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary))
    if a.sheet and rows:
        tdir = Path(a.sheet).parent / "_frames"; tdir.mkdir(exist_ok=True)
        k = 0
        for pos in (0.08, 0.5, 0.92):
            for p in clips:
                k += 1
                d = probe(p)[0]
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(d * pos), "-i", str(p), "-frames:v", "1",
                                "-vf", "scale=108:192:force_original_aspect_ratio=decrease,pad=108:192:(ow-iw)/2:(oh-ih)/2",
                                str(tdir / f"f{k:03d}.png")], check=False)
        cols = len(clips)
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", "1", "-i", str(tdir / "f%03d.png"),
                        "-vf", f"tile={cols}x3", "-frames:v", "1", a.sheet], check=False)
        for f in tdir.glob("*.png"): f.unlink()
        tdir.rmdir()

if __name__ == "__main__":
    main()

