import os
import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"

sys.path.append(str(BASE_DIR))
from database import db
from ai_caption import generate_ai_caption
from instagram_poster import post_reel_to_instagram

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

def main():
    print("=" * 65)
    print("      GHOST TRAFFIC // SINGLE REEL AUTO-DISPATCH")
    print("=" * 65)

    accounts = load_accounts()
    if not accounts:
        print("[!] No accounts found in accounts.json")
        input("\nPress Enter to exit...")
        return

    print("\nSelect Target Account:")
    for idx, acc in enumerate(accounts, 1):
        st = is_account_logged_in(acc)
        status = "[✓ Logged In]" if st is True else ("[!] Chrome Open" if st == "CHROME_OPEN" else "[! Login Required]")
        progress = db.get_account_progress(acc["id"])
        print(f" [{idx}] {acc['name']} ({acc['id']}) {status} - Next: Part {progress['next_part'] or 'DONE'}")

    choice = input(f"\nSelect account [1-{len(accounts)}] (default: 1): ").strip()
    selected_idx = 0
    if choice.isdigit() and 1 <= int(choice) <= len(accounts):
        selected_idx = int(choice) - 1

    selected_account = accounts[selected_idx]
    print(f"\n[*] Target Account Selected: {selected_account['name']} ({selected_account['id']})")

    # Check login state
    st = is_account_logged_in(selected_account)
    if st == "CHROME_OPEN":
        print("\n" + "!" * 65)
        print(f"[!] DHYAN DO: Chrome window abhi open hai!")
        print(f"    Agar Instagram par feed login ho gayi hai, toh pehle")
        print(f"    us Chrome window ko [X] CLOSE (band) kar do.")
        print(f"    (Jab tak Chrome band nahi hoga, session save aur unlock nahi hoga)")
        print("!" * 65)
        input("\nChrome window ko band karne ke baad yahan [ENTER] dabao...")
        st = is_account_logged_in(selected_account)

    if st is not True:
        print("\n" + "!" * 65)
        print(f"[!] WARNING: {selected_account['name']} is NOT logged in yet!")
        print(f"[!] Pehle '1_Login_Account_{selected_idx+1}.bat' par double click karke")
        print(f"    apna Instagram login karo, phir Chrome band karke ye script chalana.")
        print("!" * 65)
        input("\nPress Enter to exit...")
        return

    # Check if any videos exist in outputs
    all_videos = db.get_all_videos()
    if not all_videos:
        print("\n" + "!" * 65)
        print("[!] Koi video nahi mili!")
        print("    Kripya 'outputs' folder me apni .mp4 videos daalein.")
        print("!" * 65)
        input("\nPress Enter to exit...")
        return

    # Get next unposted clip
    next_clip = db.get_next_unposted_video(selected_account["id"])
    if not next_clip:
        print(f"\n[✓] Saari {len(all_videos)} videos already post ho chuki hain for {selected_account['name']}!")
        input("\nPress Enter to exit...")
        return

    clip_path = Path(next_clip["filepath"])
    part_num = next_clip["part"]
    total_parts = len(db.get_all_videos()) or 69

    print(f"\n[>] Next Sequential Payload: Part {part_num} of {total_parts}")
    print(f"[>] File: {clip_path.name}")

    caption = generate_ai_caption(clip_path.name, part_num, total_parts)
    print("\n--- AI DYNAMIC CAPTION PREVIEW ---")
    print(caption)
    print("----------------------------------\n")

    confirm = input("Press [ENTER] to dispatch this reel now (or 'q' to cancel): ").strip().lower()
    if confirm == 'q':
        print("[*] Dispatch cancelled by user.")
        return

    print("\n[*] Launching Chrome & Dispatching Reel...")
    success = post_reel_to_instagram(selected_account, clip_path, headless=False)

    if success:
        print("\n" + "=" * 65)
        print(f"[✓] SUCCESS! Part {part_num} successfully published on Instagram!")
        progress = db.get_account_progress(selected_account["id"])
        print(f"[✓] Progress: {progress['posted_count']}/{progress['total_clips']} reels posted.")
        print(f"[✓] Next up for next time: Part {progress['next_part'] or 'DONE'}")
        print("=" * 65)
    else:
        print("\n[!] Reel posting was not completed. Please check Chrome or debug_screenshots.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
