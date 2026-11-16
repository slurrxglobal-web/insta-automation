import os
import sys
import time
import json
import random
from pathlib import Path
from instagram_poster import post_reel_to_instagram, load_posted_history

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from common import get_outputs_dir, load_accounts, BASE_DIR, ROOT_DIR, ACCOUNTS_FILE
except ImportError:
    from auto_poster.common import get_outputs_dir, load_accounts, BASE_DIR, ROOT_DIR, ACCOUNTS_FILE

OUTPUTS_DIR = get_outputs_dir()

def get_unposted_clips_for_account(account_id):
    history = load_posted_history()
    all_clips = sorted(list(OUTPUTS_DIR.glob("*.mp4")), key=lambda p: p.name)
    unposted = []
    for c in all_clips:
        posted_accounts = history.get(c.name, [])
        if account_id not in posted_accounts:
            unposted.append(c)
    return unposted

def interactive_menu():
    print("""
=============================================================
👻 GHOST TRAFFIC - AUTO POSTER (MULTI-ACCOUNT MATRIX)
=============================================================
 [1] Login / Connect an Account (One-Time Setup)
 [2] Post NEXT Reel on 1 Account (Instant Test)
 [3] Post 1 Reel Across ALL Active Accounts
 [4] Start Automated Drip Scheduler (Loop with intervals)
 [5] View Accounts & Upload Statistics
 [0] Exit
=============================================================
""")
    choice = input("Select an option (0-5): ").strip()
    return choice

def main():
    while True:
        choice = interactive_menu()

        if choice == "1":
            from login_manager import run_login
            run_login()

        elif choice == "2":
            accounts = [a for a in load_accounts() if a.get("enabled", True)]
            if not accounts:
                print("[!] No enabled accounts in accounts.json")
                continue
            
            print("\nSelect Account to post:")
            for i, a in enumerate(accounts, 1):
                unposted = len(get_unposted_clips_for_account(a["id"]))
                print(f" [{i}] {a['id']} ({a.get('name')}) - {unposted} clips available")
            
            pick = input("Pick account number: ").strip()
            try:
                acc = accounts[int(pick) - 1]
            except Exception:
                print("[!] Invalid choice.")
                continue

            unposted = get_unposted_clips_for_account(acc["id"])
            if not unposted:
                print(f"[!] No unposted clips available in outputs/ for {acc['id']}.")
                continue

            clip = unposted[0]
            print(f"\nTarget Clip: {clip.name}")
            show_browser = input("Show browser window while posting? (y/n, default=y): ").strip().lower() != "n"
            post_reel_to_instagram(acc, clip, headless=not show_browser)

        elif choice == "3":
            accounts = [a for a in load_accounts() if a.get("enabled", True)]
            if not accounts:
                print("[!] No enabled accounts.")
                continue

            print(f"\n[*] Starting broadcast to {len(accounts)} active accounts...")
            for acc in accounts:
                unposted = get_unposted_clips_for_account(acc["id"])
                if not unposted:
                    print(f"[-] No unposted clips for {acc['id']}, skipping.")
                    continue
                clip = unposted[0]
                print(f"\n>>> Posting to {acc['id']}: {clip.name}")
                post_reel_to_instagram(acc, clip, headless=False)
                
                # Jitter delay between accounts to prevent simultaneous activity flag
                delay = random.randint(30, 60)
                print(f"[*] Sleeping {delay} seconds before next account to stay safe...")
                time.sleep(delay)

        elif choice == "4":
            print("\n--- AUTOMATED DRIP SCHEDULER ---")
            interval_min = input("Interval between posts in MINUTES (e.g. 60 or 90): ").strip()
            try:
                interval_sec = int(interval_min) * 60
            except ValueError:
                interval_sec = 60 * 60

            print(f"[*] Drip scheduler started. Interval: {interval_sec // 60} minutes.")
            print("[*] Press Ctrl+C anytime to stop.\n")

            while True:
                accounts = [a for a in load_accounts() if a.get("enabled", True)]
                for acc in accounts:
                    unposted = get_unposted_clips_for_account(acc["id"])
                    if not unposted:
                        print(f"[-] No clips left for {acc['id']}.")
                        continue
                    clip = unposted[0]
                    print(f"\n[+] {time.strftime('%Y-%m-%d %H:%M:%S')} - Posting to {acc['id']}: {clip.name}")
                    post_reel_to_instagram(acc, clip, headless=True)
                    time.sleep(random.randint(45, 90))

                print(f"\n[💤] Sleeping for {interval_sec // 60} minutes until next round...")
                time.sleep(interval_sec)

        elif choice == "5":
            accounts = load_accounts()
            history = load_posted_history()
            all_clips = list(OUTPUTS_DIR.glob("*.mp4"))
            print("\n================ ACCOUNTS STATUS ================")
            print(f"Total Video Clips in outputs/: {len(all_clips)}")
            print(f"Total Posts in History: {len(history)}")
            print("-------------------------------------------------")
            for a in accounts:
                unposted = len(get_unposted_clips_for_account(a["id"]))
                posted = len(all_clips) - unposted
                print(f"• ID: {a['id']:<10} | Name: {a.get('name', ''):<22} | Platform: {a.get('platform'):<10} | Posted: {posted} | Remaining: {unposted}")
            print("=================================================\n")

        elif choice == "0":
            print("Exiting Auto Poster. Bye!")
            break

if __name__ == "__main__":
    main()
