"""No-Claude check: reads the saved run logs and prints the evidence."""
import glob, json, re, sys
import os
R = os.environ.get("CHEAP_RESULTS", "results").rstrip("/") + "/"
print("run          model ids seen          Anthropic conns   DeepSeek conns   'claude' in logs")
tot_bad = 0
for f in sorted(glob.glob(R + "run_t*.json")):
    r = json.load(open(f)); tag = f.split("run_")[1][:-5]
    txt = open(R + f"stream_{tag}.jsonl", encoding="utf-8").read().lower()
    n = len(re.findall(r"claude-(?:opus|sonnet|haiku)|\"model\":\"claude|opus-|sonnet-", txt))
    tot_bad += len(r["anthropic_connections"]) + n
    print(f"{tag:<12} {','.join(m for m in r['models_seen'] if m != '<synthetic>'):<22} {len(r['anthropic_connections']):^15} {(r.get('deepseek_connection_ips') or 0):^16} {n:^8}")
print("TOTAL Claude signs:", tot_bad)
