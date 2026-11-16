# 🚀 Ghost Traffic // Instagram Reels Multi-Account Auto-Poster

An automated, anti-detect Instagram Reels syndication engine built on **Playwright Persistent Contexts**. Designed to sequentially publish 9:16 vertical video reels across multiple accounts with anti-duplicate AI captions and hashtags.

---

## ⚡ Quick Start (In 3 Minutes)

### 1. Prerequisites
- **Windows 10 / 11**
- **Google Chrome** installed
- **Python 3.10+** installed (*Ensure "Add Python to PATH" was checked during installation*)

### 2. One-Click Setup
Double-click **`0_Setup_Install_Requirements.bat`**.  
This automatically installs Playwright and downloads the required browser binaries.

### 3. Add Your Reels
Copy your vertical `.mp4` video files into the **`outputs/`** directory.  
Files should include part numbers in their names (e.g. `Part_01.mp4`, `Part_02.mp4` ... `Part_69.mp4`).

### 4. Authenticate Account
Double-click **`1_Login_Account_1.bat`**.
- Google Chrome will open with an isolated profile.
- Log in with your Instagram credentials and complete OTP/2FA.
- Once you see your Instagram feed, **close the Chrome window (`[X]`)** so session cookies are saved and unlocked.

### 5. Dispatch Reels!
- **Post Next Single Reel:** Double-click **`2_Post_Single_Reel.bat`**.
- **Automated Drip Scheduler:** Double-click **`3_Start_Auto_Scheduler.bat`** and set your posting interval (e.g., 60 minutes).
- **Check Pipeline Status:** Double-click **`4_Check_Queue_Status.bat`** to view telemetry and remaining reels.

---

## 📁 System Architecture

```text
├── 0_Setup_Install_Requirements.bat  # 1-Click Dependency & Playwright Installer
├── 1_Login_Account_1.bat             # Isolated Chrome Login for Account 1
├── 1_Login_Account_2.bat             # Isolated Chrome Login for Account 2
├── 2_Post_Single_Reel.bat            # Dispatches the next unposted reel
├── 3_Start_Auto_Scheduler.bat        # Automated interval drip scheduler
├── 4_Check_Queue_Status.bat          # Real-time queue & account progress
├── HOW_TO_USE.txt                    # Quick-reference guide (Open in Notepad)
├── requirements.txt                  # Python dependencies
├── outputs/                          # Drop your .mp4 reels here
└── auto_poster/
    ├── accounts.json                 # Account profiles & proxy config
    ├── captions.json                 # Spintax hooks, CTAs, and hashtags
    ├── ai_caption.py                 # Dynamic caption & hashtag generator
    ├── browser_factory.py            # Anti-detect browser context launcher
    ├── database.py                   # Sequential queue manager
    ├── ghost_database.json           # Telemetry state
    ├── instagram_poster.py           # Core Playwright upload engine
    ├── post_single.py                # Single reel dispatch runner
    ├── scheduler_cli.py              # Drip loop runner
    └── status_cli.py                 # Telemetry monitor
```

---

## 🛡️ Features

- **Isolated Fingerprints:** Each account gets its own independent User Data directory (`profiles/insta_01`, `profiles/insta_02`), preventing cross-contamination or account linking by Instagram.
- **Auto 9:16 Ratio:** Automatically sets the 9:16 aspect ratio during reel upload.
- **Anti-Duplicate Captions:** Generates dynamic variations of hooks, episode labels, and rotating hashtags from `captions.json` to prevent spam triggers.
- **Zero Web Server Overhead:** Operates directly via native Windows `.bat` files for instant response and zero lag.
