"""Shared helpers: run agent-browser and Playwright MCP the same way for every test.
Settings come from environment variables so the scripts run on any machine:
  AB_BIN      agent-browser command (default: agent-browser)
  AB_MCP      Playwright MCP command (default: npx -y @playwright/mcp@0.0.84)
  AB_CHROME   path to the Chrome for Testing that `agent-browser install` downloaded (auto-detected under ~/.agent-browser)
"""
import json, os, shlex, shutil, subprocess, time
from pathlib import Path

AB = shutil.which(os.environ.get("AB_BIN", "agent-browser")) or "agent-browser"  # which() finds the .cmd shim on Windows
MCP = shlex.split(os.environ.get("AB_MCP", "npx -y @playwright/mcp@0.0.84"))
MCP[0] = shutil.which(MCP[0]) or MCP[0]

def _chrome():
    if os.environ.get("AB_CHROME"): return os.environ["AB_CHROME"]
    root = Path(os.environ.get("USERPROFILE", Path.home())) / ".agent-browser" / "browsers"
    found = sorted(root.glob("chrome-*/chrome.exe")) or sorted(root.glob("chrome-*/chrome"))
    return str(found[-1])

SITES = [
    ("example", "https://example.com"),
    ("hackernews", "https://news.ycombinator.com"),
    ("wikipedia", "https://en.wikipedia.org/wiki/Web_browser"),
    ("github-repo", "https://github.com/vercel-labs/agent-browser"),
    ("books-toscrape", "https://books.toscrape.com"),
    ("quotes-js", "https://quotes.toscrape.com/js/"),
    ("react-dev", "https://react.dev"),
    ("python-org", "https://www.python.org"),
    ("httpbin-form", "https://httpbin.org/forms/post"),
    ("bbc-news", "https://www.bbc.com/news"),
]

def ab(*args, session="bench", timeout=90):
    t = time.time()
    p = subprocess.run([AB, "--session", session, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.stdout, p.stderr, p.returncode, time.time() - t

class Mcp:
    def __init__(self):
        self.p = subprocess.Popen([*MCP, "--headless", "--executable-path", _chrome()], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        self.n = 0
        self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "bench", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); self.p.stdin.flush()
    def rpc(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line: raise RuntimeError("mcp closed")
            m = json.loads(line)
            if m.get("id") == self.n: return m
    def call(self, tool, args):
        r = self.rpc("tools/call", {"name": tool, "arguments": args})
        res = r.get("result", {})
        return "\n".join(c.get("text", "") for c in res.get("content", [])), res.get("isError", False)
    def close(self):
        try: self.p.terminate()
        except Exception: pass
