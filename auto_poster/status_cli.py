import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"

sys.path.append(str(BASE_DIR))
from database import db

def load_accounts():
    if ACCOUNTS_FILE.exists():
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def is_account_logged_in(account_dict):
    profile_dir = BASE_DIR / account_dict.get("profile_dir", f"profiles/{account_dict['id']}")
    cookies_path = profile_dir / "Default" / "Network" / "Cookies"
    if not cookies_path.exists():
        return False
    try:
        import sqlite3
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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 65)
    print("      GHOST TRAFFIC // QUEUE & ACCOUNT TELEMETRY")
    print("=" * 65)

    all_vids = db.get_all_videos()
    print(f"\n[+] Total Sequenced Clips in Pipeline: {len(all_vids)}")

    accounts = load_accounts()
    print("\n--- ACCOUNTS STATUS ---")
    for a in accounts:
        logged = is_account_logged_in(a)
        if logged is True:
            status_str = "[OK] LOGGED IN (READY)"
        elif logged == "CHROME_OPEN":
            status_str = "[!] CHROME IS OPEN (Please close Chrome to unlock session)"
        else:
            status_str = "[!] LOGIN REQUIRED"
        p = db.get_account_progress(a["id"])
        print(f"\nAccount: {a['name']} ({a['id']})")
        print(f"  Platform:    {a.get('platform', 'instagram').upper()}")
        print(f"  Auth Status: {status_str}")
        print(f"  Progress:    {p['posted_count']} / {p['total_clips']} reels posted")
        print(f"  Next Part:   Part {p['next_part'] or 'DONE (All Videos Posted!)'}")
        if p.get("next_filename"):
            print(f"  Next File:   {p['next_filename']}")

    print("\n" + "=" * 65)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
