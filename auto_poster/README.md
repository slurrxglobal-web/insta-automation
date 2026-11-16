# 🚀 Ghost Traffic - Multi-Account Auto Poster

Custom-built isolated browser automation engine using **Playwright Persistent Contexts**.  
No AdsPower or paid software needed.

---

## 📁 File Structure

- **`accounts.json`**: Account configuration (ID, name, platform, profile folder, optional proxy).
- **`captions.json`**: Dynamic hook titles, CTA, and hashtag rotation bank.
- **`common.py`**: Unified shared logic for accounts, profiles, output paths, and JSON storage.
- **`database.py`**: Pipeline queue database managing sequential order and telemetry.
- **`ghost_database.json`**: Single source of truth tracking reel metadata, sequence part, and dispatch status per account. *(Note: `posted_history.json` is legacy and automatically migrated on first run).*
- **`browser_factory.py`**: Isolated Chromium browser launcher with anti-detect stealth & proxy support.
- **`login_manager.py`**: Interactive one-time login tool. Opens visible browser window to log in and save cookies/session permanently.
- **`instagram_poster.py`**: Instagram Reels automated uploader (file attach, 9:16 aspect ratio, dynamic spintax captions, share) with resilient fallback selectors.
- **`post_single.py`**: Instant single reel dispatcher.
- **`scheduler_cli.py`**: Autonomous interval drip scheduler.
- **`status_cli.py`**: Real-time queue and account telemetry viewer.
- **`gui_poster.py`**: Tkinter desktop UI for visual control.
- **`web_poster.py`**: Localhost Web Studio dashboard (Port 5050).
- **`run_poster.py`**: Interactive CLI controller.

---

## ⚡ Quick Start

### Step 1: One-Time Login
Double-click `Start_Auto_Poster.bat` (or run `python auto_poster/login_manager.py`).
1. Choose Account 1 (`insta_01`).
2. Browser window will pop open.
3. Log in to Instagram with your credentials + OTP/2FA.
4. Press `[ENTER]` in terminal. Your session is now saved permanently in `profiles/insta_01`.
5. Repeat for Account 2 (`insta_02`).

### Step 2: Test Post
1. Choose option `[2]` in `run_poster.py`.
2. Select account.
3. Watch the browser automatically pick the first unposted reel from `outputs/`, set aspect ratio, type caption, and publish!

---

## 🛡️ Adding Proxies Later (When Scaling to 10+ Accounts)
In `accounts.json`, simply edit the `"proxy"` field:
```json
{
  "id": "insta_01",
  "platform": "instagram",
  "name": "Instagram Account 1",
  "profile_dir": "profiles/insta_01",
  "proxy": {
    "server": "http://123.45.67.89:8080",
    "username": "user123",
    "password": "pass123"
  },
  "enabled": true
}
```
If `"proxy": null`, it uses your normal direct connection.
