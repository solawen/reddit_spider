---
name: reddit-spider
description: >
  Fetch and summarize Reddit posts by subreddit, sort order, and time range, or
  search Reddit by keyword. Use this skill when the user asks to fetch, scrape,
  browse, or summarize Reddit content. Examples: "give me today's top posts
  from r/Economics", "show me r/popular hot posts", "search Reddit for Federal
  Reserve news this week", "what's trending on r/wallstreetbets", "抓取 r/Bitcoin
  本周热帖", "搜索关于美联储的最新帖子", "更新 Reddit cookies". Default subreddits:
  r/popular (general), r/Economics and r/MacroEconomics (macro), r/investing and
  r/stocks (markets), r/wallstreetbets and r/options (hot finance),
  r/CryptoCurrency and r/Bitcoin (crypto).
version: 1.0.0
metadata:
  openclaw:
    emoji: "🦀"
    requires:
      bins:
        - python3
---

# Reddit Spider

## Overview

This skill fetches Reddit posts via the authenticated JSON API and returns a
formatted Markdown summary. Two operations are supported: subreddit fetch and
keyword search. Cookies are stored locally and can be updated via conversation.

## Intent Detection

Identify the user's intent from their message:

- **Cookie update**: message contains "更新 Reddit cookies" or "update Reddit
  cookies" or "cookie" followed by a long string. Run cookie_manager.py.
- **Keyword search**: message mentions searching for a topic or keyword without
  specifying a subreddit. Use `--search`.
- **Subreddit fetch** (default): message mentions a subreddit name, or asks for
  popular/trending/top posts. Use `--subreddit`.

## Parameter Extraction

Extract these parameters from the user's message:

| Parameter | Default | Choices |
|-----------|---------|---------|
| `--subreddit` | (from message) | any subreddit name, without "r/" prefix |
| `--sort` | `hot` | `hot`, `top`, `new`, `rising` |
| `--time` | `day` | `hour`, `day`, `week`, `month`, `year`, `all` |
| `--limit` | `20` | 1–100 |
| `--search` | (from message) | any keyword string |

Time range mapping:
- "今天" / "today" / "日" → `day`
- "本周" / "this week" / "周" → `week`
- "本月" / "this month" / "月" → `month`
- "今年" / "this year" → `year`
- "最新" / "latest" / "new" without time context → use `--sort new --time day`

## Execution

Run the appropriate command from the skill's directory:

```bash
# Subreddit fetch
python3 scripts/reddit_spider.py --subreddit <name> --sort <sort> --time <timeframe> --limit <n>

# Keyword search
python3 scripts/reddit_spider.py --search "<keyword>" --sort <sort> --time <timeframe> --limit <n>

# Cookie update
python3 scripts/cookie_manager.py --update "<cookie_string>"
```

Return the command's stdout as your reply verbatim.

## Error Handling

- If the output starts with `⚠️`, relay it to the user as-is without modification.
- If the output starts with `✅`, relay it as-is.
- If the command exits non-zero and produces no output, reply: "⚠️ reddit-spider 运行失败，请检查 Python 环境和依赖（pip install httpx）"

## First-Run Note

On first use, if no cookies have been configured, the skill will attempt to
bootstrap from a `chrome_info.txt` file in the skill's root directory. If that
file is absent, most content will still be accessible anonymously, but some
subreddits may be restricted.
