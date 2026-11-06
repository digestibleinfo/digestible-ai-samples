# agent-browser: sample pack

Used in the Digestible AI videos about [agent-browser](https://github.com/vercel-labs/agent-browser) (Vercel Labs, Apache-2.0): a native Rust command-line tool that gives an AI agent a browser.

**Download:** [agent-browser-samples.zip](https://github.com/digestibleinfo/digestible-ai-samples/raw/main/agent-browser/agent-browser-samples.zip). Save it into the folder you made in the video and unpack it with `tar -xf agent-browser-samples.zip` in Command Prompt. The same files are in [files](files).

## What was tested (no LLM, no API key, no tokens bought)
1. `snapshot_tokens.py`: opens 10 public pages and counts the tokens of one page snapshot from agent-browser (`snapshot`, `snapshot -i`) and from Playwright MCP (`browser_navigate` + `browser_snapshot`). Both drove the same Chrome for Testing 157. Tokens are counted with tiktoken `o200k_base`, an OpenAI tokenizer, so other models count somewhat differently; the ratios matter more than the absolute numbers.
2. `site_tasks.py`: ten small real jobs on ten public sites (click a link, search, fill and submit a form, read a JavaScript-rendered page), played by a script that reads `snapshot -i`, finds an `@ref` by role and name, acts, then checks the result. Three runs each, 30 runs. With the third argument `wait` it adds `agent-browser wait --load load` after every `open`.

Results are in [files/results](files/results): `tokens.json`, `tasks.json` (no wait), `tasks_wait.json` (wait), and `results.md`.

## Headline numbers
- Tokens over the 10 pages: Playwright MCP 107,417; agent-browser full snapshot 60,287 (1.8x smaller); agent-browser interactive-only snapshot 30,357 (3.5x smaller).
- Jobs, no wait: 28 of 30 passed. Both misses were a snapshot taken before the page had finished loading. With `wait --load load`: 30 of 30.

## Setup used
Windows 11 Pro, AMD Ryzen 7 2700, 72 GB RAM (no GPU used). agent-browser 0.41.2 on Node 24.22.1, Chrome for Testing 157.0.8103.38. Playwright MCP `@playwright/mcp@0.0.84` run headless with `--executable-path` set to the same Chrome.

Installing `npm install -g agent-browser` on Node 22 installed version 0.27.0, not 0.41.2: 0.41.2 declares `engines: node >=24`, and npm quietly picked the newest version that allows your Node.

## Rerun it
```
npm install -g agent-browser
agent-browser install
npm install @playwright/mcp@0.0.84
python -m pip install tiktoken
set AB_MCP=npx playwright-mcp
cd scripts
python snapshot_tokens.py tokens.json
python site_tasks.py tasks.json 3
python site_tasks.py tasks_wait.json 3 wait
```
(`AB_BIN` and `AB_CHROME` override the agent-browser command and the Chrome path; see `scripts/common.py`.)

## Caveats
- Playwright MCP 0.0.84 puts the snapshot in a separate `browser_snapshot` call, so one page costs two tool responses; the totals include both. Other versions or settings differ.
- The interactive-only snapshot leaves out page text, so it is the cheap way to act, not to read. The full snapshot is the fair comparison for reading.
- Live websites change. The GitHub and BBC counts will not repeat exactly.
- Three runs per job is a small sample.
- No language model drove these runs; a script played the agent. How well a model uses the refs is not measured here.
