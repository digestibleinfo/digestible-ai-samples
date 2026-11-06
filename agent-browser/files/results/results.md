# Results

## Tokens per page (tiktoken o200k_base)

| site | agent-browser full | agent-browser -i | Playwright MCP | MCP / -i |
|---|---|---|---|---|
| example | 267 | 11 | 394 | 35.8x |
| hackernews | 7,166 | 5,130 | 13,535 | 2.6x |
| wikipedia | 19,325 | 6,934 | 37,833 | 5.5x |
| github-repo | 8,979 | 5,738 | 12,627 | 2.2x |
| books-toscrape | 5,408 | 1,962 | 8,793 | 4.5x |
| quotes-js | 689 | 81 | 1,152 | 14.2x |
| react-dev | 4,077 | 1,059 | 10,720 | 10.1x |
| python-org | 4,299 | 2,148 | 8,199 | 3.8x |
| httpbin-form | 423 | 211 | 645 | 3.1x |
| bbc-news | 9,654 | 7,083 | 13,519 | 1.9x |
| **total** | 60,287 | 30,357 | 107,417 | 3.5x |

## Ten jobs x 3 runs, no wait

| task | passed of 3 | typical seconds | failure |
|---|---|---|---|
| example: follow Learn more | 3 | 3.2 |  |
| hackernews: open first comments page | 3 | 4.5 |  |
| wikipedia: search Chromium | 3 | 6.8 |  |
| books.toscrape: open a book | 3 | 5.2 |  |
| quotes (JavaScript-rendered): 10 quotes appear | 3 | 5.9 |  |
| httpbin: fill and submit a form | 2 | 4.6 | no textbox matching 'Customer name' in snapshot |
| python.org: search asyncio | 3 | 5.4 |  |
| github: repo page reads | 3 | 4.7 |  |
| react.dev: open Learn | 3 | 4.6 |  |
| bbc news: open a headline | 2 | 7.7 | https://www.bbc.com/news |
| **total** | 28 of 30 | | |

## Same jobs, `wait --load load` after every open

| task | passed of 3 | typical seconds | failure |
|---|---|---|---|
| example: follow Learn more | 3 | 3.3 |  |
| hackernews: open first comments page | 3 | 4.5 |  |
| wikipedia: search Chromium | 3 | 5.7 |  |
| books.toscrape: open a book | 3 | 5.0 |  |
| quotes (JavaScript-rendered): 10 quotes appear | 3 | 5.7 |  |
| httpbin: fill and submit a form | 3 | 4.5 |  |
| python.org: search asyncio | 3 | 6.3 |  |
| github: repo page reads | 3 | 4.7 |  |
| react.dev: open Learn | 3 | 4.7 |  |
| bbc news: open a headline | 3 | 7.3 |  |
| **total** | 30 of 30 | | |
