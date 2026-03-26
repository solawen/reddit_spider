import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

COOKIE_FILE = Path.home() / ".openclaw" / "reddit-spider" / "cookies.json"


def parse_cookie_string(raw: str) -> str:
    return raw.strip()


def save_cookies(cookie_string: str) -> None:
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "updated_at": datetime.now().isoformat(),
        "cookie_string": cookie_string,
    }
    COOKIE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_cookies() -> str | None:
    if not COOKIE_FILE.exists():
        return None
    data = json.loads(COOKIE_FILE.read_text())
    return data.get("cookie_string")


def bootstrap_from_chrome_info(chrome_info_path: Path) -> str | None:
    if not chrome_info_path.exists():
        return None
    lines = chrome_info_path.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "cookie" and i + 1 < len(lines):
            return lines[i + 1].strip()
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Reddit cookies for reddit-spider")
    parser.add_argument("--update", metavar="COOKIE_STRING", required=True,
                        help="Raw cookie string to store")
    args = parser.parse_args()
    cookie_string = parse_cookie_string(args.update)
    save_cookies(cookie_string)
    print("Cookie updated")
