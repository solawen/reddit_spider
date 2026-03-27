import pytest
import httpx
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "reddit-spider" / "scripts"))
import reddit_spider
from reddit_spider import build_headers, format_posts, get_cookies


# ── helpers ────────────────────────────────────────────────────────────────

def make_child(
    title="Test Post",
    score=100,
    num_comments=10,
    author="user1",
    permalink="/r/test/comments/abc/test/",
    selftext="",
):
    return {
        "data": {
            "title": title,
            "score": score,
            "num_comments": num_comments,
            "author": author,
            "permalink": permalink,
            "selftext": selftext,
        }
    }


# ── build_headers ──────────────────────────────────────────────────────────

def test_build_headers_contains_chrome_user_agent():
    headers = build_headers(None)
    assert "Chrome/146" in headers["User-Agent"]


def test_build_headers_includes_sec_ch_ua():
    headers = build_headers(None)
    assert "sec-ch-ua" in headers


def test_build_headers_sets_cookie_when_provided():
    headers = build_headers("token=abc")
    assert headers["Cookie"] == "token=abc"


def test_build_headers_omits_cookie_key_when_none():
    headers = build_headers(None)
    assert "Cookie" not in headers


# ── get_cookies ────────────────────────────────────────────────────────────

def test_get_cookies_returns_stored_cookie(tmp_path):
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"), \
         patch.object(reddit_spider, "CHROME_INFO_PATH", tmp_path / "chrome_info.txt"):
        from cookie_manager import save_cookies
        save_cookies("stored=cookie")
        result = get_cookies()
    assert result == "stored=cookie"


def test_get_cookies_bootstraps_from_chrome_info_when_no_stored(tmp_path):
    chrome_info = tmp_path / "chrome_info.txt"
    chrome_info.write_text(":authority\nwww.reddit.com\ncookie\nbootstrap=abc\ndnt\n1\n")
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"), \
         patch.object(reddit_spider, "CHROME_INFO_PATH", chrome_info):
        result = get_cookies()
    assert result == "bootstrap=abc"


def test_get_cookies_returns_none_when_nothing_available(tmp_path):
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"), \
         patch.object(reddit_spider, "CHROME_INFO_PATH", tmp_path / "missing.txt"):
        result = get_cookies()
    assert result is None


# ── format_posts ───────────────────────────────────────────────────────────

def test_format_posts_contains_title_and_url():
    posts = [make_child(title="Hello World", permalink="/r/test/comments/abc/")]
    out = format_posts(posts, "r/test · Hot · day")
    assert "Hello World" in out
    assert "https://www.reddit.com/r/test/comments/abc/" in out


def test_format_posts_formats_score_with_commas():
    posts = [make_child(score=12345)]
    assert "12,345" in format_posts(posts, "r/test")


def test_format_posts_shows_comment_count():
    posts = [make_child(num_comments=99)]
    assert "99" in format_posts(posts, "r/test")


def test_format_posts_shows_author():
    posts = [make_child(author="john_doe")]
    assert "john_doe" in format_posts(posts, "r/test")


def test_format_posts_truncates_selftext_at_150():
    posts = [make_child(selftext="x" * 200)]
    out = format_posts(posts, "r/test")
    assert "…" in out
    assert "x" * 151 not in out


def test_format_posts_shows_selftext_when_short():
    posts = [make_child(selftext="Short body")]
    assert "Short body" in format_posts(posts, "r/test")


def test_format_posts_no_blockquote_for_link_posts():
    posts = [make_child(selftext="")]
    lines = format_posts(posts, "r/test").split("\n")
    assert not any(line.strip().startswith(">") for line in lines)


def test_format_posts_shows_post_count():
    posts = [make_child(), make_child()]
    assert "共 2 条" in format_posts(posts, "r/test")


def test_format_posts_empty_list():
    out = format_posts([], "r/test")
    assert "📭" in out


# ── fetch_subreddit ─────────────────────────────────────────────────────────

def test_fetch_subreddit_builds_correct_url(respx_mock):
    import respx
    route = respx_mock.get("https://www.reddit.com/r/Economics/hot.json?t=day&limit=5&raw_json=1")
    route.respond(200, json={"data": {"children": []}})

    from reddit_spider import fetch_subreddit
    fetch_subreddit("Economics", "hot", "day", 5, "fake_cookie")

    assert route.called


def test_fetch_subreddit_returns_posts_list(respx_mock):
    import respx
    route = respx_mock.get("https://www.reddit.com/r/test/top.json?t=week&limit=2&raw_json=1")
    route.respond(200, json={
        "data": {
            "children": [
                {"data": {"title": "Post 1", "score": 100}},
                {"data": {"title": "Post 2", "score": 50}},
            ]
        }
    })

    from reddit_spider import fetch_subreddit
    result = fetch_subreddit("test", "top", "week", 2, None)

    assert len(result) == 2
    assert result[0]["data"]["title"] == "Post 1"


def test_fetch_subreddit_handles_401_error(respx_mock):
    import respx
    route = respx_mock.get("https://www.reddit.com/r/test/hot.json?t=day&limit=10&raw_json=1")
    route.respond(401)

    from reddit_spider import fetch_subreddit
    result = fetch_subreddit("test", "hot", "day", 10, "bad_cookie")

    assert result == "⚠️ Cookie 已失效，请通过对话发送新的 cookie 字符串更新"


def test_fetch_subreddit_handles_403_error(respx_mock):
    import respx
    route = respx_mock.get("https://www.reddit.com/r/test/hot.json?t=day&limit=10&raw_json=1")
    route.respond(403)

    from reddit_spider import fetch_subreddit
    result = fetch_subreddit("test", "hot", "day", 10, "bad_cookie")

    assert result == "⚠️ Cookie 已失效，请通过对话发送新的 cookie 字符串更新"


def test_fetch_subreddit_handles_429_error(respx_mock):
    import respx
    route = respx_mock.get("https://www.reddit.com/r/test/hot.json?t=day&limit=10&raw_json=1")
    route.respond(429)

    from reddit_spider import fetch_subreddit
    result = fetch_subreddit("test", "hot", "day", 10, None)

    assert result == "⚠️ 请求频率过高，请稍后再试"


def test_fetch_subreddit_handles_timeout(respx_mock):
    import respx
    route = respx_mock.get("https://www.reddit.com/r/test/hot.json?t=day&limit=10&raw_json=1")
    route.side_effect = httpx.TimeoutException("Timeout")

    from reddit_spider import fetch_subreddit
    result = fetch_subreddit("test", "hot", "day", 10, None)

    assert result == "⚠️ 请求超时，请检查网络连接"


# ── fetch_search ────────────────────────────────────────────────────────────

def test_fetch_search_builds_correct_url(respx_mock):
    route = respx_mock.get("https://www.reddit.com/search.json?q=Federal+Reserve&sort=relevance&t=week&limit=10&raw_json=1")
    route.respond(200, json={"data": {"children": []}})

    from reddit_spider import fetch_search
    fetch_search("Federal Reserve", "relevance", "week", 10, None)

    assert route.called


def test_fetch_search_returns_posts_list(respx_mock):
    route = respx_mock.get("https://www.reddit.com/search.json?q=bitcoin&sort=new&t=day&limit=3&raw_json=1")
    route.respond(200, json={
        "data": {
            "children": [{"data": {"title": "Bitcoin post"}}]
        }
    })

    from reddit_spider import fetch_search
    result = fetch_search("bitcoin", "new", "day", 3, None)

    assert len(result) == 1
    assert result[0]["data"]["title"] == "Bitcoin post"


# ── main / CLI ─────────────────────────────────────────────────────────────

def test_main_subreddit_mode(capsys, respx_mock):
    route = respx_mock.get("https://www.reddit.com/r/Economics/hot.json?t=day&limit=10&raw_json=1")
    route.respond(200, json={
        "data": {
            "children": [{"data": {"title": "Test Post", "score": 100, "num_comments": 5, "author": "user1", "permalink": "/r/Economics/comments/abc/test/", "selftext": ""}}]
        }
    })

    from reddit_spider import main
    main(["--subreddit", "Economics", "--sort", "hot", "--time", "day", "--limit", "10"])

    captured = capsys.readouterr()
    assert "Test Post" in captured.out
    assert "100" in captured.out


def test_main_search_mode(capsys, respx_mock):
    route = respx_mock.get("https://www.reddit.com/search.json?q=inflation&sort=relevance&t=week&limit=5&raw_json=1")
    route.respond(200, json={"data": {"children": []}})

    from reddit_spider import main
    main(["--search", "inflation", "--sort", "relevance", "--time", "week", "--limit", "5"])

    captured = capsys.readouterr()
    assert "📭" in captured.out


def test_main_requires_subreddit_or_search(capsys):
    from reddit_spider import main
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_main_error_output(capsys, respx_mock):
    route = respx_mock.get("https://www.reddit.com/r/test/hot.json?t=day&limit=20&raw_json=1")
    route.respond(401)

    from reddit_spider import main
    main(["--subreddit", "test"])

    captured = capsys.readouterr()
    assert "⚠️ Cookie 已失效" in captured.out
