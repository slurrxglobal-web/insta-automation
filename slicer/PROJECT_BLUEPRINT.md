# 👻 GHOST TRAFFIC ENGINE - MASTER BLUEPRINT

> **Version:** 1.0.0  
> **Target:** Automated Short-Form Video Processing & Anti-Copyright Engine  
> **Primary Monetization Funnel:** Mass Short-Form Content (FB Reels, YT Shorts) → Telegram Hub → CPA / Smartlinks  

---

## 1. Project Overview & Objectives
**Ghost Traffic Engine** is a high-performance, automated media processing pipeline designed to take raw long-form videos (movies, podcasts, high-retention streams) and programmatically slice them into high-converting 9:16 vertical reels with automated anti-copyright countermeasures, metadata stripping, hook overlays, and call-to-actions.

### Key Performance Goals:
- **Zero Human Editing:** Process a 2-hour video into 80–120 ready-to-post vertical clips in under 15 minutes.
- **Stealth / Anti-Copyright:** Bypass automated algorithmic hash matching (Meta Rights Manager, YouTube Content ID) via multi-layered acoustic and visual transformations.
- **Model / Agent Clarity:** Ensure any future AI session or subagent can inspect this blueprint, understand the exact state of progress, and execute the next task without hallucination or context drift.

---

## 2. Directory Architecture
```
ghost traffic/
│
├── PROJECT_BLUEPRINT.md      # Master documentation and roadmap (Single Source of Truth)
├── engine.py                 # Core CLI orchestration script
│
├── configs/
│   ├── settings.json         # Clip length, aspect ratio, audio pitch offsets, speed factors
│   └── templates.json        # Caption formats, watermark handles, Telegram links
│
├── inputs/                   # Raw movie / video files placed here (.mp4, .mkv)
│
├── outputs/                  # Final rendered 9:16 vertical clips ready for upload
│
└── assets/
    ├── fonts/                # Bold, high-retention fonts for overlays (e.g. Montserrat-Black)
    └── watermarks/           # Transparent badges, arrows, and ambient frame assets
```

---

## 3. The 4-Phase Roadmap

### 🏁 Phase 1: Environment & Foundation (CURRENT)
- [x] Create workspace directories (`inputs`, `outputs`, `configs`, `assets`).
- [x] Establish Master Blueprint (`PROJECT_BLUEPRINT.md`).
- [ ] Create `configs/settings.json` with baseline production parameters.
- [ ] Verify FFmpeg binary and Python dependencies (`ffmpeg-python`, `exiftool` availability).

### ⚙️ Phase 2: Core Engine Development (`engine.py`)
- [ ] **Scene & Duration Slicer:** Segment input videos into clean 60–90 second chunks.
- [ ] **9:16 Canvas Converter:**
  - Center: 16:9 crisp original frame.
  - Top & Bottom: Dynamic Gaussian blurred, zoomed background of the active video (eliminates black bars).
- [ ] **Anti-Copyright & Signature Scrambler:**
  - Micro-speed shift (1.02x – 1.04x).
  - Audio pitch detune (-0.4 to -0.6 semitones) + subtle EQ filter.
  - Micro-contrast / dynamic color grading LUT overlay.
  - ExifTool / FFmpeg global metadata purge (`-map_metadata -1`).
- [ ] **Dynamic Hook & CTA Overlay:**
  - Top: Header bar with dynamic part counter (`"PART 01"`, `"PART 02"`).
  - Bottom: CTA banner (`"Full Movie in Telegram: @Handle"`).

### 🧪 Phase 3: Testing & Anti-Copyright Verification
- [ ] Test render with a 5-minute raw video sample.
- [ ] Verify audio sync, aspect ratio, and visual aesthetics.
- [ ] Run hash comparison test before and after processing to confirm MD5/SHA256 signature alteration.
- [ ] Perform a private test upload on Facebook/Instagram to ensure zero immediate copyright flags.

### 🚀 Phase 4: Scaling & Bulk Orchestration
- [ ] Batch processing: Drop multiple movies into `inputs/` and process sequentially.
- [ ] Integration with auto-schedulers / ADB mobile farming tools for hands-free publishing.
- [ ] Telemetry logging: Track generated clip counts and processing times.

---

## 4. Technical Specifications & Default Configs

```json
{
  "clip_settings": {
    "default_duration_seconds": 75,
    "min_duration_seconds": 60,
    "max_duration_seconds": 90,
    "output_resolution": "1080x1920",
    "fps": 30
  },
  "anti_copyright": {
    "speed_multiplier": 1.025,
    "pitch_shift_factor": 0.98,
    "contrast_boost": 1.03,
    "saturation_boost": 1.05,
    "strip_metadata": true
  },
  "branding": {
    "telegram_handle": "@GhostTrafficHub",
    "cta_text": "Watch Full Video on Telegram"
  }
}
```

---

## 5. Instructions for Future AI Agents & Subagents
1. **Never edit files outside of designated tasks:** Always adhere to the directory structure.
2. **Consult this blueprint before making architectural changes:** If parameters or features change, update this document immediately.
3. **Keep CLI execution lightweight:** Avoid heavy UI dependencies; execute commands directly via FFmpeg subprocesses for maximum speed.
