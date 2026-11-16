import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from common import load_accounts, is_account_logged_in, BASE_DIR, ROOT_DIR, ACCOUNTS_FILE
except ImportError:
    from auto_poster.common import load_accounts, is_account_logged_in, BASE_DIR, ROOT_DIR, ACCOUNTS_FILE

from database import db

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
