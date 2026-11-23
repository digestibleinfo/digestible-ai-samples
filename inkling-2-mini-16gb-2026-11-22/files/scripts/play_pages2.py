"""Honest replay of a saved page (headless Chrome page video 1080x1000) with a probe on the canvas.

    python play_pages2.py <result-folder> <page> flappy_steady|flappy_smart|flappy_aim|hexagon

The probe wraps CanvasRenderingContext2D (translate, fillText) to log every drawn string and the bird's drawn y
(translate calls with x between 80 and 120) and shows a small HUD "bird y" outside the canvas, so a bird that leaves the
canvas (y < 0 or y > 600) is visible. flappy_steady: Space every 0.45 s for 30 s (same input for every page, as in
play_pages.py), then stops pressing. flappy_smart: presses Space only when the bird's y is below 360 (a sensible
player), 30 s. Writes <page>_<mode>.mp4 and play_<mode>.json in the result folder.
"""
import json, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

RUN = Path("work/results")  # folder with the saved runs
OUTD = Path("results")
FFMPEG = "ffmpeg"
folder, pagename, mode = sys.argv[1:4]
d = RUN / folder
vid = d / "_vid"
shutil.rmtree(vid, ignore_errors=True)
PROBE = """
(() => {
  window.__texts = []; window.__ys = []; window.__birdY = null;
  const P = CanvasRenderingContext2D.prototype;
  const ft = P.fillText; P.fillText = function (t, ...a) { const s = String(t);
    if (window.__texts[window.__texts.length - 1] !== s) window.__texts.push(s); return ft.call(this, t, ...a); };
  window.__rects = []; const fr = P.fillRect; P.fillRect = function (x, y, w, h) { window.__rects.push([x, y, w, h]); if (window.__rects.length > 120) window.__rects.shift(); return fr.call(this, x, y, w, h); };
  const tr = P.translate; P.translate = function (x, y) {
    if (x >= 80 && x <= 120) { window.__birdY = y; window.__ys.push(Math.round(y)); } return tr.call(this, x, y); };
  window.addEventListener('DOMContentLoaded', () => {
    const h = document.createElement('div');
    h.style.cssText = 'position:fixed;left:8px;top:8px;font:bold 22px monospace;color:#fff;background:#000a;padding:4px 8px;z-index:9';
    document.body.appendChild(h);
    setInterval(() => { const y = window.__birdY;
      h.textContent = 'bird y = ' + (y == null ? '-' : Math.round(y)) + '  (canvas 0..600)' + (y != null && (y < 0 || y > 600) ? '  OFF SCREEN' : ''); }, 50);
  });
})();
"""
log = {"mode": mode}
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": 1080, "height": 1000}, record_video_dir=str(vid),
                        record_video_size={"width": 1080, "height": 1000})
    ctx.add_init_script(PROBE if mode.startswith('flappy') else PROBE.replace("window.addEventListener('DOMContentLoaded'", "(()=>{})||window.addEventListener('DOMContentLoaded'"))
    page = ctx.new_page()
    page.on("pageerror", lambda e: errs.append(str(e)[:200]))
    page.on("console", lambda m: errs.append("console.error: " + m.text[:200]) if m.type == "error" else None)
    page.goto((d / f"{pagename}.html").as_uri())
    time.sleep(2)
    if mode.startswith("flappy"):
        page.keyboard.press("Space")
        t0 = time.time(); outs = []; offscreen_t = None
        while time.time() - t0 < 30:
            y = page.evaluate("window.__birdY")
            if y is not None and (y < 0 or y > 600) and offscreen_t is None:
                offscreen_t = round(time.time() - t0, 1)
            outs.append(y)
            if mode == "flappy_steady":
                page.keyboard.press("Space"); time.sleep(0.45)
            elif mode == 'flappy_aim':
                tgt = page.evaluate("(() => { const m=[]; for (const r of window.__rects.slice().reverse()) { const [x,y,w,h]=r; if (w>=55 && w<=80 && y>40 && y+h>=515 && y+h<=525) m.push(r); } if(!m.length) return 300; const a=m[0]; let pick=a; for (const r of m) { if (r[0] < a[0]-100) { pick=r; break; } } if (pick[0]+pick[2] < 75) pick=a; return pick[1]-78; })()")
                if y is None or y > tgt:
                    page.keyboard.press('Space')
                time.sleep(0.04)
            else:
                if y is None or y > 360:
                    page.keyboard.press("Space")
                time.sleep(0.08)
        log["first_offscreen_at_s"] = offscreen_t
        ys = [y for y in outs if y is not None]
        log["bird_y_min"], log["bird_y_max"] = round(min(ys)), round(max(ys))
        log["texts_seen_after_30s"] = page.evaluate("window.__texts.slice(-6)")
        if mode == "flappy_steady":
            time.sleep(10)  # stop pressing
        log["texts_end"] = page.evaluate("window.__texts.slice(-6)")
        log["bird_y_end"] = page.evaluate("window.__birdY")
        time.sleep(2)
    else:
        time.sleep(14)
        log["texts"] = page.evaluate("window.__texts.slice(-6)")
    path = page.video.path()
    ctx.close(); b.close()
out = d / f"{pagename}_{mode}.mp4"
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(path), "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-pix_fmt", "yuv420p", str(out)], check=True)
shutil.rmtree(vid, ignore_errors=True)
log["errors"] = errs
(d / f"play_{mode}.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
print(json.dumps(log)[:900])



