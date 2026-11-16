import os
import sys
import json
import time
import queue
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

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

OUTPUTS_DIR = get_outputs_dir()

class AutoPosterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("👻 Ghost Traffic - Auto Poster Studio v1.0")
        self.geometry("980x760")
        self.minsize(920, 700)
        self.configure(bg="#0B0F19")

        self.log_queue = queue.Queue()
        self.scheduler_running = False
        self.scheduler_thread = None

        self._setup_styles()
        self._build_ui()
        self._refresh_all_data()

        # Log polling loop
        self.after(100, self._process_log_queue)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#0B0F19", foreground="#E2E8F0", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#1E293B")
        style.configure("TCombobox", fieldbackground="#1E293B", background="#334155", foreground="#FFFFFF")

    def log(self, message, tag=None):
        self.log_queue.put((message, tag))

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg, tag = self.log_queue.get_nowait()
            self.console.config(state="normal")
            timestamp = time.strftime("[%H:%M:%S] ")
            self.console.insert("end", timestamp, "dim")
            if tag:
                self.console.insert("end", f"{msg}\n", tag)
            else:
                if "[✓]" in msg or "SUCCESS" in msg or "🎉" in msg:
                    self.console.insert("end", f"{msg}\n", "success")
                elif "[!]" in msg or "ERROR" in msg or "Fail" in msg:
                    self.console.insert("end", f"{msg}\n", "error")
                elif "[*]" in msg:
                    self.console.insert("end", f"{msg}\n", "info")
                else:
                    self.console.insert("end", f"{msg}\n")
            self.console.see("end")
            self.console.config(state="disabled")
        self.after(100, self._process_log_queue)

    def _build_ui(self):
        # 1. Header Banner
        header = tk.Frame(self, bg="#111827", padx=20, pady=12, highlightbackground="#1F2937", highlightthickness=1)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title_box = tk.Frame(header, bg="#111827")
        title_box.pack(side="left")

        tk.Label(title_box, text="👻 GHOST TRAFFIC AUTO-POSTER", bg="#111827", fg="#38BDF8", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Multi-Account Cloud Syndication & Reels Automation", bg="#111827", fg="#9CA3AF", font=("Segoe UI", 9)).pack(anchor="w")

        # Stats Badge
        self.stats_label = tk.Label(header, text="Loading clips...", bg="#1F2937", fg="#10B981", font=("Segoe UI", 10, "bold"), padx=12, pady=6)
        self.stats_label.pack(side="right")

        # Main Body: 2 Columns
        body = tk.Frame(self, bg="#0B0F19")
        body.pack(fill="both", expand=True, padx=15, pady=5)

        left_col = tk.Frame(body, bg="#0B0F19", width=420)
        left_col.pack(side="left", fill="both", padx=(0, 8), expand=False)

        right_col = tk.Frame(body, bg="#0B0F19")
        right_col.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # ==========================================
        # LEFT COLUMN: ACCOUNTS MANAGEMENT
        # ==========================================
        acc_card = tk.LabelFrame(left_col, text=" 👤 Accounts Manager ", bg="#111827", fg="#F43F5E", font=("Segoe UI", 10, "bold"), padx=12, pady=10, highlightbackground="#1F2937", highlightthickness=1)
        acc_card.pack(fill="x", pady=(0, 10))

        # Account Listbox
        self.acc_listbox = tk.Listbox(acc_card, bg="#1F2937", fg="#F9FAFB", selectbackground="#38BDF8", selectforeground="#0B0F19", font=("Segoe UI", 10), height=5, relief="flat", highlightthickness=0)
        self.acc_listbox.pack(fill="x", pady=5)
        self.acc_listbox.bind("<<ListboxSelect>>", self._on_account_selected)

        # Account Action Buttons
        btn_row1 = tk.Frame(acc_card, bg="#111827")
        btn_row1.pack(fill="x", pady=4)

        self.btn_login = tk.Button(btn_row1, text="🔑 1-Click Login / Connect", bg="#0284C7", fg="#FFFFFF", activebackground="#0369A1", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, cursor="hand2", command=self._action_login)
        self.btn_login.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_add = tk.Button(btn_row1, text="➕ Add Account", bg="#374151", fg="#FFFFFF", activebackground="#4B5563", font=("Segoe UI", 9), relief="flat", padx=8, pady=5, cursor="hand2", command=self._action_add_account)
        btn_add.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Scheduler Card
        sched_card = tk.LabelFrame(left_col, text=" ⏱️ Automated Drip Scheduler ", bg="#111827", fg="#38BDF8", font=("Segoe UI", 10, "bold"), padx=12, pady=10, highlightbackground="#1F2937", highlightthickness=1)
        sched_card.pack(fill="x", pady=(0, 10))

        r_int = tk.Frame(sched_card, bg="#111827")
        r_int.pack(fill="x", pady=3)
        tk.Label(r_int, text="Interval between posts:", bg="#111827", fg="#E5E7EB", font=("Segoe UI", 9)).pack(side="left")
        self.interval_entry = tk.Entry(r_int, width=5, bg="#1F2937", fg="#FFFFFF", insertbackground="#FFF", font=("Segoe UI", 9, "bold"), justify="center", relief="flat")
        self.interval_entry.insert(0, "60")
        self.interval_entry.pack(side="left", padx=5)
        tk.Label(r_int, text="minutes", bg="#111827", fg="#9CA3AF", font=("Segoe UI", 9)).pack(side="left")

        self.btn_scheduler = tk.Button(sched_card, text="▶️ Start Drip Auto-Scheduler", bg="#10B981", fg="#FFFFFF", activebackground="#059669", font=("Segoe UI", 10, "bold"), relief="flat", pady=6, cursor="hand2", command=self._toggle_scheduler)
        self.btn_scheduler.pack(fill="x", pady=6)

        # ==========================================
        # RIGHT COLUMN: REEL SELECTOR & CAPTION
        # ==========================================
        reel_card = tk.LabelFrame(right_col, text=" 🎬 Next Reel to Post ", bg="#111827", fg="#A855F7", font=("Segoe UI", 10, "bold"), padx=12, pady=10, highlightbackground="#1F2937", highlightthickness=1)
        reel_card.pack(fill="x", pady=(0, 10))

        self.reel_combo = ttk.Combobox(reel_card, state="readonly", font=("Segoe UI", 9))
        self.reel_combo.pack(fill="x", pady=4)

        # Caption editor
        tk.Label(reel_card, text="Telegram CTA & Bio Hook:", bg="#111827", fg="#9CA3AF", font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 1))
        self.cta_entry = tk.Entry(reel_card, bg="#1F2937", fg="#FFFFFF", insertbackground="#FFF", font=("Segoe UI", 9), relief="flat")
        self.cta_entry.pack(fill="x", pady=2)

        # Controls & Post Button
        action_row = tk.Frame(reel_card, bg="#111827")
        action_row.pack(fill="x", pady=8)

        self.show_browser_var = tk.BooleanVar(value=True)
        chk_browser = tk.Checkbutton(action_row, text="Show live browser window while posting", variable=self.show_browser_var, bg="#111827", fg="#D1D5DB", selectcolor="#0B0F19", activebackground="#111827", activeforeground="#38BDF8", font=("Segoe UI", 9))
        chk_browser.pack(side="left")

        self.btn_post_now = tk.Button(reel_card, text="🚀 POST SELECTED REEL NOW", bg="#F43F5E", fg="#FFFFFF", activebackground="#E11D48", font=("Segoe UI", 11, "bold"), relief="flat", pady=8, cursor="hand2", command=self._action_post_now)
        self.btn_post_now.pack(fill="x", pady=(4, 2))

        # ==========================================
        # BOTTOM: REAL-TIME CONSOLE
        # ==========================================
        console_frame = tk.LabelFrame(self, text=" 💻 Live Activity Terminal ", bg="#111827", fg="#38BDF8", font=("Segoe UI", 9, "bold"), padx=10, pady=6, highlightbackground="#1F2937", highlightthickness=1)
        console_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.console = scrolledtext.ScrolledText(console_frame, bg="#030712", fg="#F3F4F6", font=("Consolas", 9), insertbackground="#FFF", relief="flat", state="disabled", wrap="word")
        self.console.pack(fill="both", expand=True)

        self.console.tag_config("success", foreground="#34D399")
        self.console.tag_config("error", foreground="#F87171")
        self.console.tag_config("info", foreground="#60A5FA")
        self.console.tag_config("dim", foreground="#6B7280")

        self.log("[+] Ghost Traffic Auto-Poster GUI Ready.")
        self.log(f"[*] Slicer outputs detected at: {OUTPUTS_DIR}")

    def _refresh_all_data(self):
        # Refresh Accounts
        accounts = load_json(ACCOUNTS_FILE, [])
        self.acc_listbox.delete(0, "end")
        for acc in accounts:
            label = f"{acc['id']} - {acc.get('name', 'Account')} [{acc.get('platform')}]"
            self.acc_listbox.insert("end", label)

        if accounts:
            self.acc_listbox.select_set(0)

        # Refresh Captions
        captions = load_json(CAPTIONS_FILE, {})
        default_cta = captions.get("default_cta", "👉 Watch full uncut video on Telegram: @GhostTrafficHub (Link in Bio)")
        self.cta_entry.delete(0, "end")
        self.cta_entry.insert(0, default_cta)

        # Refresh Clips
        clips = sorted(list(OUTPUTS_DIR.glob("*.mp4")), key=lambda p: p.name)
        total_posted = db.db.get("stats", {}).get("total_posted", 0)
        self.reel_combo["values"] = [c.name for c in clips]
        if clips:
            self.reel_combo.current(0)
            self.stats_label.config(text=f"🎬 {len(clips)} Total Clips Found | {total_posted} Posts Logged")
        else:
            self.stats_label.config(text="⚠️ 0 Clips Found in slicer/outputs", fg="#F87171")

    def _on_account_selected(self, event=None):
        pass

    def _get_selected_account(self):
        accounts = load_json(ACCOUNTS_FILE, [])
        sel = self.acc_listbox.curselection()
        if not sel or sel[0] >= len(accounts):
            return None
        return accounts[sel[0]]

    def _action_login(self):
        acc = self._get_selected_account()
        if not acc:
            messagebox.showwarning("No Account Selected", "Pehle list me se account select karo!")
            return

        def run_login_worker():
            self.btn_login.config(state="disabled", text="⏳ Browser Open...")
            self.log(f"[*] Launching visible browser for {acc['id']} login...")
            try:
                from browser_factory import get_browser_context
                from playwright.sync_api import sync_playwright

                profile_subpath = acc.get("profile_dir", f"profiles/{acc['id']}")
                with sync_playwright() as p:
                    context = get_browser_context(
                        p,
                        profile_subpath=profile_subpath,
                        headless=False,
                        proxy_dict=acc.get("proxy")
                    )
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto("https://www.instagram.com/")
                    
                    self.log(f"[👉] Browser khul gaya hai! Instagram login karo aur OTP complete karo.")
                    self.log(f"[👉] Login hone ke baad browser ko manually CLOSE kar dena.")
                    
                    # Wait until user closes the browser or page
                    try:
                        page.wait_for_timeout(600000) # up to 10 mins
                    except Exception:
                        pass
                    
                    context.close()
                    self.log(f"[✓] Login session saved permanently for {acc['id']}!")
            except Exception as e:
                self.log(f"[!] Login error: {e}")
            finally:
                self.btn_login.config(state="normal", text="🔑 1-Click Login / Connect")

        threading.Thread(target=run_login_worker, daemon=True).start()

    def _action_add_account(self):
        # Quick popup
        top = tk.Toplevel(self)
        top.title("Add New Account")
        top.geometry("340x220")
        top.configure(bg="#111827")
        top.grab_set()

        tk.Label(top, text="Account ID (e.g. insta_03):", bg="#111827", fg="#FFF").pack(pady=(12, 2))
        e_id = tk.Entry(top, bg="#1F2937", fg="#FFF", insertbackground="#FFF")
        e_id.pack(fill="x", padx=20, pady=2)

        tk.Label(top, text="Friendly Name (e.g. Cinema Hub):", bg="#111827", fg="#FFF").pack(pady=(8, 2))
        e_name = tk.Entry(top, bg="#1F2937", fg="#FFF", insertbackground="#FFF")
        e_name.pack(fill="x", padx=20, pady=2)

        def save_new():
            new_id = e_id.get().strip()
            new_name = e_name.get().strip()
            if not new_id:
                return
            accounts = load_json(ACCOUNTS_FILE, [])
            accounts.append({
                "id": new_id,
                "platform": "instagram",
                "name": new_name or new_id,
                "profile_dir": f"profiles/{new_id}",
                "proxy": None,
                "enabled": True
            })
            save_json(ACCOUNTS_FILE, accounts)
            self._refresh_all_data()
            self.log(f"[+] Added new account: {new_id}")
            top.destroy()

        tk.Button(top, text="Save Account", bg="#10B981", fg="#FFF", relief="flat", font=("Segoe UI", 9, "bold"), command=save_new).pack(pady=15)

    def _action_post_now(self):
        acc = self._get_selected_account()
        if not acc:
            messagebox.showwarning("Select Account", "Pehle account select karo!")
            return

        selected_clip_name = self.reel_combo.get().strip()
        if not selected_clip_name:
            messagebox.showwarning("Select Clip", "Outputs me koi clip nahi mili!")
            return

        clip_path = OUTPUTS_DIR / selected_clip_name
        if not clip_path.exists():
            messagebox.showerror("Error", f"File nahi mili: {clip_path}")
            return

        headless = not self.show_browser_var.get()

        def post_worker():
            self.btn_post_now.config(state="disabled", text="⏳ Posting Reel...", bg="#374151")
            self.log(f"\n[*] Starting Instant Post for {acc['id']}...")
            self.log(f"[*] Video: {selected_clip_name}")

            try:
                from instagram_poster import post_reel_to_instagram
                success = post_reel_to_instagram(acc, clip_path, headless=headless)
                if success:
                    self.log(f"[🎉] SUCCESS: Reel successfully posted on Instagram!")
                    self._refresh_all_data()
                else:
                    self.log(f"[!] Post failed or timed out. Check debug_screenshots folder.")
            except Exception as e:
                self.log(f"[!] Error: {e}")
            finally:
                self.btn_post_now.config(state="normal", text="🚀 POST SELECTED REEL NOW", bg="#F43F5E")

        threading.Thread(target=post_worker, daemon=True).start()

    def _toggle_scheduler(self):
        if not self.scheduler_running:
            self.scheduler_running = True
            self.btn_scheduler.config(text="⏹️ Stop Scheduler", bg="#EF4444")
            try:
                interval_minutes = int(self.interval_entry.get().strip())
            except ValueError:
                interval_minutes = 60

            self.log(f"[▶️] Scheduler Started! Posting every {interval_minutes} minutes.")

            def scheduler_loop():
                while self.scheduler_running:
                    accounts = [a for a in load_json(ACCOUNTS_FILE, []) if a.get("enabled", True)]
                    from run_poster import get_unposted_clips_for_account
                    from instagram_poster import post_reel_to_instagram

                    for acc in accounts:
                        if not self.scheduler_running:
                            break
                        unposted = get_unposted_clips_for_account(acc["id"])
                        if not unposted:
                            self.log(f"[-] No unposted clips remaining for {acc['id']}.")
                            continue
                        clip = unposted[0]
                        self.log(f"\n[⏱️ Scheduler] Auto posting to {acc['id']}: {clip.name}")
                        headless = not self.show_browser_var.get()
                        post_reel_to_instagram(acc, clip, headless=headless)
                        time.sleep(30)

                    # Sleep interval
                    for _ in range(interval_minutes * 60):
                        if not self.scheduler_running:
                            break
                        time.sleep(1)

            self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
            self.scheduler_thread.start()
        else:
            self.scheduler_running = False
            self.btn_scheduler.config(text="▶️ Start Drip Auto-Scheduler", bg="#10B981")
            self.log("[⏹️] Scheduler Stopped.")

if __name__ == "__main__":
    app = AutoPosterGUI()
    app.mainloop()
