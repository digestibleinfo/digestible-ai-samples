"""Records HyperFlow H3 Flash text-to-video clips in the real ComfyUI UI under an 8 GB VRAM / 32 GB RAM cap.
Reuses tutorials/comfyui/ui_recorder.py (Playwright screen recording, VRAM/RAM sampler).

    python record_h3.py <clip number> [--lowres]   # starts ComfyUI itself via lowvram_launch.py, stops it after
"""
import asyncio, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(r"<repo>")
sys.path.insert(0, str(ROOT / "tutorials" / "comfyui"))
import ui_recorder as u  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

PORTABLE = Path(r"<work>\ComfyUI_windows_portable")
JOB = ROOT / "trial" / "jobs" / "hyperflow-h3-flash-8gb-2026-11-14"
REC = Path(r"<work>\records")
API = PORTABLE / "ComfyUI" / "custom_nodes" / "ComfyUI-HyperFlow-Flash" / "example_workflows" / "api" / "hyperflow_t2v_api.json"
UNET = "minimax_h3_fl2va_hyperflow_flash_14b-Q3_K_M.gguf"
SEED = 42
PROMPTS = {
    1: "A cheetah sprinting across golden grassland at sunset, the camera tracking alongside, dust kicked up behind its paws.",
    2: "A woman in a red coat walks down a rainy city street at night, neon signs reflected in the puddles, the camera follows from behind and then turns to show her face.",
    3: "A golden retriever runs into a lake and shakes the water off its fur, slow motion, droplets catching the sunlight.",
    4: "A close-up of a coffee shop chalkboard sign that reads OPEN 24 HOURS, steam drifting past, the camera slowly pushing in.",
    5: "A birthday cake with five lit candles on a kitchen table, a child leans in and blows them out, smoke curls upward.",
}
LAYOUT = {"1": (40, 60, 380, 80), "2": (40, 190, 380, 120), "3": (40, 360, 380, 80), "4": (40, 490, 380, 80),
          "5": (470, 60, 430, 400), "6": (950, 60, 320, 100), "7": (950, 200, 320, 80), "8": (950, 320, 320, 100),
          "9": (950, 460, 320, 80), "10": (950, 580, 320, 100), "11": (1320, 60, 300, 80), "12": (1320, 180, 300, 80),
          "13": (1320, 300, 300, 100), "14": (1320, 440, 600, 520)}


_wd = u.wait_done
async def _long(c, run=0, limit=3600):
    return await _wd(c, run, limit)
u.wait_done = _long


_setup = u.setup
async def _setup2(page, clean=True):
    await page.goto(u.URL, wait_until="networkidle")
    await page.wait_for_function("() => window.app && window.app.api && window.app.graph", timeout=120000)
    await _setup(page, clean)
    for _ in range(3):
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(400)
u.setup = _setup2


_cr = u.click_run
async def _click2(c):
    await c.page.keyboard.press("Escape")
    await c.page.wait_for_timeout(500)
    await _cr(c)
u.click_run = _click2


def make(n, width, height, length):
    def graph(prompt):
        g = json.loads(API.read_text())
        g["1"]["inputs"]["unet_name"] = UNET
        g["5"]["inputs"].update(prompt=prompt, width=width, height=height, length=length)
        g["8"]["inputs"]["noise_seed"] = SEED
        g["14"]["inputs"]["filename_prefix"] = f"hyperflow/h3_8gb_clip{n}"
        return g
    return graph


def gpu_used():
    return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True).stdout.split()[0])


def wait_up(limit=180):
    t = time.time()
    while time.time() - t < limit:
        try:
            urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2); return
        except OSError:
            time.sleep(1)
    raise TimeoutError("ComfyUI did not start")


async def main(n, width, height, length, flags, tag):
    REC.mkdir(parents=True, exist_ok=True)
    pidf = PORTABLE.parent / "comfy.pid"
    env = os.environ | {"COMFY_PORTABLE": str(PORTABLE), "COMFY_LOG_FILE": str(REC / f"server_clip{n}{tag}.log"),
                        "VRAM_BASELINE_MIB": str(gpu_used()), "COMFY_PID_FILE": str(pidf), "HUD_VRAM_GB": "8", "HUD_RAM_GB": "32",
                        "COMFY_VRAM_RESERVE_MARGIN_GB": "0.5"}
    os.environ.update(env)
    launcher = subprocess.Popen([r"<repo>\tutorials\venv\Scripts\python.exe",
                                 str(ROOT / "tutorials/comfyui/lowvram_launch.py"), "8", "32", *flags],
                                env=env, stdout=open(REC / f"launcher_clip{n}{tag}.log", "w"), stderr=subprocess.STDOUT)
    try:
        wait_up()
        u.P = {"out": REC, "graph": make(n, width, height, length), "name": f"HyperFlow H3 Flash clip {n}", "prompt_node": "5",
               "prompt_widget": "prompt", "layout": LAYOUT, "tour": [], "prompts": []}
        variant = [("Q3_K_M", "1", {"1": {"unet_name": UNET}})]
        async with async_playwright() as pw:
            info = await u.record_clip(pw, f"h3-clip{n}{tag}", u.clip_variants, PROMPTS[n], variant)
        (REC / f"ui_clip{n}{tag}.json").write_text(json.dumps(info))
        m = info["marks"]; s = [x for x in info["vram_mib"] if m["run0"] <= x[0] <= m["done0"]]
        print("RESULT", {"seconds": round(m["done0"] - m["run0"] - 1.5, 1), "peak_vram_gb": round(max(x[1] for x in s) / 1024, 2),
                         "peak_ram_gb": round(max(x[2] for x in s) / 1024, 2), "marks": m})
    finally:
        try:
            import psutil
            p = psutil.Process(int(pidf.read_text())); p.terminate(); p.wait(30)
        except Exception as e:
            print("stop:", e)
        launcher.wait(timeout=60)


if __name__ == "__main__":
    n = int(sys.argv[1]); a = sys.argv[2:]
    kv = dict(x.split("=") for x in a if "=" in x)
    flags = [f for f in a if f.startswith("--")]
    asyncio.run(main(n, int(kv.get("w", 1344)), int(kv.get("h", 768)), int(kv.get("len", 124)), flags, kv.get("tag", "")))
