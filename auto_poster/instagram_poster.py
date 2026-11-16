import os
import sys
import time
import json
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from browser_factory import get_browser_context

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from common import (
        get_outputs_dir, load_json, save_json, load_accounts,
        BASE_DIR, ROOT_DIR, ACCOUNTS_FILE, CAPTIONS_FILE
    )
except ImportError:
    from auto_poster.common import (
        get_outputs_dir, load_json, save_json, load_accounts,
        BASE_DIR, ROOT_DIR, ACCOUNTS_FILE, CAPTIONS_FILE
    )

from database import db
from ai_caption import generate_ai_caption

OUTPUTS_DIR = get_outputs_dir()
DEBUG_DIR = BASE_DIR / "debug_screenshots"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

def load_captions_data():
    return load_json(CAPTIONS_FILE, {
        "spintax_hooks": ["Wait till the end! 😱", "Watch this! 🔥"],
        "default_cta": "👉 Full video on Telegram: @GhostTrafficHub",
        "hashtags": ["#reels", "#viral", "#explore"]
    })

def load_posted_history():
    db.sync_filesystem()
    return {fname: v.get("posted_by", []) for fname, v in db.db.get("videos", {}).items()}

def mark_as_posted(video_filename, account_id):
    db.mark_dispatched(video_filename, account_id)

def generate_caption(video_name, custom_cta=None):
    part_num = db._extract_part_number(video_name)
    total_parts = len(db.get_all_videos()) or None
    return generate_ai_caption(video_name, part_num, total_parts, custom_cta)

def post_reel_to_instagram(account_dict, video_path, headless=False, log_fn=None):
    """
    Automates uploading a reel to Instagram Web for a specific account.
    """
    def log(msg):
        print(msg)
        if log_fn:
            try:
                log_fn(msg)
            except Exception:
                pass

    account_id = account_dict["id"]
    profile_subpath = account_dict.get("profile_dir", f"profiles/{account_id}")
    video_path = Path(video_path).resolve()

    if not video_path.exists():
        log(f"[!] Video file not found: {video_path}")
        return False

    log(f"[*] Posting Video: {video_path.name}")
    log(f"[*] Target Node: {account_id} ({account_dict.get('name')})")

    with sync_playwright() as p:
        context = get_browser_context(
            p,
            profile_subpath=profile_subpath,
            headless=headless,
            proxy_dict=account_dict.get("proxy")
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(30000)

        try:
            log("[1/7] Navigating to Instagram...")
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            time.sleep(3)

            # Check if logged in
            if "accounts/login" in page.url or page.locator("input[name='username']").count() > 0:
                log(f"[!] ERROR: Account {account_id} is NOT logged in!")
                log(f"[!] Pehle 'Launch Browser' button dabakar account login karo.")
                page.screenshot(path=str(DEBUG_DIR / f"{account_id}_not_logged_in.png"))
                context.close()
                return False

            # Dismiss notifications / popups if present
            try:
                not_now_btns = page.locator("button:has-text('Not Now'), button:has-text('Cancel')")
                if not_now_btns.count() > 0:
                    not_now_btns.first.click(timeout=3000)
                    time.sleep(1)
            except Exception:
                pass

            log("[2/7] Opening 'Create' post modal...")
            # Click Create button
            create_btn = page.locator("svg[aria-label='New post'], svg[aria-label='Create'], span:text-is('Create'), a[role='link']:has-text('Create')").first
            create_btn.wait_for(state="visible", timeout=10000)
            create_btn.click()
            time.sleep(2)

            # If clicking Create opened a popover with "Post" option
            post_submenu = page.locator("span:text-is('Post'), div[role='button']:has-text('Post')")
            if post_submenu.count() > 0 and post_submenu.first.is_visible():
                post_submenu.first.click()
                time.sleep(1)

            log("[3/7] Uploading video file...")
            file_input = None
            file_input_selectors = [
                "input[type='file'][accept*='video']",
                "input[type='file']",
                "div[role='dialog'] input[type='file']",
                "form input[type='file']"
            ]
            for sel in file_input_selectors:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0:
                        file_input = el
                        log(f"  -> File input matched with selector: '{sel}'")
                        break
                except Exception:
                    pass

            if not file_input:
                file_input = page.locator("input[type='file']").first

            file_input.wait_for(state="attached", timeout=10000)
            file_input.set_input_files(str(video_path))
            log("  -> File attached to file input.")
            time.sleep(4)

            # Grab reference to the main create reel dialog
            dialog = page.locator("div[role='dialog']").first

            # Check for "Video posts are now shared as reels" modal
            try:
                reels_ok_btn = page.locator("button:has-text('OK'), div[role='button']:has-text('OK')").first
                if reels_ok_btn.is_visible(timeout=3000):
                    try:
                        reels_ok_btn.click(force=True, timeout=2000)
                    except Exception:
                        reels_ok_btn.dispatch_event("click")
                    time.sleep(1.5)
            except Exception:
                pass

            log("[4/7] Setting 9:16 aspect ratio...")
            try:
                time.sleep(1)
                crop_selectors = [
                    "button:has(svg[aria-label='Select crop'])",
                    "div[role='button']:has(svg[aria-label='Select crop'])",
                    "svg[aria-label='Select crop']",
                    "[aria-label='Select crop']",
                    "button:has(svg[aria-label='Crop'])",
                    "div[role='button']:has(svg[aria-label='Crop'])"
                ]
                crop_btn = None
                for c_sel in crop_selectors:
                    try:
                        el = dialog.locator(c_sel).first
                        if el.count() > 0 and el.is_visible():
                            crop_btn = el
                            log(f"  -> Crop button matched with selector: '{c_sel}'")
                            break
                    except Exception:
                        pass

                if crop_btn:
                    try:
                        crop_btn.click(force=True, timeout=3000)
                    except Exception:
                        crop_btn.dispatch_event("click")
                    time.sleep(1)

                    # Find '9:16' or 'Original' ratio button inside dialog
                    ratio_btn = None
                    for r_query in ["9:16", "Original"]:
                        try:
                            btn = dialog.get_by_role("button", name=r_query, exact=True)
                            if btn.count() > 0 and btn.first.is_visible():
                                ratio_btn = btn.first
                                log(f"  -> Ratio button matched role button: '{r_query}'")
                                break
                        except Exception:
                            pass
                        try:
                            txt_el = dialog.get_by_text(r_query, exact=True)
                            if txt_el.count() > 0 and txt_el.first.is_visible():
                                ratio_btn = txt_el.first
                                log(f"  -> Ratio button matched text: '{r_query}'")
                                break
                        except Exception:
                            pass

                    if not ratio_btn:
                        filtered = dialog.locator(
                            "div[role='button']:has-text('9:16'), "
                            "button:has-text('9:16'), "
                            "[role='button']:has-text('Original'):not(:has-text('audio'))"
                        )
                        if filtered.count() > 0 and filtered.first.is_visible():
                            ratio_btn = filtered.first
                            log("  -> Ratio button matched CSS fallback")

                    if ratio_btn and ratio_btn.is_visible():
                        try:
                            ratio_btn.click(force=True, timeout=3000)
                        except Exception:
                            ratio_btn.dispatch_event("click")
                        log("  -> 9:16 (Original) ratio selected successfully. [OK]")
                        time.sleep(1)

                # Safety check: if Discard prompt appeared, dismiss it by clicking Cancel
                try:
                    cancel_btn = page.locator("div[role='dialog'] button:has-text('Cancel'), button:text-is('Cancel')")
                    if cancel_btn.count() > 0 and cancel_btn.first.is_visible():
                        cancel_btn.first.click(force=True)
                        time.sleep(1)
                except Exception:
                    pass

            except Exception as e:
                log(f"  (Aspect ratio selection skipped: {e})")

            log("[5/7] Navigating through editor...")
            next_btn = dialog.locator("div[role='button']:has-text('Next'), button:has-text('Next')").first
            next_btn.wait_for(state="visible", timeout=10000)
            next_btn.click(force=True)
            time.sleep(2)

            next_btn = dialog.locator("div[role='button']:has-text('Next'), button:has-text('Next')").first
            next_btn.wait_for(state="visible", timeout=10000)
            next_btn.click(force=True)
            time.sleep(2)

            log("[6/7] Adding caption & hashtags...")
            caption_text = generate_caption(video_path.name)
            caption_selectors = [
                "div[aria-label='Write a caption...']",
                "div[aria-label*='caption']",
                "div[contenteditable='true'][role='textbox']",
                "div[contenteditable='true']",
                "textarea[aria-label*='caption']"
            ]
            caption_box = None
            for cap_sel in caption_selectors:
                try:
                    el = dialog.locator(cap_sel).first
                    if el.count() > 0 and el.is_visible():
                        caption_box = el
                        log(f"  -> Caption input matched selector: '{cap_sel}'")
                        break
                except Exception:
                    pass

            if not caption_box:
                caption_box = dialog.locator("div[aria-label='Write a caption...'], div[contenteditable='true']").first

            caption_box.wait_for(state="visible", timeout=10000)
            caption_box.click(force=True)
            time.sleep(0.5)

            caption_box.fill(caption_text)
            time.sleep(1.5)

            log("[7/7] Sharing Reel...")
            time.sleep(1)

            # 1. If any "Discard post?" confirmation popped up, dismiss it
            try:
                cancel_btn = page.locator("div[role='dialog'] button:has-text('Cancel'), div[role='dialog'] div[role='button']:has-text('Cancel')")
                if cancel_btn.count() > 0 and cancel_btn.first.is_visible():
                    cancel_btn.first.click()
                    time.sleep(1)
            except Exception:
                pass

            # 2. Locate the Share button inside the Create dialog
            dialog = page.locator("div[role='dialog']").first
            share_btn = None

            # Primary: get_by_role('button', name='Share', exact=True)
            try:
                role_share = dialog.get_by_role("button", name="Share", exact=True)
                if role_share.count() > 0 and role_share.first.is_visible():
                    share_btn = role_share.first
                    log("  -> Share button matched role button: 'Share'")
            except Exception:
                pass

            # Secondary: Search visible buttons in dialog strictly matching exact text "Share" (ignoring "Share to")
            if not share_btn:
                buttons = dialog.locator("div[role='button'], button")
                for i in range(buttons.count()):
                    btn = buttons.nth(i)
                    try:
                        if btn.inner_text().strip() == "Share" and btn.is_visible():
                            share_btn = btn
                            log("  -> Share button matched exact text 'Share'")
                            break
                    except Exception:
                        pass

            # Fallback selectors
            if not share_btn:
                share_fallbacks = [
                    "div[role='button']:has-text('Share')",
                    "button:has-text('Share')",
                    "[aria-label='Share']"
                ]
                for s_sel in share_fallbacks:
                    try:
                        el = dialog.locator(s_sel).first
                        if el.count() > 0 and el.is_visible():
                            share_btn = el
                            log(f"  -> Share button matched fallback selector: '{s_sel}'")
                            break
                    except Exception:
                        pass

            if not share_btn:
                share_btn = dialog.locator("div[role='button']:has-text('Share')").first

            share_btn.wait_for(state="visible", timeout=10000)

            # 3. Robust multi-method click
            log("  -> Clicking 'Share' button...")
            try:
                share_btn.click(timeout=3000)
            except Exception:
                log("  -> Standard click bypassed, executing direct force click...")
                try:
                    share_btn.click(force=True, timeout=3000)
                except Exception:
                    log("  -> Dispatching DOM click...")
                    share_btn.dispatch_event("click")

            # Brief pause, re-check if button needs a second click
            time.sleep(2)
            try:
                if share_btn.is_visible() and page.locator("text='Sharing', div[role='progressbar']").count() == 0:
                    share_btn.click(force=True, timeout=2000)
            except Exception:
                pass

            log("  -> Uploading and processing video (waiting up to 90 seconds)...")
            upload_done = False
            start_time = time.time()
            while time.time() - start_time < 90:
                time.sleep(2)
                # Check for success confirmation text
                success_text = page.locator("text='Your reel has been shared', text='Your post has been shared', text='Reel shared', text='Shared'")
                if success_text.count() > 0 and success_text.first.is_visible():
                    upload_done = True
                    break

                # If the modal dialog itself closed, reel is shared
                if dialog.count() == 0:
                    upload_done = True
                    break

                # If sharing spinner is showing, keep waiting
                sharing_indicator = page.locator("text='Sharing', div[role='progressbar'], svg[aria-label='Loading...']")
                if sharing_indicator.count() > 0:
                    time.sleep(1)
                    continue

            if upload_done:
                log("\n[✓] SUCCESS: Reel successfully published on Instagram! [OK]")
                mark_as_posted(video_path.name, account_id)
                db.mark_dispatched(video_path.name, account_id)
                time.sleep(3)
                context.close()
                return True
            else:
                log("[!] Timeout waiting for final confirmation. Checking screenshot...")
                ts = int(time.time())
                page.screenshot(path=str(DEBUG_DIR / f"{account_id}_upload_status_{ts}.png"))
                page.screenshot(path=str(DEBUG_DIR / f"{account_id}_upload_status.png"))
                if share_btn and (share_btn.count() == 0 or not share_btn.is_visible()):
                    log("[✓] Share button disappeared. Post is likely uploaded.")
                    mark_as_posted(video_path.name, account_id)
                    db.mark_dispatched(video_path.name, account_id)
                    context.close()
                    return True
                else:
                    log("[!] Upload might not have completed.")
                    print("[!] Instagram UI badla ho sakta hai, debug_screenshots check karo.")
                    context.close()
                    return False

        except Exception as e:
            ts = int(time.time())
            print(f"[!] Error during posting: {e}")
            try:
                err_path = DEBUG_DIR / f"{account_id}_error_{ts}.png"
                page.screenshot(path=str(err_path))
                page.screenshot(path=str(DEBUG_DIR / f"{account_id}_error.png"))
                print(f"[i] Debug screenshot saved: debug_screenshots/{err_path.name}")
            except Exception:
                pass
            print("[!] Instagram UI badla ho sakta hai, debug_screenshots check karo.")
            context.close()
            return False

if __name__ == "__main__":
    from login_manager import load_accounts

    accounts = load_accounts()
    if not accounts:
        print("[!] No accounts found in accounts.json")
        sys.exit(1)

    # Find first available clip in outputs/
    clips = sorted(list(OUTPUTS_DIR.glob("*.mp4")))
    if not clips:
        print("[!] No .mp4 clips found in outputs/ directory.")
        sys.exit(1)

    print(f"Found {len(clips)} clips in outputs/")
    target_clip = clips[0]
    target_account = accounts[0]

    post_reel_to_instagram(target_account, target_clip, headless=False)
