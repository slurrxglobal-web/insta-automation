import os
import sys
import json
import shutil
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, Response

BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "inputs"
OUTPUTS_DIR = BASE_DIR / "outputs"
CONFIGS_DIR = BASE_DIR / "configs"
CONFIG_FILE = CONFIGS_DIR / "settings.json"

for d in [INPUTS_DIR, OUTPUTS_DIR, CONFIGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
logs = ["[+] Ghost Traffic Web Studio initialized on Localhost."]

def add_log(msg):
    logs.append(msg)
    if len(logs) > 300:
        logs.pop(0)

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ghost Traffic Engine - Studio</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B0F19; color: #F1F5F9; font-family: ui-sans-serif, system-ui, sans-serif; }
        /* Terminal custom scrollbar */
        #terminal::-webkit-scrollbar { width: 6px; }
        #terminal::-webkit-scrollbar-track { background: rgba(0,0,0,0.4); border-radius: 4px; }
        #terminal::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        #terminal::-webkit-scrollbar-thumb:hover { background: #475569; }
        #outputList::-webkit-scrollbar { width: 6px; }
        #outputList::-webkit-scrollbar-track { background: rgba(0,0,0,0.4); border-radius: 4px; }
        #outputList::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    </style>
</head>
<body class="p-6 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl mb-6">
        <div>
            <h1 class="text-2xl font-black tracking-wide text-sky-400 flex items-center gap-2">
                👻 GHOST TRAFFIC ENGINE
            </h1>
            <p class="text-xs text-slate-400 mt-1">Universal Ingestion (YT, Insta Reels, TikTok) + 9:16 Anti-Copyright Studio</p>
        </div>
        <div class="flex items-center gap-3">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Localhost Live :5000
            </span>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <!-- Left: Ingestion & Settings -->
        <div class="space-y-6">
            <!-- 1. Universal Downloader Card -->
            <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
                <h2 class="text-sm font-bold uppercase tracking-wider text-rose-400 mb-4 flex items-center gap-2">
                    ⬇ 1. Universal Media Downloader
                </h2>
                
                <div class="space-y-3">
                    <div>
                        <label class="text-xs font-medium text-slate-300">Media URL (YouTube / Insta Reel / TikTok / X):</label>
                        <input id="mediaUrl" type="text" placeholder="https://www.youtube.com/watch?v=... or Insta Reel" 
                                class="mt-1 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-rose-500">
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs font-medium text-slate-300">Download Format:</label>
                            <select id="downloadFmt" class="mt-1 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none">
                                <option value="mp4">MP4 (Video HD)</option>
                                <option value="mp3">MP3 (Audio Only)</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-medium text-slate-300">Time Trimming:</label>
                            <div class="flex items-center gap-1 mt-1">
                                <input id="trimStart" type="text" placeholder="00:00" class="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-2 py-2 text-xs text-center text-white">
                                <span class="text-slate-500 text-xs">to</span>
                                <input id="trimEnd" type="text" placeholder="02:00" class="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-2 py-2 text-xs text-center text-white">
                            </div>
                        </div>
                    </div>

                    <button onclick="downloadMedia()" id="dlBtn" class="w-full bg-gradient-to-r from-rose-500 to-red-600 hover:from-rose-600 hover:to-red-700 text-white font-bold py-2.5 rounded-lg text-sm transition shadow-md">
                        Fetch & Download to Inputs
                    </button>
                </div>
            </div>

            <!-- 2. Slicing & Branding Parameters -->
            <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
                <h2 class="text-sm font-bold uppercase tracking-wider text-sky-400 mb-4 flex items-center gap-2">
                    ⚙ 2. Slicing & Branding Setup
                </h2>
                
                <div class="space-y-3">
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs font-medium text-slate-300">Clip Duration (sec):</label>
                            <input id="clipDuration" type="number" value="{{ cfg.clip_settings.default_duration_seconds }}" 
                                   class="mt-1 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                        <div>
                            <label class="text-xs font-medium text-slate-300">Telegram Channel:</label>
                            <input id="tgHandle" type="text" value="{{ cfg.branding.telegram_handle }}" 
                                   class="mt-1 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                    </div>

                    <div>
                        <label class="text-xs font-medium text-slate-300">Call-To-Action (Bottom Banner):</label>
                        <input id="ctaText" type="text" value="{{ cfg.branding.cta_text }}" 
                                class="mt-1 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                    </div>

                    <button onclick="startRender()" id="renderBtn" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg text-sm transition shadow-lg mt-2">
                        ⚡ START 9:16 ANTI-COPYRIGHT RENDER
                    </button>
                </div>
            </div>
        </div>

        <!-- Right: Real-time Console & Outputs -->
        <div class="space-y-6">
            <!-- Console -->
            <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
                <div class="flex items-center justify-between mb-3">
                    <h2 class="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                        📟 Live Processing Terminal
                    </h2>
                    <button onclick="clearLogs()" class="text-xs text-slate-500 hover:text-slate-300 transition">Clear</button>
                </div>
                <div id="terminal" class="bg-black/90 rounded-xl p-3.5 font-mono text-xs text-emerald-400 h-[360px] max-h-[360px] overflow-y-auto space-y-1 border border-slate-800/80 break-words whitespace-pre-wrap select-text">
                </div>
            </div>

            <!-- Ready Outputs Quick Links -->
            <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
                <div class="flex items-center justify-between mb-3">
                    <h2 class="text-sm font-bold uppercase tracking-wider text-indigo-400">
                        🎬 Generated Clips (<span id="outputCount">0</span>)
                    </h2>
                    <button onclick="refreshOutputs()" class="text-xs text-slate-400 hover:text-white transition">↻ Refresh</button>
                </div>
                <div id="outputList" class="space-y-2 max-h-36 overflow-y-auto text-xs">
                    <!-- Loaded dynamically -->
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                const term = document.getElementById('terminal');
                term.innerHTML = data.logs.map(l => `<div>${l}</div>`).join('');
                term.scrollTop = term.scrollHeight;
            } catch (e) {}
        }
        setInterval(fetchLogs, 1500);

        async function refreshOutputs() {
            try {
                const res = await fetch('/api/outputs');
                const data = await res.json();
                document.getElementById('outputCount').innerText = data.files.length;
                const list = document.getElementById('outputList');
                if (data.files.length === 0) {
                    list.innerHTML = '<div class="text-slate-500 italic">No rendered clips yet.</div>';
                } else {
                    list.innerHTML = data.files.map(f => `
                        <div class="flex items-center justify-between bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-700/60">
                            <span class="text-slate-200 font-mono">${f.name}</span>
                            <span class="text-slate-400 text-[11px]">${f.size}</span>
                        </div>
                    `).join('');
                }
            } catch (e) {}
        }
        refreshOutputs();

        async function downloadMedia() {
            const url = document.getElementById('mediaUrl').value.trim();
            if (!url) { alert('Please enter a URL!'); return; }
            const fmt = document.getElementById('downloadFmt').value;
            const start = document.getElementById('trimStart').value.trim();
            const end = document.getElementById('trimEnd').value.trim();

            const btn = document.getElementById('dlBtn');
            btn.disabled = true;
            btn.innerText = 'Downloading...';

            await fetch('/api/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url, format: fmt, start, end })
            });

            btn.disabled = false;
            btn.innerText = 'Fetch & Download to Inputs';
            document.getElementById('mediaUrl').value = '';
        }

        async function startRender() {
            const dur = document.getElementById('clipDuration').value;
            const tg = document.getElementById('tgHandle').value;
            const cta = document.getElementById('ctaText').value;

            const btn = document.getElementById('renderBtn');
            btn.disabled = true;
            btn.innerText = '⏳ Rendering 9:16 Clips (Please wait)...';

            await fetch('/api/render', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ duration: dur, tg_handle: tg, cta_text: cta })
            });

            btn.disabled = false;
            btn.innerText = '⚡ START 9:16 ANTI-COPYRIGHT RENDER';
            refreshOutputs();
        }

        async function clearLogs() {
            await fetch('/api/clear-logs', { method: 'POST' });
            fetchLogs();
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    cfg = load_settings()
    return render_template_string(HTML_TEMPLATE, cfg=cfg)

@app.route("/api/logs")
def get_logs():
    return jsonify({"logs": logs})

@app.route("/api/clear-logs", methods=["POST"])
def clear_logs():
    global logs
    logs = ["[+] Logs cleared."]
    return jsonify({"status": "ok"})

@app.route("/api/outputs")
def get_outputs():
    files = []
    if OUTPUTS_DIR.exists():
        for f in sorted(OUTPUTS_DIR.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True):
            sz_mb = f.stat().st_size / (1024 * 1024)
            files.append({"name": f.name, "size": f"{sz_mb:.1f} MB"})
    return jsonify({"files": files})

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.json or {}
    url = data.get("url", "").strip()
    fmt = data.get("format", "mp4")
    start = data.get("start", "").strip()
    end = data.get("end", "").strip()

    def run_dl():
        add_log(f"[*] Starting download for: {url}")
        cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings"]
        cmd += [
            "--extractor-args", "youtube:player_client=android,web",
            "--retries", "10",
            "--fragment-retries", "10"
        ]
        if fmt == "mp3":
            cmd += ["-x", "--audio-format", "mp3", "-o", str(INPUTS_DIR / "%(title)s.mp3")]
        else:
            cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", str(INPUTS_DIR / "%(title)s.%(ext)s")]

        if start and end and fmt != "mp3":
            cmd += ["--download-sections", f"*{start}-{end}", "--force-keyframes-at-cuts"]
            add_log(f"[*] Timeline segment: {start} -> {end}")

        cmd.append(url)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                l = line.strip()
                if l:
                    add_log("  " + l)
            proc.wait()
            if proc.returncode == 0:
                add_log("[✓] Media downloaded into inputs/ folder!")
            else:
                add_log(f"[!] Downloader finished with code: {proc.returncode}")
        except Exception as e:
            add_log(f"[!] Error: {e}")

    threading.Thread(target=run_dl, daemon=True).start()
    return jsonify({"status": "started"})

@app.route("/api/render", methods=["POST"])
def api_render():
    data = request.json or {}
    cfg = load_settings()
    try:
        dur = int(data.get("duration", 75))
    except ValueError:
        dur = 75

    cfg["clip_settings"]["default_duration_seconds"] = dur
    if "tg_handle" in data:
        cfg["branding"]["telegram_handle"] = data["tg_handle"].strip()
    if "cta_text" in data:
        cfg["branding"]["cta_text"] = data["cta_text"].strip()
    save_settings(cfg)

    def run_render():
        add_log("\n==============================================")
        add_log("[*] STARTING 9:16 ANTI-COPYRIGHT RENDER ENGINE...")
        add_log("==============================================")
        try:
            proc = subprocess.Popen([sys.executable, str(BASE_DIR / "engine.py")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                l = line.strip()
                if l:
                    add_log("  " + l)
            proc.wait()
            if proc.returncode == 0:
                add_log("\n[✓] ALL REELS SUCCESSFULLY RENDERED!")
            else:
                add_log(f"\n[!] Render process ended with code: {proc.returncode}")
        except Exception as e:
            add_log(f"[!] Render error: {e}")

    threading.Thread(target=run_render, daemon=True).start()
    return jsonify({"status": "started"})

if __name__ == "__main__":
    print("[*] Starting Ghost Traffic Web Studio on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
