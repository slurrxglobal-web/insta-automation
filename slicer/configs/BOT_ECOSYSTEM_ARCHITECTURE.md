# 🤖 GHOST TRAFFIC: 3-BOT TELEGRAM AUTOMATION ECOSYSTEM

```mermaid
flowchart TD
    User([👤 Operator / Saurav]) -->|1. Sends Movie Name e.g. /movie Animal| Bot1[🤖 Bot 1: Scraper & Fetcher Bot]
    
    subgraph INGESTION [Phase A: Acquisition]
        Bot1 -->|Scrapes Indexers / DDL / Torrents| DL[Download to inputs/ folder]
    end

    subgraph PROCESSING [Phase B: Ghost Engine]
        DL -->|Trigger Event| Bot2[⚙️ Bot 2: Ghost Clipper Worker]
        Bot2 -->|FFmpeg 9:16 + Anti-Copyright + Branding| OUT[80-100 Reels in outputs/]
    end

    subgraph DISTRIBUTION [Phase C: Multi-Channel Upload]
        OUT -->|Batch Queue| Bot3[🚀 Bot 3: Multi-Platform Uploader]
        Bot3 -->|Meta Graph API| FB[Facebook Pages 1-5]
        Bot3 -->|YouTube Data API v3| YT[YT Shorts Channels]
        Bot3 -->|Telethon / MTProto| TG[Telegram Movie Hub]
    end

    subgraph MONETIZATION [Phase D: Cashflow]
        FB & YT -->|Bio / Comment Hook| TG
        TG -->|Pinned Download Link| CPA[💰 CPA Offer / Adsterra Smartlink]
    end
```

---

## The 3-Bot Role Breakdown

| Bot Component | Trigger | Tech Stack | Execution Responsibility |
| :--- | :--- | :--- | :--- |
| **Bot 1: Scraper & Downloader** | Telegram DM `/movie <title>` | Python `aiogram` + Jackett / Torrent-Aria2c / DDL Scrapers | Finds highest seed stream, downloads `.mp4` into `inputs/`. |
| **Bot 2: Ghost Slicer Worker** | `on_download_complete` Webhook | Python `engine.py` + FFmpeg subprocesses | Splits video into 75s clips, applies 9:16 blurred canvas, speed & pitch detune, exports to `outputs/`. |
| **Bot 3: Multi-Platform Distributor** | Scheduled Cron / Hourly Queue | Python `facebook-sdk` + `google-api-python-client` | Distributes 5-10 reels/day across 5+ pages/channels with rotating titles and Telegram CTA tags. |
