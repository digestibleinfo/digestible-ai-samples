import json, csv, collections
from pathlib import Path
from datetime import datetime

R = Path(r"WORKDIR\results")
truth = json.loads(Path(r"WORKDIR\source\truth.json").read_text(encoding="utf-8"))
SRC_SHA = "3D5DA78D0E9D3FE2EF378EC0422F9B27825CDD24CC988334C7A45940D29FF96D"
cfg = {
    "run1": dict(start="2026-11-24T22:28:13", end="2026-11-24T22:46:23", llm="Ollama qwen2.5vl:7b (local, 6.0 GB, 16384 context)", cost_usd=0.0),
    "run2": dict(start="2026-11-24T23:00:55", end="2026-11-24T23:18:51", llm="DeepSeek deepseek-flash (cloud, native provider)", cost_usd=None),
}
summary = {}
for run, c in cfg.items():
    d = R / run
    chk = json.loads((d / "check.json").read_text(encoding="utf-8"))
    cap = json.loads((d / "caption_check.json").read_text(encoding="utf-8"))
    capmap = {r["clip"]: r for r in cap["rows"]}
    rows = chk["rows"]
    use = [json.loads(l) for l in (d / "meta" / "llm_usage.jsonl").read_text(encoding="utf-8").splitlines()]
    tok = collections.defaultdict(float)
    for u in use:
        for k in ("prompt_tokens", "completion_tokens"):
            if isinstance(u.get(k), (int, float)): tok[(u["kind"], k)] += u[k]
    stage = {u["stage"]: u["seconds"] for u in use if u.get("kind") == "timing"}
    est = any(u.get("estimated") for u in use)
    g = list(csv.DictReader(open(d / "gpu.csv")))
    peak_v = max(int(x["vram_mib"]) for x in g); base_v = int(g[0]["vram_mib"])
    peak_app = max(int(x["app_rss_mb"]) for x in g); peak_ol = max(int(x["ollama_rss_mb"]) for x in g)
    min_free = min(int(x["sys_free_ram_mb"]) for x in g)
    secs = (datetime.fromisoformat(c["end"]) - datetime.fromisoformat(c["start"])).total_seconds()
    clean = 0
    for r in rows:
        cp = capmap.get(r["clip"], {})
        r["C4_caption_wer"] = cp.get("caption_wer"); r["C4_caption"] = cp.get("C4_caption")
        r["C1_strict"] = r["C1"]
        r["all_checks_strict"] = bool(r["C1"] and r["C2"] and r["C3_vertical"] and r["C4_caption"] and r["C5"])
        r["all_checks_ignoring_duration"] = bool(r["C1_plays"] and r["C2"] and r["C3_vertical"] and r["C4_caption"] and r["C5"])
    s = {
        "run": run, "app": "AutoClip Desktop 1.6.0", "llm": c["llm"], "asr": "Whisper base on this PC (CPU), 113 s",
        "start": c["start"], "end": c["end"], "wall_seconds": secs, "wall_minutes": round(secs / 60, 1),
        "source_sha256": SRC_SHA, "source_seconds": truth["duration"],
        "clips": len(rows),
        "tokens_text_prompt": tok[("text", "prompt_tokens")], "tokens_text_completion": tok[("text", "completion_tokens")],
        "tokens_vision_prompt": tok[("vision", "prompt_tokens")], "tokens_vision_completion": tok[("vision", "completion_tokens")],
        "tokens_estimated_by_app": est, "stage_seconds": stage,
        "cost_usd": c["cost_usd"], "peak_vram_mib": peak_v, "idle_vram_mib_at_start": base_v,
        "peak_app_ram_mb": peak_app, "peak_ollama_ram_mb": peak_ol, "min_free_system_ram_mb": min_free,
        "check": {
            "C1_plays": sum(r["C1_plays"] for r in rows),
            "C1_in_30_90_window_strict": sum(r["C1_window"] for r in rows),
            "C1_in_window_without_1.8s_outro": sum(r["C1_window_without_outro"] for r in rows),
            "C2_cut_not_inside_a_sentence": sum(bool(r["C2"]) for r in rows),
            "C3_vertical_9x16": sum(r["C3_vertical"] for r in rows),
            "C4_caption_wer_le_15pct_app_srt_vs_truth": sum(bool(r["C4_caption"]) for r in rows),
            "C4_audio_wer_le_15pct_our_whisper": sum(bool(r["C4"]) for r in rows),
            "C5_no_duplicates": sum(bool(r["C5"]) for r in rows),
            "all_checks_strict": sum(r["all_checks_strict"] for r in rows),
            "all_checks_ignoring_duration": sum(r["all_checks_ignoring_duration"] for r in rows),
        },
        "clip_lengths_s": sorted(round(r["duration"]) for r in rows),
    }
    summary[run] = s
    chk["rows"] = rows; chk["summary_final"] = s["check"]
    (d / "check.json").write_text(json.dumps(chk, indent=1), encoding="utf-8")
    (d / "run.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
(R / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
for k, v in summary.items():
    print(k, v["wall_minutes"], "min", "clips", v["clips"], v["check"], "VRAM", v["peak_vram_mib"], "appRAM", v["peak_app_ram_mb"], "olRAM", v["peak_ollama_ram_mb"], "tok", v["tokens_text_prompt"], v["tokens_text_completion"], v["tokens_vision_prompt"], v["tokens_vision_completion"])
