import os
import sys
import json
import math
import subprocess
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "inputs"
OUTPUTS_DIR = BASE_DIR / "outputs"
CONFIGS_DIR = BASE_DIR / "configs"
ASSETS_DIR = BASE_DIR / "assets"

CONFIG_FILE = CONFIGS_DIR / "settings.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "clip_settings": {
            "default_duration_seconds": 75,
            "output_resolution": "1080x1920",
            "fps": 30
        },
        "anti_copyright": {
            "speed_multiplier": 1.025,
            "pitch_shift_factor": 0.98,
            "contrast_boost": 1.03,
            "saturation_boost": 1.05,
            "strip_metadata": True
        },
        "branding": {
            "telegram_handle": "@GhostTrafficHub",
            "cta_text": "Full Video on Telegram"
        }
    }

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except FileNotFoundError:
        print("\n[!] ERROR: 'ffprobe' system me nahi mila / ffprobe executable was not found.")
        print("    FFmpeg install karke uske 'bin' folder ko system Environment Variables (PATH) me add karein.")
        print("    Download link: https://www.gyan.dev/ffmpeg/builds/ ya https://ffmpeg.org/download.html\n")
        raise

def process_clip(input_path, output_path, start_time, duration, part_num, total_parts, config):
    clip_cfg = config["clip_settings"]
    anti_cfg = config["anti_copyright"]
    branding = config["branding"]

    tg_handle = branding.get("telegram_handle", "@GhostTrafficHub")
    cta_text = branding.get("cta_text", "Full Movie on Telegram")
    part_str = f"PART {part_num:02d}"

    speed = anti_cfg.get("speed_multiplier", 1.025)
    contrast = anti_cfg.get("contrast_boost", 1.03)
    saturation = anti_cfg.get("saturation_boost", 1.05)

    # Complex filter for 9:16 vertical + blurred background + center crisp video + color grade
    filter_complex = (
        f"[0:v]split=2[bg_raw][fg_raw];"
        f"[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        f"[fg_raw]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[combined];"
        f"[combined]eq=contrast={contrast}:saturation={saturation},setpts=PTS/{speed},"
        f"drawtext=text='{part_str}':fontcolor=white:fontsize=52:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=120:font=Arial,"
        f"drawtext=text='👉 {cta_text} \\: {tg_handle}':fontcolor=yellow:fontsize=40:box=1:boxcolor=black@0.7:boxborderw=12:x=(w-text_w)/2:y=h-160:font=Arial[v_out]"
    )

    # Audio speed & slight pitch variation
    # atempo adjusts duration without changing sample rate
    audio_filter = f"atempo={speed}"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-map", "0:a?",
        "-af", audio_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", str(clip_cfg.get("fps", 30)),
        "-map_metadata", "-1" if anti_cfg.get("strip_metadata", True) else "0",
        str(output_path)
    ]

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("\n[!] ERROR: 'ffmpeg' system me nahi mila / ffmpeg executable was not found.")
        print("    FFmpeg install karke uske 'bin' folder ko system Environment Variables (PATH) me add karein.")
        print("    Download link: https://www.gyan.dev/ffmpeg/builds/ ya https://ffmpeg.org/download.html\n")
        raise

def run_engine():
    config = load_config()
    clip_duration = config["clip_settings"].get("default_duration_seconds", 75)

    # Find first video in inputs
    video_files = [f for f in INPUTS_DIR.iterdir() if f.suffix.lower() in [".mp4", ".mkv", ".mov", ".webm"]]
    if not video_files:
        print("[!] No video found in inputs/ folder.")
        return

    input_video = video_files[0]
    total_duration = get_video_duration(input_video)
    total_parts = math.ceil(total_duration / clip_duration)

    print(f"[*] Processing: {input_video.name}")
    print(f"[*] Total duration: {total_duration:.1f}s | Target clip duration: {clip_duration}s | Total parts: {total_parts}")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    for part in range(1, total_parts + 1):
        start = (part - 1) * clip_duration
        current_dur = min(clip_duration, total_duration - start)
        if current_dur < 10:  # Skip tiny tail segments
            continue

        out_name = f"{input_video.stem}_part_{part:02d}.mp4"
        out_path = OUTPUTS_DIR / out_name

        print(f" -> Rendering {out_name} (start: {start}s, dur: {current_dur}s)...")
        process_clip(input_video, out_path, start, current_dur, part, total_parts, config)
        print(f"    [OK] Saved: {out_name}")

    print("\n[OK] ALL CLIPS GENERATED SUCCESSFULLY IN outputs/!")

if __name__ == "__main__":
    run_engine()
