import os
import sys
import json
from pathlib import Path
import pytest

# Ensure repo root and auto_poster are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "auto_poster"))

from auto_poster.database import GhostDatabase

def test_extract_part_number():
    db = GhostDatabase()
    assert db._extract_part_number("Part_01.mp4") == 1
    assert db._extract_part_number("reel_part-12.mp4") == 12
    assert db._extract_part_number("clip_part5.mp4") == 5
    assert db._extract_part_number("video_07.mp4") == 7
    assert db._extract_part_number("random_video.mp4") == 999

def test_database_sync_and_progress(tmp_path, monkeypatch):
    # Setup temporary directory for outputs
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    
    (outputs_dir / "clip_part_01.mp4").write_text("dummy video 1")
    (outputs_dir / "clip_part_02.mp4").write_text("dummy video 2")
    (outputs_dir / "clip_part_03.mp4").write_text("dummy video 3")
    (outputs_dir / "sample_test.mp4").write_text("sample ignored")

    db_file = tmp_path / "ghost_database.json"

    monkeypatch.setattr("auto_poster.database.get_outputs_dir", lambda: outputs_dir)
    monkeypatch.setattr("auto_poster.database.DB_FILE", db_file)

    db = GhostDatabase()
    all_videos = db.get_all_videos()
    assert len(all_videos) == 3
    assert [v["part"] for v in all_videos] == [1, 2, 3]

    # Test next unposted
    next_vid = db.get_next_unposted_video("account_1")
    assert next_vid is not None
    assert next_vid["part"] == 1

    # Mark Part 1 dispatched
    db.mark_dispatched(next_vid["filename"], "account_1")
    progress = db.get_account_progress("account_1")
    assert progress["total_clips"] == 3
    assert progress["posted_count"] == 1
    assert progress["remaining"] == 2
    assert progress["next_part"] == 2

    # Next unposted should now be Part 2
    next_vid2 = db.get_next_unposted_video("account_1")
    assert next_vid2["part"] == 2

    # Account 2 should still get Part 1
    next_acc2 = db.get_next_unposted_video("account_2")
    assert next_acc2["part"] == 1
