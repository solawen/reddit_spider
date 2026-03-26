import json
import pytest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "reddit-spider" / "scripts"))
from cookie_manager import (
    parse_cookie_string,
    save_cookies,
    load_cookies,
    bootstrap_from_chrome_info,
)


def test_parse_cookie_string_strips_whitespace():
    assert parse_cookie_string("  token=abc; session=xyz  ") == "token=abc; session=xyz"


def test_parse_cookie_string_passthrough():
    raw = "token=abc; session=xyz"
    assert parse_cookie_string(raw) == raw


def test_save_and_load_roundtrip(tmp_path):
    cookie_str = "token=abc123; session=xyz"
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"):
        save_cookies(cookie_str)
        result = load_cookies()
    assert result == cookie_str


def test_save_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "cookies.json"
    with patch("cookie_manager.COOKIE_FILE", nested):
        save_cookies("token=abc")
    assert nested.exists()


def test_save_writes_updated_at(tmp_path):
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "cookies.json"):
        save_cookies("token=abc")
        data = json.loads((tmp_path / "cookies.json").read_text())
    assert "updated_at" in data


def test_load_returns_none_when_file_missing(tmp_path):
    with patch("cookie_manager.COOKIE_FILE", tmp_path / "nonexistent.json"):
        assert load_cookies() is None


def test_bootstrap_extracts_cookie_line(tmp_path):
    chrome_info = tmp_path / "chrome_info.txt"
    chrome_info.write_text(
        ":authority\nwww.reddit.com\ncookie\ntoken=abc; session=xyz\ndnt\n1\n"
    )
    assert bootstrap_from_chrome_info(chrome_info) == "token=abc; session=xyz"


def test_bootstrap_returns_none_when_no_cookie_header(tmp_path):
    chrome_info = tmp_path / "chrome_info.txt"
    chrome_info.write_text(":authority\nwww.reddit.com\ndnt\n1\n")
    assert bootstrap_from_chrome_info(chrome_info) is None


def test_bootstrap_returns_none_for_missing_file(tmp_path):
    assert bootstrap_from_chrome_info(tmp_path / "missing.txt") is None
