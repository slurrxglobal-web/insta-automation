import sys
import subprocess
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "slicer"))

from slicer.engine import load_config, get_video_duration

def test_settings_json_consistency():
    cfg = load_config()
    clip_cfg = cfg.get("clip_settings", {})
    default_dur = clip_cfg.get("default_duration_seconds")
    min_dur = clip_cfg.get("min_duration_seconds", 60)
    max_dur = clip_cfg.get("max_duration_seconds", 90)

    assert default_dur is not None
    assert min_dur <= default_dur <= max_dur
    assert default_dur == 75

def test_ffmpeg_missing_friendly_error(monkeypatch, capsys):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("ffprobe not found")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(FileNotFoundError):
        get_video_duration("dummy.mp4")

    captured = capsys.readouterr()
    assert "ffprobe" in captured.out.lower()
    assert "ffmpeg" in captured.out.lower()
    assert "path" in captured.out.lower()
