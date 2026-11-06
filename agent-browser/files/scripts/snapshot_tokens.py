"""Zero-token test: how many tokens does one page snapshot cost, agent-browser vs Playwright MCP?
Token counts use tiktoken o200k_base (an OpenAI tokenizer, so a proxy: other models count a little differently).
Usage: python snapshot_tokens.py <out.json>"""
import json, sys, time
import tiktoken
from common import SITES, ab, Mcp

enc = tiktoken.get_encoding("o200k_base")
tok = lambda s: len(enc.encode(s, disallowed_special=()))
out = {"tokenizer": "tiktoken o200k_base", "sites": []}
mcp = Mcp()
for name, url in SITES:
    row = {"site": name, "url": url}
    o, e, rc, t = ab("open", url, timeout=120); row["ab_open_s"] = round(t, 2); row["ab_open_ok"] = rc == 0
    for key, flags in [("ab_full", []), ("ab_interactive", ["-i"]), ("ab_interactive_compact", ["-i", "-c"])]:
        o, e, rc, t = ab("snapshot", *flags)
        row[key] = {"tokens": tok(o), "chars": len(o), "refs": o.count("[ref="), "seconds": round(t, 2), "ok": rc == 0}
    t0 = time.time()
    try:
        nav, err = mcp.call("browser_navigate", {"url": url})
        snap, err2 = mcp.call("browser_snapshot", {})
        txt = nav + chr(10) + snap
        row["mcp"] = {"tokens": tok(txt), "navigate_tokens": tok(nav), "snapshot_tokens": tok(snap), "chars": len(txt),
                      "refs": txt.count("[ref="), "seconds": round(time.time() - t0, 2), "ok": not (err or err2)}
    except Exception as ex:
        row["mcp"] = {"ok": False, "error": str(ex)[:100]}
    print(name, row["ab_full"]["tokens"], row["ab_interactive"]["tokens"], row["mcp"].get("tokens"), flush=True)
    out["sites"].append(row)
ab("close")
mcp.close()
json.dump(out, open(sys.argv[1], "w"), indent=1)

print()
print(f"{'site':16}{'ab full':>9}{'ab -i':>8}{'MCP':>9}{'MCP / ab -i':>13}")
for r in out["sites"]:
    m = r["mcp"].get("tokens", 0)
    print(f"{r['site']:16}{r['ab_full']['tokens']:>9}{r['ab_interactive']['tokens']:>8}{m:>9}{m / max(1, r['ab_interactive']['tokens']):>12.1f}x")
tot = lambda k: sum(r[k]["tokens"] for r in out["sites"])
print(f"{'total':16}{tot('ab_full'):>9}{tot('ab_interactive'):>8}{tot('mcp'):>9}")
