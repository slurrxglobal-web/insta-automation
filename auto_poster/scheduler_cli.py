import os
import sys
import json
import time
import random
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
from ai_caption import generate_ai_caption
from instagram_poster import post_reel_to_instagram

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 65)
    print("      GHOST TRAFFIC // AUTONOMOUS DRIP SCHEDULER")
    print("=" * 65)

    accounts = load_accounts()
    if not accounts:
        print("[!] No accounts found in accounts.json")
        input("\nPress Enter to exit...")
        return

    active_accounts = [a for a in accounts if a.get("enabled", True) and is_account_logged_in(a)]
    if not active_accounts:
        print("\n[!] No logged-in accounts found!")
        print("[!] Pehle '1_Login_Account_1.bat' chala kar account login karo.")
        input("\nPress Enter to exit...")
        return

    print(f"\n[✓] Found {len(active_accounts)} active logged-in account(s):")
    for a in active_accounts:
        p = db.get_account_progress(a["id"])
        print(f"  - {a['name']} ({a['id']}): Next Part {p['next_part'] or 'DONE'} ({p['posted_count']}/{p['total_clips']} posted)")

    interval_input = input("\nEnter posting interval in minutes (default: 60): ").strip()
    interval_mins = 60
    if interval_input.isdigit() and int(interval_input) >= 10:
        interval_mins = int(interval_input)

    print(f"\n[*] Scheduler started! Interval: {interval_mins} minutes per cycle.")
    print("[*] Press Ctrl+C at any time to stop.\n")

    cycle = 1
    while True:
        print(f"\n>>> CYCLE #{cycle} STARTING ({time.strftime('%Y-%m-%d %H:%M:%S')}) <<<")
        for acc in active_accounts:
            next_clip = db.get_next_unposted_video(acc["id"])
            if not next_clip:
                print(f"[*] All clips posted for {acc['name']}.")
                continue

            clip_path = Path(next_clip["filepath"])
            part_num = next_clip["part"]
            print(f"\n[>] Dispatching Part {part_num} to {acc['name']}...")
            try:
                success = post_reel_to_instagram(acc, clip_path, headless=False)
                if success:
                    print(f"[✓] Part {part_num} successfully published for {acc['name']}!")
                else:
                    print(f"[!] Upload failed for Part {part_num}.")
            except Exception as e:
                print(f"[!] Error during posting: {e}")

            # 45 second humanized jitter between accounts
            time.sleep(45)

        cycle += 1
        sleep_secs = interval_mins * 60 + random.randint(-60, 60)
        print(f"\n[*] Cycle complete. Next post scheduled in {interval_mins} mins (~{sleep_secs // 60}m)...")
        for remaining in range(sleep_secs, 0, -10):
            mins_left = remaining // 60
            secs_left = remaining % 60
            print(f"\rNext upload in: {mins_left:02d}m {secs_left:02d}s ... (Ctrl+C to stop)", end="", flush=True)
            time.sleep(10)
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Scheduler stopped by user.")
        input("\nPress Enter to exit...")
