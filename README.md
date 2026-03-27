# Reddit Spider

A Python CLI tool for scraping Reddit content via the JSON API. Supports browsing subreddits and keyword search with formatted Markdown output.

## Features

- **Subreddit browsing** — fetch posts from any subreddit with sorting (hot, top, new, rising)
- **Keyword search** — search all of Reddit by keyword
- **Time filtering** — filter by hour, day, week, month, year, or all time
- **Cookie authentication** — persistent cookie management for authenticated access
- **Rate limiting** — built-in delays to be respectful to Reddit's servers
- **Formatted output** — clean Markdown output with post titles, scores, comments, and snippets

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd reddit-spider/reddit-spider

# Install dependencies
pip install -r scripts/requirements.txt
```

## Usage

### Browse a Subreddit

```bash
python scripts/reddit_spider.py --subreddit Economics --sort top --time day --limit 20
```

### Search Reddit

```bash
python scripts/reddit_spider.py --search "Federal Reserve" --sort relevance --time week --limit 10
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--subreddit` | Subreddit name (without r/) | - |
| `--search` | Search keyword | - |
| `--sort` | Sort order: hot, top, new, rising, relevance | hot |
| `--time` | Timeframe: hour, day, week, month, year, all | day |
| `--limit` | Number of posts (1-100) | 20 |

## Cookie Management

Reddit Spider uses cookie-based authentication. To update your cookies:

```bash
python scripts/cookie_manager.py --update "your_cookie_string_here"
```

Cookies are stored at `~/.openclaw/reddit-spider/cookies.json`.

## Testing

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run tests
pytest tests/
```

## Project Structure

```
reddit-spider/
├── scripts/
│   ├── reddit_spider.py    # Main scraper
│   ├── cookie_manager.py   # Cookie management
│   └── requirements.txt    # Dependencies
└── tests/
    ├── test_reddit_spider.py
    ├── test_cookie_manager.py
    ├── test_integration.py
    └── requirements.txt
```

## Requirements

- Python 3.12+
- httpx >= 0.27.0

## License

MIT
