import json, glob, os
R = os.environ.get("CHEAP_RESULTS", "results").rstrip("/") + "/"
names = {"1": "easy: CLI flag", "2": "medium: CSV export, 3 files", "3": "hard: planted cache bugs"}
rows = []
for t in "123":
    for m in ("plain", "plugin"):
        r = json.load(open(R + f"run_t{t}-{m}.json"))
        pt = r["planner_input_miss"] + r["planner_cache_read"] + r["planner_output"]
        it = r["impl_input_miss"] + r["impl_cache_read"] + r["impl_output"]
        rows.append(dict(task=t, name=names[t], mode=m, planner_tokens=pt, implementer_tokens=it, planner_usd=r["planner_usd"], implementer_usd=r["impl_usd"],
            total_usd=r["total_usd"], tests_passed=r["tests_passed"], tests_failed=r["tests_failed"], wall_s=r["wall_s"], worker_jobs=r["worker_jobs"]))
tot = {}
for m in ("plain", "plugin"):
    s = [x for x in rows if x["mode"] == m]
    tot[m] = dict(planner_tokens=sum(x["planner_tokens"] for x in s), implementer_tokens=sum(x["implementer_tokens"] for x in s),
        total_usd=round(sum(x["total_usd"] for x in s), 4), tests_passed=sum(x["tests_passed"] for x in s), tests_failed=sum(x["tests_failed"] for x in s), wall_s=sum(x["wall_s"] for x in s))
json.dump(dict(prices="deepseek-flash peak USD/1M tokens: cache hit 0.006, miss 0.30, output 1.20 (2026-11-03 pricing page)", rows=rows, totals=tot), open(R + "results.json", "w"), indent=1)
print(f"{'task':<5}{'run':<8}{'planner tok':>12}{'impl tok':>10}{'cost $':>9}{'tests':>7}{'wall':>7}")
for x in rows:
    print(f"{x['task']:<5}{('alone','plugin')[x['mode']=='plugin']:<8}{x['planner_tokens']:>12,}{x['implementer_tokens']:>10,}{x['total_usd']:>9.4f}{x['tests_passed']:>3}/{x['tests_passed']+x['tests_failed']:<3}{x['wall_s']:>6}s")
for m in ("plain", "plugin"):
    t = tot[m]; print(f"ALL  {('alone','plugin')[m=='plugin']:<8}{t['planner_tokens']:>12,}{t['implementer_tokens']:>10,}{t['total_usd']:>9.4f}{t['tests_passed']:>3}/{t['tests_passed']+t['tests_failed']:<3}{t['wall_s']:>6}s")
