import sys
import re
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "auto_poster"))

from auto_poster.ai_caption import clean_video_name, generate_ai_caption

def test_clean_video_name():
    raw_name = "INDIA'S GOT LATENT S2 EP8 ft. MC Stan_part_02.mp4"
    cleaned = clean_video_name(raw_name)
    assert "part" not in cleaned.lower()
    assert ".mp4" not in cleaned.lower()
    assert "INDIA'S GOT LATENT" in cleaned

def test_generate_ai_caption_without_total_parts():
    caption = generate_ai_caption("test_video_part_03.mp4", 3, total_parts=None)
    assert "[PART 03]" in caption
    assert "/ 69" not in caption
    assert "/ None" not in caption
    assert "Episode:" in caption
    assert "👉" in caption
    # Check that hashtags are present
    hashtags = re.findall(r'#\w+', caption)
    assert len(hashtags) == 6

def test_generate_ai_caption_with_total_parts():
    caption = generate_ai_caption("test_video_part_05.mp4", 5, total_parts=20)
    assert "[PART 05 / 20]" in caption
    assert "Episode:" in caption
    assert "👉" in caption
    hashtags = re.findall(r'#\w+', caption)
    assert len(hashtags) == 6

def test_custom_cta():
    custom = "Join our secret channel"
    caption = generate_ai_caption("test_video_part_01.mp4", 1, custom_cta=custom)
    assert custom in caption
