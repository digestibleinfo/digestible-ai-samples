"""Pass/fail test: ten small real jobs on ten public sites, driven only by agent-browser commands
(open, snapshot -i, find a @ref by role and name, click/fill/press, then a script checks the result).
No LLM involved: a script plays the agent, so the test measures the tool, not a model.
Usage: python site_tasks.py <out.json> [runs] [wait]"""
import json, re, sys, time
from common import ab as _ab

WAIT = len(sys.argv) > 3 and sys.argv[3] == "wait"  # third argument "wait": wait for the load event after every open

def ab(*a, **k):
    r = _ab(*a, **k)
    if WAIT and a[0] == "open":
        _ab("wait", "--load", "load")
    return r

def refs(snap, role, name_re):
    pat = re.compile(rf'^\s*- (?:{role}) "(?P<n>[^"]*)".*?\[(?:[^\]]*, )?ref=(?P<r>e\d+)\]', re.M)
    return [("@" + m["r"], m["n"]) for m in pat.finditer(snap) if re.search(name_re, m["n"], re.I)]

def need(snap, role, name_re):
    r = refs(snap, role, name_re)
    if not r: raise AssertionError(f"no {role} matching {name_re!r} in snapshot")
    return r[0][0]

def url(): return ab("get", "url")[0].strip()
def title(): return ab("get", "title")[0].strip()
def snap(): return ab("snapshot", "-i")[0]

def t_example():
    ab("open", "https://example.com"); ab("click", need(snap(), "link", "learn more")); ab("wait", "1500")
    assert "iana.org" in url(), url()
def t_hn():
    ab("open", "https://news.ycombinator.com"); s = snap()
    ab("click", need(s, "link", r"\d+\s*comments?|discuss")); ab("wait", "1500")
    assert "item?id=" in url(), url()
def t_wiki():
    ab("open", "https://en.wikipedia.org/wiki/Web_browser"); ab("fill", need(snap(), "searchbox", "search"), "Chromium")
    ab("press", "Enter"); ab("wait", "2000"); assert "Chromium" in title(), title()
def t_books():
    ab("open", "https://books.toscrape.com"); ab("click", need(snap(), "link", "A Light in the Attic")); ab("wait", "1500")
    assert "A Light in the Attic" in title(), title()
def t_quotes():
    ab("open", "https://quotes.toscrape.com/js/"); ab("wait", "2000")
    n = ab("eval", "document.querySelectorAll('.quote').length")[0].strip()
    s = ab("snapshot")[0]
    assert n == "10" and "Albert Einstein" in s, (n, "Einstein" in s)
def t_httpbin():
    ab("open", "https://httpbin.org/forms/post"); s = snap()
    ab("fill", need(s, "textbox", "Customer name"), "Ada Lovelace"); ab("click", need(s, "radio", "Large"))
    ab("click", need(s, "checkbox", "Bacon")); ab("click", need(s, "button", "Submit order")); ab("wait", "2000")
    body = ab("get", "text", "body")[0]
    assert "Ada Lovelace" in body and "large" in body.lower() and "bacon" in body.lower(), body[:200]
def t_python():
    ab("open", "https://www.python.org"); s = snap()
    ab("fill", need(s, "searchbox|textbox", "search"), "asyncio") if refs(s, "searchbox", "search") or refs(s, "textbox", "search") else (_ for _ in ()).throw(AssertionError("no search box"))
    ab("press", "Enter"); ab("wait", "2500"); assert "asyncio" in url() or "search" in url(), url()
def t_github():
    ab("open", "https://github.com/vercel-labs/agent-browser"); ab("wait", "1500")
    t = title(); assert "agent-browser" in t, t
    s = snap(); need(s, "link", r"^Issues")
def t_react():
    ab("open", "https://react.dev"); ab("click", need(snap(), "link", r"^Learn$")); ab("wait", "2000")
    assert "/learn" in url(), url()
def t_bbc():
    ab("open", "https://www.bbc.com/news"); s = snap()
    links = [r for r in refs(s, "link", r".{25,}")]
    assert links, "no headline-sized link"
    ab("click", links[0][0]); ab("wait", "2500"); assert "bbc." in url() and url().rstrip("/") != "https://www.bbc.com/news", url()

TASKS = [("example: follow Learn more", t_example), ("hackernews: open first comments page", t_hn),
         ("wikipedia: search Chromium", t_wiki), ("books.toscrape: open a book", t_books),
         ("quotes (JavaScript-rendered): 10 quotes appear", t_quotes), ("httpbin: fill and submit a form", t_httpbin),
         ("python.org: search asyncio", t_python), ("github: repo page reads", t_github),
         ("react.dev: open Learn", t_react), ("bbc news: open a headline", t_bbc)]

if __name__ == "__main__":
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    res = []
    for name, fn in TASKS:
        row = {"task": name, "runs": []}
        for i in range(runs):
            t0 = time.time()
            try: fn(); ok, why = True, ""
            except Exception as e: ok, why = False, str(e)[:160]
            row["runs"].append({"pass": ok, "seconds": round(time.time() - t0, 1), "why": why})
            ab("close")
        row["passed"] = sum(r["pass"] for r in row["runs"])
        print(name, row["passed"], "/", runs, [r["why"] for r in row["runs"] if r["why"]][:1], flush=True)
        res.append(row)
    json.dump(res, open(sys.argv[1], "w"), indent=1)
