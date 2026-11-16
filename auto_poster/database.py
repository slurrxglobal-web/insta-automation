import os
import re
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DB_FILE = BASE_DIR / "ghost_database.json"

def get_outputs_dir():
    candidates = [
        ROOT_DIR / "outputs",
        BASE_DIR / "outputs",
        ROOT_DIR / "slicer" / "outputs"
    ]
    for c in candidates:
        if c.exists() and list(c.glob("*.mp4")):
            return c
    out = ROOT_DIR / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out

class GhostDatabase:
    def __init__(self):
        self.outputs_dir = get_outputs_dir()
        self.db = self._load_db()
        self.sync_filesystem()

    def _load_db(self):
        if DB_FILE.exists():
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "videos": {},
            "accounts_queue": {},
            "stats": {"total_rendered": 0, "total_posted": 0}
        }

    def save(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=2)

    def _extract_part_number(self, filename):
        match = re.search(r'part[_-]?(\d+)', filename, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Fallback: find any trailing number
        num_match = re.search(r'(\d+)\.mp4$', filename, re.IGNORECASE)
        if num_match:
            return int(num_match.group(1))
        return 999

    def sync_filesystem(self):
        if not self.outputs_dir.exists():
            return

        mp4_files = sorted(
            [p for p in self.outputs_dir.glob("*.mp4") if not p.name.lower().startswith("sample_")],
            key=lambda p: self._extract_part_number(p.name)
        )
        current_filenames = {p.name for p in mp4_files}

        # Remove obsolete or sample files from database
        for fname in list(self.db["videos"].keys()):
            if fname not in current_filenames:
                del self.db["videos"][fname]

        for path in mp4_files:
            fname = path.name
            if fname not in self.db["videos"]:
                part_num = self._extract_part_number(fname)
                size_mb = round(path.stat().st_size / (1024 * 1024), 2)
                self.db["videos"][fname] = {
                    "filename": fname,
                    "filepath": str(path),
                    "part": part_num,
                    "size_mb": size_mb,
                    "date_added": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime)),
                    "posted_by": []
                }

        self.db["stats"]["total_rendered"] = len(self.db["videos"])
        self.save()

    def get_all_videos(self):
        return sorted(list(self.db["videos"].values()), key=lambda x: x["part"])

    def get_next_unposted_video(self, account_id):
        all_vids = self.get_all_videos()
        for v in all_vids:
            if account_id not in v.get("posted_by", []):
                return v
        return None

    def mark_dispatched(self, filename, account_id):
        if filename in self.db["videos"]:
            if account_id not in self.db["videos"][filename]["posted_by"]:
                self.db["videos"][filename]["posted_by"].append(account_id)
        
        # Update queue tracker
        if account_id not in self.db["accounts_queue"]:
            self.db["accounts_queue"][account_id] = {
                "last_posted": None,
                "last_timestamp": None,
                "total_dispatched": 0
            }
        self.db["accounts_queue"][account_id]["last_posted"] = filename
        self.db["accounts_queue"][account_id]["last_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.db["accounts_queue"][account_id]["total_dispatched"] += 1
        
        # Update global stats
        self.db["stats"]["total_posted"] = sum(len(v["posted_by"]) for v in self.db["videos"].values())
        self.save()

    def get_account_progress(self, account_id):
        all_vids = self.get_all_videos()
        total = len(all_vids)
        posted = sum(1 for v in all_vids if account_id in v.get("posted_by", []))
        next_vid = self.get_next_unposted_video(account_id)
        return {
            "total_clips": total,
            "posted_count": posted,
            "remaining": total - posted,
            "next_part": next_vid["part"] if next_vid else None,
            "next_filename": next_vid["filename"] if next_vid else None
        }

db = GhostDatabase()
