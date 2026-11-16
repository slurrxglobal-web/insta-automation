import os
import sys
import json
import shutil
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "inputs"
OUTPUTS_DIR = BASE_DIR / "outputs"
CONFIGS_DIR = BASE_DIR / "configs"
CONFIG_FILE = CONFIGS_DIR / "settings.json"

for d in [INPUTS_DIR, OUTPUTS_DIR, CONFIGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def load_settings():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "clip_settings": {"default_duration_seconds": 75, "output_resolution": "1080x1920", "fps": 30},
        "anti_copyright": {"speed_multiplier": 1.025, "contrast_boost": 1.03, "saturation_boost": 1.05, "strip_metadata": True},
        "branding": {"telegram_handle": "@GhostTrafficHub", "cta_text": "Watch Full Video on Telegram"}
    }

def save_settings(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

class GhostTrafficStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("👻 Ghost Traffic Engine - Universal Media & Slicing Studio")
        self.geometry("820x780")
        self.minsize(760, 700)
        self.configure(bg="#0F172A")

        self.cfg = load_settings()
        self._apply_styles()
        self._build_ui()
        self.log("[+] Ghost Traffic Engine v1.2 Ready. All inputs/outputs mapped locally.")

        # Check FFmpeg and FFprobe system dependencies
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
            self.log("[✓] FFmpeg and FFprobe system dependencies verified.")
        except (FileNotFoundError, subprocess.SubprocessError):
            self.log("[!] WARNING: FFmpeg/FFprobe system PATH me nahi mila! Video slicing ke liye FFmpeg zaroori hai. (Download: https://ffmpeg.org/download.html)")

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#0F172A", foreground="#E2E8F0", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#1E293B", relief="flat")

    def _build_ui(self):
        # 1. Header Banner
        header = tk.Frame(self, bg="#1E293B", padx=20, pady=12)
        header.pack(fill="x", padx=15, pady=(15, 8))

        tk.Label(header, text="👻 GHOST TRAFFIC ENGINE", bg="#1E293B", fg="#38BDF8", font=("Segoe UI", 16, "bold")).pack(side="left")
        tk.Label(header, text="Universal Downloader (YT/Insta/TikTok) + 9:16 Anti-Copyright", bg="#1E293B", fg="#94A3B8", font=("Segoe UI", 9)).pack(side="left", padx=15, pady=4)

        container = tk.Frame(self, bg="#0F172A")
        container.pack(fill="both", expand=True, padx=15)

        # 2. Universal Ingestion Card (yt-dlp)
        ingest_box = tk.LabelFrame(container, text=" 1. Universal Media Ingestion (YouTube / Instagram Reel / TikTok) ", bg="#1E293B", fg="#F43F5E", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        ingest_box.pack(fill="x", pady=6)

        # URL Row
        r1 = tk.Frame(ingest_box, bg="#1E293B")
        r1.pack(fill="x", pady=3)
        tk.Label(r1, text="Media URL:", bg="#1E293B", fg="#CBD5E1", width=14, anchor="w").pack(side="left")
        self.url_entry = tk.Entry(r1, bg="#334155", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 10), relief="flat")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Format & Trimming Controls
        r2 = tk.Frame(ingest_box, bg="#1E293B")
        r2.pack(fill="x", pady=6)

        tk.Label(r2, text="Format:", bg="#1E293B", fg="#CBD5E1", width=14, anchor="w").pack(side="left")
        self.fmt_var = tk.StringVar(value="MP4 (Video)")
        fmt_cb = ttk.Combobox(r2, textvariable=self.fmt_var, values=["MP4 (Video)", "MP3 (Audio Only)"], state="readonly", width=15)
        fmt_cb.pack(side="left", padx=5)

        # Time range checkbox and inputs
        self.trim_var = tk.BooleanVar(value=False)
        trim_chk = tk.Checkbutton(r2, text="Trim Specific Section", variable=self.trim_var, bg="#1E293B", fg="#F8FAFC", selectcolor="#0F172A", activebackground="#1E293B", activeforeground="#38BDF8", command=self._toggle_trim_inputs)
        trim_chk.pack(side="left", padx=(15, 5))

        self.trim_frame = tk.Frame(r2, bg="#1E293B")
        self.trim_frame.pack(side="left", padx=5)

        tk.Label(self.trim_frame, text="Start:", bg="#1E293B", fg="#94A3B8").pack(side="left")
        self.start_entry = tk.Entry(self.trim_frame, width=7, bg="#334155", fg="#FFF", insertbackground="#FFF", font=("Segoe UI", 9), justify="center")
        self.start_entry.insert(0, "00:00")
        self.start_entry.pack(side="left", padx=3)

        tk.Label(self.trim_frame, text="End:", bg="#1E293B", fg="#94A3B8").pack(side="left", padx=(5, 0))
        self.end_entry = tk.Entry(self.trim_frame, width=7, bg="#334155", fg="#FFF", insertbackground="#FFF", font=("Segoe UI", 9), justify="center")
        self.end_entry.insert(0, "02:00")
        self.end_entry.pack(side="left", padx=3)
        self._toggle_trim_inputs()

        # Download Button
        dl_btn = tk.Button(r2, text="⬇ Fetch & Download", bg="#E11D48", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4, cursor="hand2", command=self.download_media)
        dl_btn.pack(side="right")

        # Local File Selector
        r3 = tk.Frame(ingest_box, bg="#1E293B")
        r3.pack(fill="x", pady=4)
        tk.Label(r3, text="Or Local File:", bg="#1E293B", fg="#CBD5E1", width=14, anchor="w").pack(side="left")
        self.local_lbl = tk.Label(r3, text="No manual file chosen (Engine auto-picks from inputs/)", bg="#334155", fg="#94A3B8", font=("Segoe UI", 9), anchor="w", padx=8, pady=4)
        self.local_lbl.pack(side="left", fill="x", expand=True, padx=5)
        browse_btn = tk.Button(r3, text="📁 Browse Video", bg="#2563EB", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=3, cursor="hand2", command=self.browse_local)
        browse_btn.pack(side="right")

        # 3. Branding & Slicing Configuration
        cfg_box = tk.LabelFrame(container, text=" 2. Slicing Parameters & Anti-Copyright Branding ", bg="#1E293B", fg="#38BDF8", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        cfg_box.pack(fill="x", pady=6)

        c1 = tk.Frame(cfg_box, bg="#1E293B")
        c1.pack(fill="x", pady=3)
        tk.Label(c1, text="Clip Length (sec):", bg="#1E293B", fg="#CBD5E1", width=16, anchor="w").pack(side="left")
        self.dur_var = tk.StringVar(value=str(self.cfg.get("clip_settings", {}).get("default_duration_seconds", 75)))
        dur_entry = tk.Entry(c1, textvariable=self.dur_var, bg="#334155", fg="#FFF", width=8, insertbackground="#FFF", font=("Segoe UI", 10), justify="center")
        dur_entry.pack(side="left", padx=5)

        tk.Label(c1, text="Telegram Channel:", bg="#1E293B", fg="#CBD5E1", width=16, anchor="w").pack(side="left", padx=(25, 0))
        self.tg_var = tk.StringVar(value=self.cfg.get("branding", {}).get("telegram_handle", "@GhostTrafficHub"))
        tg_entry = tk.Entry(c1, textvariable=self.tg_var, bg="#334155", fg="#FFF", insertbackground="#FFF", font=("Segoe UI", 10))
        tg_entry.pack(side="left", fill="x", expand=True, padx=5)

        c2 = tk.Frame(cfg_box, bg="#1E293B")
        c2.pack(fill="x", pady=3)
        tk.Label(c2, text="CTA Text:", bg="#1E293B", fg="#CBD5E1", width=16, anchor="w").pack(side="left")
        self.cta_var = tk.StringVar(value=self.cfg.get("branding", {}).get("cta_text", "Watch Full Video on Telegram"))
        cta_entry = tk.Entry(c2, textvariable=self.cta_var, bg="#334155", fg="#FFF", insertbackground="#FFF", font=("Segoe UI", 10))
        cta_entry.pack(side="left", fill="x", expand=True, padx=5)

        # 4. Action Execution Row
        act_row = tk.Frame(container, bg="#0F172A")
        act_row.pack(fill="x", pady=8)

        self.render_btn = tk.Button(act_row, text="⚡ START 9:16 ANTI-COPYRIGHT RENDER", bg="#059669", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", pady=10, cursor="hand2", command=self.start_render)
        self.render_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        open_btn = tk.Button(act_row, text="📂 Open Outputs", bg="#334155", fg="#F8FAFC", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=10, cursor="hand2", command=self.open_outputs)
        open_btn.pack(side="right")

        # 5. Live Console
        console_box = tk.LabelFrame(container, text=" Live Terminal Output ", bg="#1E293B", fg="#94A3B8", font=("Segoe UI", 9), padx=10, pady=6)
        console_box.pack(fill="both", expand=True, pady=(4, 12))

        self.console = scrolledtext.ScrolledText(console_box, bg="#020617", fg="#34D399", insertbackground="#FFF", font=("Consolas", 9), relief="flat")
        self.console.pack(fill="both", expand=True)

    def _toggle_trim_inputs(self):
        state = "normal" if self.trim_var.get() else "disabled"
        self.start_entry.config(state=state)
        self.end_entry.config(state=state)

    def log(self, text):
        self.console.insert("end", text + "\n")
        self.console.see("end")

    def browse_local(self):
        f = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4;*.mkv;*.mov;*.webm;*.avi")])
        if f:
            src = Path(f)
            dest = INPUTS_DIR / src.name
            try:
                shutil.copy2(src, dest)
                self.local_lbl.config(text=f"Loaded: {src.name}")
                self.log(f"[+] Local video copied into inputs/: {src.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not copy file: {e}")

    def download_media(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please paste a video or reel URL.")
            return

        fmt = self.fmt_var.get()
        is_audio = "MP3" in fmt
        is_trim = self.trim_var.get()
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()

        def task():
            self.log(f"\n[*] Fetching media from: {url}")
            out_template = str(INPUTS_DIR / "%(title)s.%(ext)s")

            cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings"]
            cmd += [
                "--extractor-args", "youtube:player_client=android,web",
                "--retries", "10",
                "--fragment-retries", "10"
            ]
            if is_audio:
                cmd += ["-x", "--audio-format", "mp3", "-o", str(INPUTS_DIR / "%(title)s.mp3")]
            else:
                cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", out_template]

            if is_trim and not is_audio:
                cmd += ["--download-sections", f"*{start}-{end}", "--force-keyframes-at-cuts"]
                self.log(f"[*] Trimming timeline from {start} to {end}")

            cmd.append(url)

            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                for line in proc.stdout:
                    l = line.strip()
                    if l:
                        self.log("  " + l)
                proc.wait()
                if proc.returncode == 0:
                    self.log("[✓] Media downloaded and saved into inputs/ folder!")
                    self.url_entry.delete(0, "end")
                    messagebox.showinfo("Success", "Media downloaded successfully into inputs/ folder!")
                else:
                    self.log(f"[!] Downloader finished with code: {proc.returncode}")
            except Exception as e:
                self.log(f"[!] Download error: {e}")

        threading.Thread(target=task, daemon=True).start()

    def start_render(self):
        try:
            dur = int(self.dur_var.get())
        except ValueError:
            dur = 75

        self.cfg["clip_settings"]["default_duration_seconds"] = dur
        self.cfg["branding"]["telegram_handle"] = self.tg_var.get().strip()
        self.cfg["branding"]["cta_text"] = self.cta_var.get().strip()
        save_settings(self.cfg)

        self.render_btn.config(state="disabled", text="⏳ PROCESSING REELS (PLEASE WAIT)...", bg="#D97706")

        def task():
            self.log("\n==============================================")
            self.log("[*] STARTING 9:16 ANTI-COPYRIGHT RENDER ENGINE...")
            self.log("==============================================")
            try:
                proc = subprocess.Popen([sys.executable, str(BASE_DIR / "engine.py")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                for line in proc.stdout:
                    l = line.strip()
                    if l:
                        self.log("  " + l)
                proc.wait()
                if proc.returncode == 0:
                    self.log("\n[✓] ALL REELS SUCCESSFULLY GENERATED!")
                    messagebox.showinfo("Complete", "All reels are ready in outputs/ folder!")
                else:
                    self.log(f"\n[!] Render process ended with code: {proc.returncode}")
            except Exception as e:
                self.log(f"[!] Pipeline error: {e}")
            finally:
                self.render_btn.config(state="normal", text="⚡ START 9:16 ANTI-COPYRIGHT RENDER", bg="#059669")

        threading.Thread(target=task, daemon=True).start()

    def open_outputs(self):
        os.startfile(str(OUTPUTS_DIR))

if __name__ == "__main__":
    app = GhostTrafficStudio()
    app.mainloop()
