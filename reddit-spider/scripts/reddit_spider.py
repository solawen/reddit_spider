import httpx
import time
import random
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from cookie_manager import load_cookies, bootstrap_from_chrome_info, save_cookies

CHROME_INFO_PATH = Path(__file__).parent.parent / "chrome_info.txt"

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "zh,en;q=0.9,zh-CN;q=0.8,ja;q=0.7,zh-TW;q=0.6",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "DNT": "1",
}


def build_headers(cookie: str | None) -> dict:
    headers = dict(BASE_HEADERS)
    if cookie:
        headers["Cookie"] = cookie
    return headers


def get_cookies() -> str | None:
    cookie = load_cookies()
    if cookie is None and CHROME_INFO_PATH.exists():
        cookie = bootstrap_from_chrome_info(CHROME_INFO_PATH)
        if cookie:
            save_cookies(cookie)
    return cookie


def format_posts(posts: list[dict], title: str) -> str:
    if not posts:
        return "📭 未找到相关内容"

    lines = [f"📌 {title}\n"]
    for i, child in enumerate(posts, 1):
        p = child["data"]
        post_title = p.get("title", "")
        url = "https://www.reddit.com" + p.get("permalink", "")
        score = p.get("score", 0)
        comments = p.get("num_comments", 0)
        author = p.get("author", "")
        selftext = p.get("selftext", "")

        if selftext and len(selftext) > 150:
            selftext = selftext[:150] + "…"

        line = (
            f"{i}. [{post_title}]({url})\n"
            f"   ⬆️ {score:,} · 💬 {comments:,} comments · u/{author}"
        )
        if selftext:
            line += f"\n   > {selftext}"
        lines.append(line)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"\n⏱ 抓取时间: {timestamp} · 共 {len(posts)} 条")
    return "\n\n".join(lines)


def fetch_subreddit(
    subreddit: str, sort: str, timeframe: str, limit: int, cookie: str | None
) -> list[dict] | str:
    """Fetch posts from a subreddit. Returns posts list or error string."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"t": timeframe, "limit": limit, "raw_json": "1"}
    headers = build_headers(cookie)

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=15, follow_redirects=True)
    except httpx.TimeoutException:
        return "⚠️ 请求超时，请检查网络连接"
    except httpx.RequestError:
        return "⚠️ 网络请求失败，请检查网络连接"

    if resp.status_code in (401, 403):
        return "⚠️ Cookie 已失效，请通过对话发送新的 cookie 字符串更新"
    if resp.status_code == 429:
        return "⚠️ 请求频率过高，请稍后再试"
    if resp.status_code != 200:
        return f"⚠️ 请求失败 (HTTP {resp.status_code})"

    data = resp.json()
    return data.get("data", {}).get("children", [])


def fetch_search(
    keyword: str, sort: str, timeframe: str, limit: int, cookie: str | None
) -> list[dict] | str:
    """Search Reddit by keyword. Returns posts list or error string."""
    url = "https://www.reddit.com/search.json"
    params = {"q": keyword, "sort": sort, "t": timeframe, "limit": limit, "raw_json": "1"}
    headers = build_headers(cookie)

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=15, follow_redirects=True)
    except httpx.TimeoutException:
        return "⚠️ 请求超时，请检查网络连接"
    except httpx.RequestError:
        return "⚠️ 网络请求失败，请检查网络连接"

    if resp.status_code in (401, 403):
        return "⚠️ Cookie 已失效，请通过对话发送新的 cookie 字符串更新"
    if resp.status_code == 429:
        return "⚠️ 请求频率过高，请稍后再试"
    if resp.status_code != 200:
        return f"⚠️ 请求失败 (HTTP {resp.status_code})"

    data = resp.json()
    return data.get("data", {}).get("children", [])


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Reddit Spider - Fetch Reddit posts")
    parser.add_argument("--subreddit", help="Subreddit name (without r/)")
    parser.add_argument("--search", help="Search keyword")
    parser.add_argument("--sort", default="hot", choices=["hot", "top", "new", "rising", "relevance"])
    parser.add_argument("--time", default="day", choices=["hour", "day", "week", "month", "year", "all"])
    parser.add_argument("--limit", type=int, default=20, help="Number of posts (1-100)")

    parsed = parser.parse_args(args)

    if not parsed.subreddit and not parsed.search:
        parser.error("One of --subreddit or --search is required")

    cookie = get_cookies()
    time.sleep(random.uniform(2.0, 4.0))

    if parsed.subreddit:
        result = fetch_subreddit(parsed.subreddit, parsed.sort, parsed.time, parsed.limit, cookie)
        title = f"r/{parsed.subreddit} · {parsed.sort.capitalize()} · {parsed.time}"
    else:
        result = fetch_search(parsed.search, parsed.sort, parsed.time, parsed.limit, cookie)
        title = f"Search: {parsed.search} · {parsed.sort.capitalize()} · {parsed.time}"

    if isinstance(result, str) and result.startswith("⚠️"):
        print(result)
    else:
        print(format_posts(result, title))


if __name__ == "__main__":
    main()
