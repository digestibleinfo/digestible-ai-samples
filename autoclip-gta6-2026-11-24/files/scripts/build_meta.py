"""usage: build_meta.py <run_dir>  -> writes clips_meta.json {clip file: {start, end}} from the app's studio.json
(source offsets of each clip's scene) and run.json facts that the app wrote itself."""
import json, sys
from pathlib import Path

run = Path(sys.argv[1])
d = json.loads((run / "meta" / "studio.json").read_text(encoding="utf-8"))
drafts = {x["id"]: x for x in d["drafts"]}
meta = {}
for j in d["jobs"]:
    dr = drafts.get(j["draft_id"])
    if not dr or not dr.get("scenes"): continue
    sc = dr["scenes"]
    meta[j["job_id"] + ".mp4"] = {"start": min(s["start"] for s in sc), "end": max(s["end"] for s in sc),
                                  "title": j.get("title"), "app_duration": j.get("result", {}).get("duration"),
                                  "scenes": [[s["start"], s["end"]] for s in sc]}
(run / "clips_meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=True), encoding="utf-8")
a = d["analysis"]; g = d["generation"]
facts = {"clips_rendered": len(meta), "drafts": len(d["drafts"]), "llm_calls": g.get("llm_calls"),
         "degrade_reason": g.get("degrade_count") and d["plan"].get("degrade_reason"),
         "route": g.get("route"), "provider": g.get("screening_identity", {}).get("provider"),
         "source_duration": d["plan"].get("source_duration"), "diagnostics": d["plan"].get("diagnostics")}
print(json.dumps(facts, ensure_ascii=True))
