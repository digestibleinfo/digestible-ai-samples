"""Lays the commentary sentences (voice/s<N>.wav) on a silent track at their offsets, muxes with the recording,
writes source/truth.json (duration, sentence timings)."""
import json, subprocess
from pathlib import Path
import numpy as np, soundfile as sf

root = Path(r"WORKDIR")
off = json.loads((root / "commentary" / "offsets.json").read_text(encoding="utf-8"))
dur = json.loads((root / "commentary" / "voice" / "durations.json").read_text(encoding="utf-8"))
video = root / "source" / "gameplay_raw.mp4"
total = float(subprocess.run([r"ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout)
x0, sr = sf.read(root / "commentary" / "voice" / "s1.wav", dtype="float32")
track = np.zeros(int((total + 2) * sr), dtype=np.float32)
sents = []
for o, d in zip(off, dur):
    x, r = sf.read(root / "commentary" / "voice" / d["file"], dtype="float32")
    assert r == sr
    a = int(o["t"] * sr)
    track[a:a + len(x)] += x[: len(track) - a]
    sents.append({"i": o["i"], "t": o["t"], "dur": round(len(x) / sr, 2), "text": o["text"]})
sf.write(root / "source" / "commentary_track.wav", track, sr, subtype="PCM_16")
subprocess.run([r"ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i",
                str(root / "source" / "commentary_track.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "96k", "-t", str(total), "-movflags", "+faststart",
                str(root / "source" / "source.mp4")], check=True)
speech = sum(s["dur"] for s in sents)
truth = {"duration": round(total, 2), "sentences": sents, "speech_seconds": round(speech, 1),
         "speech_share": round(speech / total, 4), "window": [30, 90]}
(root / "source" / "truth.json").write_text(json.dumps(truth, indent=1), encoding="utf-8")
print("duration", total, "sentences", len(sents), "speech s", round(speech, 1), "share", round(speech / total * 100, 2), "%")
