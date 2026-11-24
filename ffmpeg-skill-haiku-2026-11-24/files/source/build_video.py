import json, sys, subprocess, asyncio, html
from pathlib import Path
from playwright.async_api import async_playwright
import imageio_ffmpeg
J=Path(sys.argv[1]); S=J/"source"; tr=json.load(open(S/"truth.json"))
items="".join(f'<div class="c" id="c{s["n"]}"><span>{s["n"]}</span><p>{html.escape(s["text"])}</p></div>' for s in tr["sentences"])
page=f'''<html><body style="margin:0;background:#f4efe3;font-family:Georgia,serif"><div style="padding:60px 120px 900px">
<h1 style="font-size:60px;color:#223">Day pack checklist</h1>{items}</div>
<style>.c{{display:flex;gap:30px;align-items:center;margin:40px 0;padding:30px;border-radius:20px;background:#fff;opacity:.35;font-size:46px;color:#222}}
.c span{{font-size:70px;color:#d9822b;min-width:90px}}.c p{{margin:0}}.c.on{{opacity:1;box-shadow:0 0 0 6px #d9822b}}</style></body></html>'''
(S/"page.html").write_text(page,encoding="utf-8")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":1920,"height":1080},record_video_dir=str(S/"_vid"),record_video_size={"width":1920,"height":1080})
        pg=await ctx.new_page(); await pg.goto((S/"page.html").as_uri()); await pg.wait_for_timeout(500)
        t0=await pg.evaluate("performance.now()")
        for s in tr["sentences"]:
            now=await pg.evaluate("performance.now()")-t0
            wait=s["start"]*1000-now
            if wait>0: await pg.wait_for_timeout(wait)
            await pg.evaluate(f"document.querySelectorAll('.c').forEach(e=>e.classList.remove('on'));const e=document.getElementById('c{s['n']}');e.classList.add('on');window.scrollTo({{top:e.offsetTop-300,behavior:'smooth'}})")
        await pg.wait_for_timeout(int((tr["total_s"]*1000)-(await pg.evaluate("performance.now()")-t0))+300)
        await ctx.close(); await b.close()
        open(S/"t0_offset.txt","w").write(str(t0))
asyncio.run(main())
