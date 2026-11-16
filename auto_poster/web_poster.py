import os
import sys
import json
import time
import hashlib
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

from database import db
from ai_caption import generate_ai_caption
from browser_factory import get_profile_fingerprint, launch_visible_chrome, cleanup_stale_locks
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"

app = Flask(__name__)
logs = [
    "[SYSTEM] Ghost Panel v3.5 Operational // Interactive Engine Ready",
    "[STORAGE] 69 Sequenced Video Payloads Loaded in Pipeline",
    "[READY] Ready to launch anti-detect browser profiles."
]

scheduler_state = {
    "running": False,
    "interval_min": 60,
    "thread": None
}

# Active browser sessions: { account_id: { "proc": Popen, "port": int, "platform": str, "stop_event": Event } }
active_sessions = {}
session_lock = threading.Lock()

PLATFORM_URLS = {
    "instagram":  "https://www.instagram.com/",
    "facebook":   "https://www.facebook.com/",
    "twitter":    "https://x.com/login",
    "tiktok":     "https://www.tiktok.com/login",
    "snapchat":   "https://my.snapchat.com/",
    "pinterest":  "https://www.pinterest.com/login/",
    "youtube":    "https://studio.youtube.com/",
}

PLATFORM_META = {
    "instagram":  {"label": "Instagram", "bg": "linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045)", "short": "IG"},
    "facebook":   {"label": "Facebook", "bg": "#1877f2", "short": "FB"},
    "twitter":    {"label": "X / Twitter", "bg": "#000000", "short": "𝕏"},
    "tiktok":     {"label": "TikTok", "bg": "#000000", "short": "TT"},
    "snapchat":   {"label": "Snapchat", "bg": "#fffc00", "color": "#000", "short": "SC"},
    "pinterest":  {"label": "Pinterest", "bg": "#e60023", "short": "PT"},
    "youtube":    {"label": "YouTube", "bg": "#ff0000", "short": "YT"},
}

def add_log(msg):
    logs.append(msg)
    if len(logs) > 350:
        logs.pop(0)

def load_json(file_path, default=None):
    if default is None:
        default = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def check_login_status(account_dict):
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
        return row is not None
    except Exception:
        return False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ghost Panel // Anti-Detect Control Studio</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Orbitron:wght@800;900&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #080C14;
            color: #E2E8F0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-height: 100vh;
        }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .font-logo { font-family: 'Orbitron', sans-serif; }

        .card {
            background: #0E1422;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            border-radius: 12px;
        }
        .card-inner {
            background: #090E1A;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3B82F6, #2563EB);
            color: white;
            transition: all 0.2s ease;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #60A5FA, #3B82F6);
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        }

        .btn-launch {
            background: #10B981;
            color: #FFFFFF;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .btn-launch:hover {
            background: #059669;
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
        }

        .btn-danger {
            background: #EF4444;
            color: white;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .btn-danger:hover {
            background: #DC2626;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
        }

        .btn-dispatch {
            background: linear-gradient(135deg, #EC4899, #F43F5E, #E11D48);
            color: white;
            font-weight: 700;
            transition: all 0.2s ease;
        }
        .btn-dispatch:hover {
            background: linear-gradient(135deg, #F472B6, #FB7185, #F43F5E);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(225, 29, 72, 0.45);
        }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #080C14; }
        ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
    </style>
</head>
<body class="p-4 md:p-6 max-w-7xl mx-auto space-y-6">

    <!-- TOP HEADER -->
    <header class="card p-5 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <span class="font-logo font-black text-black text-lg">G</span>
            </div>
            <div>
                <div class="flex items-center gap-2.5">
                    <h1 class="text-xl font-bold tracking-tight text-white">Ghost Panel</h1>
                    <span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">v3.5 PRO</span>
                    <span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        ONLINE :5050
                    </span>
                </div>
                <p class="text-xs text-slate-400 mt-0.5">Anti-Detect Multi-Account Browser Manager & Automated Reel Syndication</p>
            </div>
        </div>

        <div class="flex items-center gap-6 text-xs">
            <div class="bg-[#090E1A] px-3.5 py-2 rounded-lg border border-slate-800">
                <div class="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Video Pipeline</div>
                <div id="statTotalClips" class="text-white font-bold text-sm mt-0.5">69 Clips Loaded</div>
            </div>
            <div class="bg-[#090E1A] px-3.5 py-2 rounded-lg border border-slate-800">
                <div class="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Active Browser</div>
                <div id="statActiveBrowsers" class="text-emerald-400 font-bold text-sm mt-0.5">0 Windows</div>
            </div>
        </div>
    </header>

    <!-- STEP GUIDE BANNER -->
    <div class="card p-4 bg-blue-950/20 border border-blue-500/20 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div class="flex items-center gap-2 text-blue-300 font-bold uppercase tracking-wider">
            <span>💡 Quick Workflow:</span>
        </div>
        <div class="flex flex-wrap items-center gap-4 text-slate-300">
            <div><strong class="text-white">1.</strong> Click <span class="text-emerald-400 font-semibold">"▶ Launch Browser"</span> &rarr; Login to Instagram in Chrome &rarr; Close window.</div>
            <div><strong class="text-white">2.</strong> Status auto-updates to <span class="text-emerald-400 font-semibold">● Connected</span>.</div>
            <div><strong class="text-white">3.</strong> Click <span class="text-rose-400 font-semibold">"🚀 DISPATCH REEL"</span> to automatically post!</div>
        </div>
    </div>

    <!-- ACTIVE BROWSER ALERT BANNER -->
    <div id="activeBrowserBanner" class="hidden card p-4 my-2 border-l-4 border-l-emerald-500 bg-emerald-950/20 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full bg-emerald-400 animate-ping"></div>
            <div>
                <div class="text-sm font-semibold text-emerald-300">
                    Browser Window Active for: <span id="bannerAccountName" class="font-bold underline text-white">Node</span>
                </div>
                <div class="text-xs text-slate-400 mt-0.5">
                    Google Chrome is running on your screen with this profile. You can log in, click, and interact freely.
                </div>
            </div>
        </div>
        <button onclick="stopActiveBrowser()" class="px-3 py-1.5 text-xs btn-danger rounded-lg flex items-center gap-1.5">
            <span>⏹</span> Close Browser
        </button>
    </div>

    <!-- MAIN TWO-COLUMN DASHBOARD -->
    <main class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

        <!-- LEFT COLUMN: PROFILES & SCHEDULER (5 COLS) -->
        <div class="lg:col-span-5 space-y-6">

            <!-- 1. ANTI-DETECT BROWSER PROFILES -->
            <section class="card p-5 space-y-4">
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                        <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                            <span>1.</span> Anti-Detect Profiles
                        </h2>
                        <p class="text-[11px] text-slate-400">Click "Launch Browser" to open isolated Chrome window</p>
                    </div>
                    <button onclick="openAddAccountModal()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition flex items-center gap-1">
                        <span>+</span> Add Profile
                    </button>
                </div>

                <div id="accountsList" class="space-y-3">
                    <div class="text-center py-8 text-xs text-slate-500 font-mono">Loading profiles...</div>
                </div>
            </section>

            <!-- 2. DRIP AUTO SCHEDULER -->
            <section class="card p-5 space-y-4">
                <div class="border-b border-slate-800 pb-3">
                    <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        <span>2.</span> Autonomous Drip Scheduler
                    </h2>
                    <p class="text-[11px] text-slate-400">Sequentially dispatches next unposted reel per account</p>
                </div>

                <div class="card-inner p-4 space-y-3">
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-400 font-medium">Posting Interval:</span>
                        <span id="intervalDisplay" class="text-blue-400 font-bold text-sm font-mono">60 mins</span>
                    </div>
                    <input id="schedInterval" type="range" min="15" max="180" step="15" value="60" 
                           oninput="document.getElementById('intervalDisplay').innerText = this.value + ' mins'"
                           class="w-full accent-blue-500 cursor-pointer">
                    <div class="text-[11px] text-slate-500 space-y-1">
                        <div>• Automatically picks the next sequenced part from 69 clips.</div>
                        <div>• 30-60s randomized jitter to look human and avoid rate limits.</div>
                    </div>
                </div>

                <button id="schedBtn" onclick="toggleScheduler()" 
                        class="w-full py-3 rounded-lg font-semibold text-xs tracking-wider uppercase transition bg-slate-800 hover:bg-slate-700 text-slate-200">
                    ▶ Start Autonomous Scheduler
                </button>
            </section>
        </div>

        <!-- RIGHT COLUMN: SEQUENTIAL QUEUE & MANUAL POST (7 COLS) -->
        <div class="lg:col-span-7 space-y-6">

            <!-- 3. QUEUE & PAYLOAD DISPATCH -->
            <section class="card p-5 space-y-4">
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                        <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                            <span>3.</span> Sequential Queue & Post
                        </h2>
                        <p class="text-[11px] text-slate-400">Select account, preview payload, and post reel immediately</p>
                    </div>
                    <span id="queueProgressBadge" class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        Part 1 of 69
                    </span>
                </div>

                <div class="space-y-4">
                    <!-- Target Account Select -->
                    <div>
                        <div class="flex items-center justify-between mb-1.5">
                            <label class="text-xs font-semibold text-slate-300">Target Account:</label>
                            <span id="accountQueueInfo" class="text-[11px] text-slate-400 font-mono"></span>
                        </div>
                        <select id="targetAccountSelect" onchange="onAccountChange()" 
                                class="w-full bg-[#090E1A] border border-slate-800 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500">
                        </select>
                    </div>

                    <!-- Selected Clip Select -->
                    <div>
                        <div class="flex items-center justify-between mb-1.5">
                            <label class="text-xs font-semibold text-slate-300">Video Payload (Auto-Selected Next Part):</label>
                            <span id="selectedPartBadge" class="text-xs font-bold text-amber-400 font-mono"></span>
                        </div>
                        <select id="clipSelect" onchange="onClipManualChange()" 
                                class="w-full bg-[#090E1A] border border-slate-800 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500">
                        </select>
                    </div>

                    <!-- AI Caption Studio -->
                    <div class="card-inner p-3.5 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                                <span>✨</span> AI Dynamic Caption (Anti-Duplicate Hook)
                            </span>
                            <button onclick="regenerateCaption()" class="text-xs text-blue-400 hover:text-blue-300 transition font-medium">
                                ↻ Regenerate
                            </button>
                        </div>
                        <textarea id="captionBox" rows="4" 
                                  class="w-full bg-[#060A12] border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono leading-relaxed"></textarea>
                    </div>

                    <!-- Post Button -->
                    <button id="postBtn" onclick="triggerPostNow()" 
                            class="w-full py-3.5 rounded-lg btn-dispatch font-bold text-sm tracking-wide transition flex items-center justify-center gap-2">
                        <span>🚀</span> DISPATCH REEL TO INSTAGRAM
                    </button>
                </div>
            </section>

            <!-- 4. LIVE TELEMETRY LOGS -->
            <section class="card p-5 space-y-3">
                <div class="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <h2 class="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                        <span>4.</span> Live Activity Terminal
                    </h2>
                    <span class="text-[10px] text-slate-500 font-mono">AUTO-STREAM 1s</span>
                </div>

                <div id="terminal" class="bg-[#050811] border border-slate-900 rounded-lg p-3.5 h-64 overflow-y-auto font-mono text-[11px] space-y-1.5 leading-relaxed">
                    <!-- Logs stream here -->
                </div>
            </section>
        </div>
    </main>

    <!-- ADD ACCOUNT MODAL -->
    <div id="addModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center hidden z-50 p-4">
        <div class="card p-6 rounded-xl max-w-md w-full space-y-4">
            <h3 class="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3">
                Add New Social Profile
            </h3>
            <div>
                <label class="text-xs font-semibold text-slate-400">Profile Identifier</label>
                <input id="newAccId" type="text" placeholder="e.g. insta_03" 
                       class="mt-1 w-full bg-[#090E1A] border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-mono">
            </div>
            <div>
                <label class="text-xs font-semibold text-slate-400">Display Label</label>
                <input id="newAccName" type="text" placeholder="e.g. Standup Comedy Hub" 
                       class="mt-1 w-full bg-[#090E1A] border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="text-xs font-semibold text-slate-400">Social Platform</label>
                <select id="newAccPlatform" class="mt-1 w-full bg-[#090E1A] border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500">
                    <option value="instagram">Instagram</option>
                    <option value="facebook">Facebook</option>
                    <option value="twitter">X / Twitter</option>
                    <option value="tiktok">TikTok</option>
                    <option value="snapchat">Snapchat</option>
                    <option value="pinterest">Pinterest</option>
                    <option value="youtube">YouTube</option>
                </select>
            </div>
            <div class="flex gap-3 pt-2">
                <button onclick="closeAddAccountModal()" class="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition">
                    Cancel
                </button>
                <button onclick="submitNewAccount()" class="flex-1 py-2 rounded-lg btn-primary text-xs font-semibold transition">
                    Create Profile
                </button>
            </div>
        </div>
    </div>

    <script>
        let cachedStatus = null;

        function openAddAccountModal() { document.getElementById('addModal').classList.remove('hidden'); }
        function closeAddAccountModal() { document.getElementById('addModal').classList.add('hidden'); }

        const PLAT_ICONS = {
            instagram: 'IG', facebook: 'FB', twitter: '𝕏',
            tiktok: 'TT', snapchat: 'SC', pinterest: 'PT', youtube: 'YT'
        };

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                cachedStatus = data;

                // 1. Render Accounts
                const accContainer = document.getElementById('accountsList');
                const accSelect = document.getElementById('targetAccountSelect');
                const prevSelected = accSelect.value;
                accContainer.innerHTML = '';
                accSelect.innerHTML = '';

                let activeCount = 0;
                let activeAccountName = null;

                data.accounts.forEach(acc => {
                    const isRunning = acc.is_browser_running;
                    if (isRunning) {
                        activeCount++;
                        activeAccountName = `${acc.name} (${acc.id})`;
                    }

                    const platLabel = PLAT_ICONS[acc.platform] || acc.platform.substring(0,2).toUpperCase();

                    const statusPill = acc.is_logged_in
                        ? '<span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Connected</span>'
                        : '<span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Login Required</span>';

                    const actionBtn = isRunning
                        ? `<button onclick="stopActiveBrowser()" class="px-3 py-1.5 text-xs btn-danger rounded-lg flex items-center gap-1"><span>⏹</span> Close</button>`
                        : `<button onclick="launchBrowser('${acc.id}')" class="px-3 py-1.5 text-xs btn-launch rounded-lg flex items-center gap-1"><span>▶</span> Launch Browser</button>`;

                    const item = document.createElement('div');
                    item.className = 'card-inner p-4 space-y-3 transition hover:border-slate-700';
                    item.innerHTML = `
                        <div class="flex items-start justify-between gap-3">
                            <div class="flex items-center gap-3 min-w-0">
                                <div class="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-white flex-shrink-0">
                                    ${platLabel}
                                </div>
                                <div class="min-w-0">
                                    <div class="font-bold text-sm text-white truncate">${acc.name}</div>
                                    <div class="text-[11px] text-slate-500 font-mono">${acc.id} &bull; ${acc.platform.toUpperCase()}</div>
                                </div>
                            </div>
                            <div class="flex-shrink-0">${statusPill}</div>
                        </div>
                        <div class="flex items-center justify-between gap-2 pt-2 border-t border-slate-900 text-[11px] text-slate-400 font-mono">
                            <div>RTX GPU &bull; ${acc.fingerprint.device_memory}GB RAM &bull; ${acc.fingerprint.hardware_concurrency}C</div>
                            <div>${actionBtn}</div>
                        </div>
                    `;
                    accContainer.appendChild(item);

                    const opt = document.createElement('option');
                    opt.value = acc.id;
                    opt.textContent = `${acc.name} (${acc.id}) [Next: Part ${acc.progress.next_part || 'Done'}]`;
                    accSelect.appendChild(opt);
                });

                if (prevSelected && data.accounts.some(a => a.id === prevSelected)) {
                    accSelect.value = prevSelected;
                }

                // Active browser banner
                document.getElementById('statActiveBrowsers').textContent = `${activeCount} Windows`;
                const banner = document.getElementById('activeBrowserBanner');
                if (activeCount > 0) {
                    banner.classList.remove('hidden');
                    document.getElementById('bannerAccountName').textContent = activeAccountName;
                } else {
                    banner.classList.add('hidden');
                }

                // Render Clips
                const clipSelect = document.getElementById('clipSelect');
                if (clipSelect.options.length === 0) {
                    data.clips.forEach(clip => {
                        const opt = document.createElement('option');
                        opt.value = clip;
                        opt.textContent = clip;
                        clipSelect.appendChild(opt);
                    });
                }
                document.getElementById('statTotalClips').textContent = `${data.clips.length} Clips Loaded`;

                onAccountChange();

                // Scheduler state
                const sBtn = document.getElementById('schedBtn');
                if (data.scheduler_running) {
                    sBtn.className = 'w-full py-3 rounded-lg font-semibold text-xs tracking-wider uppercase transition bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/30';
                    sBtn.textContent = '⏹ Stop Autonomous Scheduler';
                } else {
                    sBtn.className = 'w-full py-3 rounded-lg font-semibold text-xs tracking-wider uppercase transition bg-slate-800 hover:bg-slate-700 text-slate-200';
                    sBtn.textContent = '▶ Start Autonomous Scheduler';
                }

            } catch (e) {
                console.error("Status fetch error:", e);
            }
        }

        async function launchBrowser(accId) {
            try {
                await fetch('/api/browser/launch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ account_id: accId })
                });
                fetchStatus();
            } catch (e) {
                console.error(e);
            }
        }

        async function stopActiveBrowser() {
            try {
                await fetch('/api/browser/stop', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({})
                });
                fetchStatus();
            } catch (e) {
                console.error(e);
            }
        }

        function onAccountChange() {
            if (!cachedStatus) return;
            const accId = document.getElementById('targetAccountSelect').value;
            const acc = cachedStatus.accounts.find(a => a.id === accId);
            if (!acc) return;

            const p = acc.progress;
            document.getElementById('accountQueueInfo').textContent = `Posted: ${p.posted_count}/${p.total_clips} clips`;
            document.getElementById('queueProgressBadge').textContent = `Part ${p.next_part || 'Done'} of ${p.total_clips}`;

            if (p.next_filename) {
                document.getElementById('clipSelect').value = p.next_filename;
                document.getElementById('selectedPartBadge').textContent = `[Part ${p.next_part}]`;
            }

            regenerateCaption();
        }

        function onClipManualChange() {
            regenerateCaption();
        }

        async function regenerateCaption() {
            const clipName = document.getElementById('clipSelect').value;
            if (!clipName) return;
            try {
                const res = await fetch('/api/ai_caption', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ filename: clipName })
                });
                const data = await res.json();
                document.getElementById('captionBox').value = data.caption;
            } catch (e) {}
        }

        async function triggerPostNow() {
            const accId = document.getElementById('targetAccountSelect').value;
            const clipName = document.getElementById('clipSelect').value;
            const caption = document.getElementById('captionBox').value;

            if (!accId || !clipName) return;

            const btn = document.getElementById('postBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Dispatching Reel in Progress...';
            btn.classList.add('opacity-50');

            try {
                await fetch('/api/post_now', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        account_id: accId,
                        clip_name: clipName,
                        custom_caption: caption
                    })
                });
            } catch (e) {
                console.error(e);
            } finally {
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = '🚀 DISPATCH REEL TO INSTAGRAM';
                    btn.classList.remove('opacity-50');
                    fetchStatus();
                }, 5000);
            }
        }

        async function toggleScheduler() {
            const interval = document.getElementById('schedInterval').value;
            await fetch('/api/scheduler/toggle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ interval_min: interval })
            });
            fetchStatus();
        }

        async function submitNewAccount() {
            const accId = document.getElementById('newAccId').value.trim();
            const accName = document.getElementById('newAccName').value.trim();
            const platform = document.getElementById('newAccPlatform').value;
            if (!accId) return;

            await fetch('/api/add_account', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: accId, name: accName || accId, platform: platform })
            });
            closeAddAccountModal();
            fetchStatus();
        }

        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                const term = document.getElementById('terminal');
                term.innerHTML = data.logs.map(l => {
                    let color = 'text-slate-400';
                    if (l.includes('[ONLINE]') || l.includes('[SUCCESS]') || l.includes('[OK]') || l.includes('Connected')) {
                        color = 'text-emerald-400 font-semibold';
                    } else if (l.includes('[ERROR]') || l.includes('[FAIL]') || l.includes('error')) {
                        color = 'text-rose-400 font-semibold';
                    } else if (l.includes('[LAUNCH]') || l.includes('[SYSTEM]')) {
                        color = 'text-blue-400';
                    } else if (l.includes('[DISPATCH]') || l.includes('[CYCLE]')) {
                        color = 'text-amber-400 font-medium';
                    }
                    return `<div class="${color}">${l}</div>`;
                }).join('');
                term.scrollTop = term.scrollHeight;
            } catch (e) {}
        }

        fetchStatus();
        setInterval(fetchLogs, 1000);
        setInterval(fetchStatus, 3000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status")
def api_status():
    accounts = load_json(ACCOUNTS_FILE, [])
    acc_list = []
    with session_lock:
        running_keys = list(active_sessions.keys())

    for a in accounts:
        progress = db.get_account_progress(a["id"])
        fp = get_profile_fingerprint(a.get("profile_dir", f"profiles/{a['id']}"))
        acc_list.append({
            "id": a["id"],
            "name": a.get("name", a["id"]),
            "platform": a.get("platform", "instagram"),
            "is_logged_in": check_login_status(a),
            "is_browser_running": a["id"] in running_keys,
            "progress": progress,
            "fingerprint": fp
        })

    all_vids = [v["filename"] for v in db.get_all_videos()]

    return jsonify({
        "accounts": acc_list,
        "clips": all_vids,
        "scheduler_running": scheduler_state["running"]
    })

@app.route("/api/browser/launch", methods=["POST"])
def api_browser_launch():
    data = request.json or {}
    acc_id = data.get("account_id")
    accounts = load_json(ACCOUNTS_FILE, [])
    selected = next((a for a in accounts if a["id"] == acc_id), None)
    if not selected:
        return jsonify({"status": "error", "message": "Account not found"}), 404

    # Stop any currently active browser
    with session_lock:
        for k in list(active_sessions.keys()):
            sess = active_sessions.pop(k, None)
            if sess and sess.get("proc"):
                try:
                    sess["proc"].terminate()
                except Exception:
                    pass

    platform = selected.get("platform", "instagram")
    target_url = PLATFORM_URLS.get(platform, "https://www.instagram.com/")
    profile_subpath = selected.get("profile_dir", f"profiles/{selected['id']}")

    h = int(hashlib.sha256(selected['id'].encode()).hexdigest(), 16)
    port = 9220 + (h % 50)

    try:
        add_log(f"[LAUNCH] Opening Chrome browser window for: {selected['name']} ({selected['id']})")
        add_log(f"[LAUNCH] Target: {target_url} | Port: {port}")
        
        # Launch real Chrome with WinSta0\Default
        proc = launch_visible_chrome(profile_subpath=profile_subpath, target_url=target_url, port=port)
        
        stop_event = threading.Event()
        with session_lock:
            active_sessions[selected["id"]] = {
                "proc": proc,
                "port": port,
                "platform": platform,
                "stop_event": stop_event
            }

        add_log(f"[ONLINE] Chrome window opened on your desktop! Log into your account.")

        # Background thread to monitor process lifetime and detect cookies
        def monitor_worker():
            profile_dir = BASE_DIR / profile_subpath
            cookies_file = profile_dir / "Default" / "Network" / "Cookies"
            detected = False

            while not stop_event.is_set():
                if proc.poll() is not None:
                    add_log(f"[STOP] Chrome window closed by user for {selected['id']}.")
                    break

                if not detected and cookies_file.exists():
                    try:
                        if cookies_file.stat().st_size > 5000:
                            detected = True
                            add_log(f"[SUCCESS] Session data detected and saved for {selected['id']}!")
                    except Exception:
                        pass

                time.sleep(1.5)

            with session_lock:
                active_sessions.pop(selected["id"], None)

        threading.Thread(target=monitor_worker, daemon=True).start()
        return jsonify({"status": "started"})

    except Exception as e:
        add_log(f"[ERROR] Could not launch Chrome: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/browser/stop", methods=["POST"])
def api_browser_stop():
    with session_lock:
        for acc_id, sess in list(active_sessions.items()):
            if sess.get("stop_event"):
                sess["stop_event"].set()
            if sess.get("proc"):
                try:
                    sess["proc"].terminate()
                except Exception:
                    pass
            active_sessions.pop(acc_id, None)
            add_log(f"[STOP] Browser closed for {acc_id}.")
    return jsonify({"status": "stopped"})

@app.route("/api/ai_caption", methods=["POST"])
def api_ai_caption():
    data = request.json or {}
    filename = data.get("filename", "")
    part_num = db._extract_part_number(filename)
    total_parts = len(db.get_all_videos()) or 69
    caption = generate_ai_caption(filename, part_num, total_parts)
    return jsonify({"caption": caption})

@app.route("/api/logs")
def api_logs():
    return jsonify({"logs": logs})

@app.route("/api/add_account", methods=["POST"])
def api_add_account():
    data = request.json or {}
    new_id = data.get("id", "").strip()
    new_name = data.get("name", new_id).strip()
    new_platform = data.get("platform", "instagram").strip()
    if not new_id:
        return jsonify({"status": "error", "message": "ID is required"}), 400

    accounts = load_json(ACCOUNTS_FILE, [])
    if any(a["id"] == new_id for a in accounts):
        return jsonify({"status": "error", "message": "Node ID already exists"}), 400
    
    accounts.append({
        "id": new_id,
        "platform": new_platform,
        "name": new_name,
        "profile_dir": f"profiles/{new_id}",
        "proxy": None,
        "enabled": True
    })
    save_json(ACCOUNTS_FILE, accounts)
    add_log(f"[SYSTEM] New Profile Created: {new_id} ({new_name}) | Platform: {new_platform.upper()}")
    return jsonify({"status": "ok"})

@app.route("/api/post_now", methods=["POST"])
def api_post_now():
    data = request.json or {}
    acc_id = data.get("account_id")
    clip_name = data.get("clip_name")

    accounts = load_json(ACCOUNTS_FILE, [])
    selected = next((a for a in accounts if a["id"] == acc_id), None)
    if not selected:
        return jsonify({"status": "error", "message": "Account not found"}), 404

    clip_path = db.outputs_dir / clip_name
    if not clip_path.exists():
        return jsonify({"status": "error", "message": "Clip not found"}), 404

    def post_worker():
        add_log(f"[DISPATCH] Starting Reel Upload: {clip_name}")
        add_log(f"[DISPATCH] Target Account: {selected['name']} ({selected['id']})")
        try:
            from instagram_poster import post_reel_to_instagram
            success = post_reel_to_instagram(selected, clip_path, headless=False, log_fn=add_log)
            if success:
                add_log(f"[SUCCESS] Reel '{clip_name}' successfully posted on Instagram!")
            else:
                add_log(f"[FAIL] Upload failed or timed out. Check debug_screenshots.")
        except Exception as e:
            add_log(f"[ERROR] Dispatch error: {e}")

    threading.Thread(target=post_worker, daemon=True).start()
    return jsonify({"status": "started"})

@app.route("/api/scheduler/toggle", methods=["POST"])
def api_scheduler_toggle():
    data = request.json or {}
    interval = int(data.get("interval_min", 60))

    if not scheduler_state["running"]:
        scheduler_state["running"] = True
        scheduler_state["interval_min"] = interval
        add_log(f"[SCHEDULER] Autonomous Drip Scheduler ACTIVATED (Interval: Every {interval} mins).")

        def scheduler_loop():
            from instagram_poster import post_reel_to_instagram

            while scheduler_state["running"]:
                accounts = [a for a in load_json(ACCOUNTS_FILE, []) if a.get("enabled", True)]
                for acc in accounts:
                    if not scheduler_state["running"]:
                        break
                    next_vid = db.get_next_unposted_video(acc["id"])
                    if not next_vid:
                        add_log(f"[INFO] All sequenced parts dispatched for {acc['id']}.")
                        continue
                    clip_path = Path(next_vid["filepath"])
                    add_log(f"[CYCLE] Dispatching sequential Part {next_vid['part']} to {acc['name']}...")
                    post_reel_to_instagram(acc, clip_path, headless=False, log_fn=add_log)
                    time.sleep(45)

                for _ in range(scheduler_state["interval_min"] * 60):
                    if not scheduler_state["running"]:
                        break
                    time.sleep(1)

        t = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_state["thread"] = t
        t.start()
    else:
        scheduler_state["running"] = False
        add_log("[SCHEDULER] Autonomous Drip Scheduler STOPPED.")

    return jsonify({"scheduler_running": scheduler_state["running"]})

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print("[*] Starting Ghost Panel Pro on http://127.0.0.1:5050 ...")
    app.run(host="127.0.0.1", port=5050, debug=False)
