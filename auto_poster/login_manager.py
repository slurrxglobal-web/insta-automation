import os
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_factory import get_browser_context

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from common import load_accounts, BASE_DIR, ACCOUNTS_FILE
except ImportError:
    from auto_poster.common import load_accounts, BASE_DIR, ACCOUNTS_FILE

def run_login(account_id=None):
    accounts = load_accounts()
    if not accounts:
        print("[!] accounts.json me koi account nahi mila.")
        return

    selected = None
    if account_id:
        for acc in accounts:
            if acc["id"] == account_id:
                selected = acc
                break
    
    if not selected:
        print("\n=== SELECT ACCOUNT TO LOGIN ===")
        for i, acc in enumerate(accounts, 1):
            print(f" [{i}] {acc['id']} - {acc.get('name', 'Account')} ({acc.get('platform')})")
        
        choice = input("\nEnter number (e.g. 1): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(accounts):
                selected = accounts[idx]
        except ValueError:
            pass

    if not selected:
        print("[!] Invalid selection.")
        return

    profile_subpath = selected.get("profile_dir", f"profiles/{selected['id']}")
    platform = selected.get("platform", "instagram")
    
    target_url = "https://www.instagram.com/"
    if platform == "twitter":
        target_url = "https://x.com/login"
    elif platform == "facebook":
        target_url = "https://www.facebook.com/"
    elif platform == "snapchat":
        target_url = "https://my.snapchat.com/"
    elif platform == "pinterest":
        target_url = "https://www.pinterest.com/login/"

    print(f"\n[+] Launching browser for: {selected['id']} ({selected.get('name')})")
    print(f"[+] Profile directory: {profile_subpath}")
    print(f"[+] Target: {target_url}")

    with sync_playwright() as p:
        context = get_browser_context(
            p,
            profile_subpath=profile_subpath,
            headless=False,
            proxy_dict=selected.get("proxy")
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(target_url)

        print("\n" + "="*60)
        print("👉 BROWSER KHUL GAYA HAI!")
        print("1. Browser me apna Instagram account login karo (ID + Password).")
        print("2. OTP / 2FA verification complete karo.")
        print("3. 'Save Login Info' aaye toh 'Save' click karo.")
        print("4. Jab feed dikhne lage aur account login ho jaye...")
        print("👉 TAB YAHAN TERMINAL ME [ENTER] DABANA.")
        print("="*60 + "\n")

        input("Login complete hone ke baad yahan [ENTER] dabao...")

        # Quick verification of cookies
        cookies = context.cookies()
        session_found = any("sessionid" in c["name"] for c in cookies)
        if session_found:
            print("\n[✓] SUCCESS: Instagram session cookie successfully detected and stored!")
        else:
            print("\n[*] Session data saved to profile folder.")

        context.close()
        print(f"[✓] Browser closed cleanly. {selected['id']} is permanently saved!\n")

if __name__ == "__main__":
    acc_id = sys.argv[1] if len(sys.argv) > 1 else None
    run_login(acc_id)
