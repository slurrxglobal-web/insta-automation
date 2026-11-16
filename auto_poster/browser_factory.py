import os
import sys
import json
import time
import random
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
]

RENDERERS = [
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
]

def cleanup_stale_locks(user_data_dir):
    lock_files = ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]
    for fname in lock_files:
        fpath = user_data_dir / fname
        if fpath.exists():
            try:
                fpath.unlink()
            except Exception:
                pass

def get_profile_fingerprint(profile_id):
    h = int(hashlib.sha256(str(profile_id).encode()).hexdigest(), 16)
    ua = USER_AGENTS[h % len(USER_AGENTS)]
    gpu = RENDERERS[h % len(RENDERERS)]
    canvas_noise = (h % 10 + 1) * 0.00001
    
    return {
        "user_agent": ua,
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": gpu,
        "hardware_concurrency": 8 if (h % 2 == 0) else 16,
        "device_memory": 8 if (h % 2 == 0) else 16,
        "canvas_salt": canvas_noise,
        "screen_width": 1920,
        "screen_height": 1080
    }

def get_stealth_script(fp):
    return f"""
    // 1. Remove automation markers
    try {{
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        delete navigator.__proto__.webdriver;
    }} catch(e) {{}}

    window.chrome = {{
        runtime: {{}},
        loadTimes: function() {{}},
        csi: function() {{}},
        app: {{}}
    }};

    // 2. Hardware Concurrency & Memory
    try {{
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {fp['hardware_concurrency']} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {fp['device_memory']} }});
        Object.defineProperty(navigator, 'languages', {{ get: () => ['en-US', 'en'] }});
    }} catch(e) {{}}

    // 3. WebGL Spoofing (NVIDIA GPU Mask)
    try {{
        const getParameterOld = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{fp['webgl_vendor']}';
            if (parameter === 37446) return '{fp['webgl_renderer']}';
            return getParameterOld.apply(this, [parameter]);
        }};
        if (typeof WebGL2RenderingContext !== 'undefined') {{
            const getParameter2Old = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fp['webgl_vendor']}';
                if (parameter === 37446) return '{fp['webgl_renderer']}';
                return getParameter2Old.apply(this, [parameter]);
            }};
        }}
    }} catch(e) {{}}

    // 4. Subtle Canvas Micro-Noise
    try {{
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {{
            const ctx = this.getContext('2d');
            if (ctx) {{
                try {{
                    const img = ctx.getImageData(0, 0, Math.min(10, this.width), Math.min(10, this.height));
                    for (let i = 0; i < img.data.length; i += 4) {{
                        img.data[i] = (img.data[i] + 1) % 256;
                    }}
                    ctx.putImageData(img, 0, 0);
                }} catch(e) {{}}
            }}
            return originalToDataURL.apply(this, arguments);
        }};
    }} catch(e) {{}}
    """

def get_browser_context(playwright, profile_subpath="insta_01", headless=False, proxy_dict=None):
    """
    Launches Chrome persistent context with isolated profile and stealth protection.
    """
    user_data_dir = BASE_DIR / profile_subpath
    user_data_dir.mkdir(parents=True, exist_ok=True)
    cleanup_stale_locks(user_data_dir)

    fp = get_profile_fingerprint(str(profile_subpath))
    stealth_code = get_stealth_script(fp)

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1280,900"
    ]

    proxy_cfg = None
    if proxy_dict and proxy_dict.get("server"):
        proxy_cfg = {"server": proxy_dict["server"]}
        if proxy_dict.get("username"):
            proxy_cfg["username"] = proxy_dict["username"]
        if proxy_dict.get("password"):
            proxy_cfg["password"] = proxy_dict["password"]

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        channel="chrome",
        headless=headless,
        args=args,
        user_agent=fp["user_agent"],
        viewport={"width": 1280, "height": 900},
        proxy=proxy_cfg,
        ignore_default_args=["--enable-automation"]
    )
    context.add_init_script(stealth_code)
    return context
