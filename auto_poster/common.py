import os
import sys
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
CAPTIONS_FILE = BASE_DIR / "captions.json"
POSTED_HISTORY_FILE = BASE_DIR / "posted_history.json"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def get_outputs_dir():
    candidates = [
        ROOT_DIR / "outputs",
        BASE_DIR / "outputs",
        ROOT_DIR / "slicer" / "outputs"
    ]
    for c in candidates:
        if c.exists() and list(c.glob("*.mp4")):
            return c
    out = ROOT_DIR / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out

def load_json(file_path, default=None):
    file_path = Path(file_path)
    if not file_path.exists():
        return default if default is not None else {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def save_json(file_path, data):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_accounts():
    if not ACCOUNTS_FILE.exists():
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def is_account_logged_in(account_dict):
    profile_dir = BASE_DIR / account_dict.get("profile_dir", f"profiles/{account_dict['id']}")
    cookies_path = profile_dir / "Default" / "Network" / "Cookies"
    if not cookies_path.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{cookies_path.as_posix()}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM cookies WHERE name = 'sessionid' LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return bool(row)
    except Exception as e:
        err_msg = str(e).lower()
        if "unable to open" in err_msg or "lock" in err_msg or "busy" in err_msg:
            return "CHROME_OPEN"
        return False
