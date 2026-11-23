"""Plays the two saved pages on screen (headless Chrome page video, 1080x1000) and logs the pass checks.

    python play_pages.py flappy|hexagon

flappy: waits, then presses Space repeatedly (a 'playing' bot keeps the bird up for a while), samples the page
canvas to see pipes move; finally stops pressing so the bird falls to Game Over. Frame differences of canvas crops
decide C3/C7/C8; the visible text is read from the page. Writes <name>_play.mp4 and play.json next to the html.
"""
import json, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

RUN = Path("results")  # run from the folder that holds results/
FFMPEG = "ffmpeg"  # any ffmpeg on PATH
name = sys.argv[1]
d = RUN / name
vid = d / "_vid"
shutil.rmtree(vid, ignore_errors=True)
errs, log = [], {}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": 1080, "height": 1000}, record_video_dir=str(vid),
                        record_video_size={"width": 1080, "height": 1000})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errs.append(str(e)[:200]))
    page.on("console", lambda m: errs.append("console.error: " + m.text[:200]) if m.type == "error" else None)
    page.goto((d / f"{name}.html").as_uri())
    time.sleep(2)
    body_text = lambda: page.evaluate("document.body.innerText")[:300]
    shot = lambda: page.screenshot(type="png", clip={"x": 0, "y": 0, "width": 1080, "height": 1000})
    import hashlib
    h = lambda b_: hashlib.md5(b_).hexdigest()
    if name == "flappy":
        log["text_start"] = body_text()
        page.keyboard.press("Space")  # start / flap
        hs = []
        for i in range(60):  # about 30 s: flap at a steady rhythm
            page.keyboard.press("Space")
            time.sleep(0.45)
            hs.append(h(shot())) if i % 4 == 0 else None
            log.setdefault("texts", []).append(body_text().replace("\n", " | ")) if i % 6 == 0 else None
        log["frames_changing"] = len(set(hs))
        time.sleep(14)  # stop flapping: the bird falls
        log["text_end"] = body_text().replace("\n", " | ")
        time.sleep(3)
    else:
        hs = []
        for i in range(22):
            time.sleep(0.5)
            hs.append(h(shot()))
        log["frames_changing"] = len(set(hs))
        log["text"] = body_text().replace("\n", " | ")
        time.sleep(6)
    path = page.video.path()
    ctx.close()
    b.close()
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(path), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-pix_fmt", "yuv420p", str(d / f"{name}_play.mp4")], check=True)
shutil.rmtree(vid, ignore_errors=True)
log["errors"] = errs
(d / "play.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
print(json.dumps(log)[:800])

