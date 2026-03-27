"""
Integration smoke test for reddit-spider skill.
Tests the end-to-end flow with mocked HTTP responses.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "reddit-spider" / "scripts"))


@pytest.fixture
def mock_cookies(tmp_path):
    """Provide mocked cookie file path."""
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"):
        yield tmp_path


def test_smoke_subreddit_fetch(capsys, respx_mock, mock_cookies):
    """End-to-end test: subreddit fetch flow."""
    import respx
    from reddit_spider import main

    # Mock Reddit API response
    route = respx_mock.get("https://www.reddit.com/r/Economics/top.json?t=day&limit=5&raw_json=1")
    route.respond(200, json={
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Fed Raises Interest Rates",
                        "score": 5420,
                        "num_comments": 342,
                        "author": "econ_user",
                        "permalink": "/r/Economics/comments/abc123/fed_raises_rates/",
                        "selftext": "The Federal Reserve announced..."
                    }
                },
                {
                    "data": {
                        "title": "Inflation Data Released",
                        "score": 3200,
                        "num_comments": 128,
                        "author": "data_analyst",
                        "permalink": "/r/Economics/comments/def456/inflation_data/",
                        "selftext": ""
                    }
                }
            ]
        }
    })

    # Run the main function
    main(["--subreddit", "Economics", "--sort", "top", "--time", "day", "--limit", "5"])

    # Verify output
    captured = capsys.readouterr()
    output = captured.out

    assert "📌 r/Economics · Top · day" in output
    assert "Fed Raises Interest Rates" in output
    assert "Inflation Data Released" in output
    assert "5,420" in output or "5420" in output
    assert "u/econ_user" in output
    assert "u/data_analyst" in output
    assert "共 2 条" in output
    assert "⏱ 抓取时间:" in output


def test_smoke_search_flow(capsys, respx_mock, mock_cookies):
    """End-to-end test: search flow."""
    route = respx_mock.get("https://www.reddit.com/search.json?q=bitcoin+ETF&sort=new&t=week&limit=3&raw_json=1")
    route.respond(200, json={
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Bitcoin ETF Approved",
                        "score": 15000,
                        "num_comments": 2500,
                        "author": "crypto_news",
                        "permalink": "/r/CryptoCurrency/comments/ghi789/bitcoin_etf/",
                        "selftext": "SEC approves first Bitcoin ETF..."
                    }
                }
            ]
        }
    })

    from reddit_spider import main
    main(["--search", "bitcoin ETF", "--sort", "new", "--time", "week", "--limit", "3"])

    captured = capsys.readouterr()
    output = captured.out

    assert "📌 Search: bitcoin ETF · New · week" in output
    assert "Bitcoin ETF Approved" in output
    assert "u/crypto_news" in output
    assert "共 1 条" in output


def test_smoke_cookie_bootstrap_and_fetch(capsys, tmp_path, respx_mock):
    """Test cookie bootstrap from chrome_info.txt and subsequent fetch."""
    # Create chrome_info.txt with cookie
    chrome_info = tmp_path / "chrome_info.txt"
    chrome_info.write_text(
        ":authority\nwww.reddit.com\ncookie\nbootstrap_cookie=value123\ndnt\n1\n"
    )

    # Mock Reddit API
    route = respx_mock.get("https://www.reddit.com/r/popular/hot.json?t=day&limit=20&raw_json=1")
    route.respond(200, json={
        "data": {
            "children": [{"data": {"title": "Popular Post", "score": 1000, "num_comments": 50, "author": "user", "permalink": "/r/popular/comments/xyz/popular_post/", "selftext": ""}}]
        }
    })

    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"):
        with patch("reddit_spider.CHROME_INFO_PATH", chrome_info):
            from reddit_spider import main
            main(["--subreddit", "popular"])

    captured = capsys.readouterr()
    assert "Popular Post" in captured.out


def test_smoke_empty_results(capsys, respx_mock, mock_cookies):
    """Test handling of empty results."""
    route = respx_mock.get("https://www.reddit.com/r/EmptySub/hot.json?t=day&limit=20&raw_json=1")
    route.respond(200, json={"data": {"children": []}})

    from reddit_spider import main
    main(["--subreddit", "EmptySub"])

    captured = capsys.readouterr()
    assert "📭 未找到相关内容" in captured.out


def test_smoke_error_propagation(capsys, respx_mock, mock_cookies):
    """Test that errors are properly propagated to output."""
    route = respx_mock.get("https://www.reddit.com/r/test/hot.json?t=day&limit=20&raw_json=1")
    route.respond(401)

    from reddit_spider import main
    main(["--subreddit", "test"])

    captured = capsys.readouterr()
    assert "⚠️ Cookie 已失效" in captured.out
