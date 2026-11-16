import os
import sys
import json
import sqlite3
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "auto_poster"))

from auto_poster.common import (
    load_accounts, is_account_logged_in, load_json, save_json, get_outputs_dir
)

def test_load_and_save_json(tmp_path):
    test_file = tmp_path / "test.json"
    data = {"name": "ghost", "status": "active", "count": 42}
    save_json(test_file, data)
    assert test_file.exists()

    loaded = load_json(test_file)
    assert loaded == data

    # Test non-existent file returns default
    missing = load_json(tmp_path / "nonexistent.json", default={"fallback": True})
    assert missing == {"fallback": True}

def test_load_accounts(tmp_path, monkeypatch):
    acc_file = tmp_path / "accounts.json"
    dummy_accounts = [
        {"id": "acc_01", "name": "Account 1", "platform": "instagram", "enabled": True}
    ]
    save_json(acc_file, dummy_accounts)

    monkeypatch.setattr("auto_poster.common.ACCOUNTS_FILE", acc_file)
    accounts = load_accounts()
    assert len(accounts) == 1
    assert accounts[0]["id"] == "acc_01"

def test_is_account_logged_in_with_sqlite(tmp_path, monkeypatch):
    # Setup profile directory with SQLite cookies DB
    profile_dir = tmp_path / "profiles" / "test_acc"
    network_dir = profile_dir / "Default" / "Network"
    network_dir.mkdir(parents=True)
    cookies_db = network_dir / "Cookies"

    acc_dict = {
        "id": "test_acc",
        "profile_dir": str(profile_dir.relative_to(tmp_path))
    }

    monkeypatch.setattr("auto_poster.common.BASE_DIR", tmp_path)

    # 1. Cookies file missing
    assert is_account_logged_in({"id": "missing_acc"}) is False

    # 2. SQLite DB exists without sessionid
    conn = sqlite3.connect(cookies_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE cookies (name TEXT, value TEXT)")
    cur.execute("INSERT INTO cookies VALUES ('csrftoken', 'abc123xyz')")
    conn.commit()
    conn.close()

    assert is_account_logged_in(acc_dict) is False

    # 3. SQLite DB exists with sessionid
    conn = sqlite3.connect(cookies_db)
    cur = conn.cursor()
    cur.execute("INSERT INTO cookies VALUES ('sessionid', 'sess_999888777')")
    conn.commit()
    conn.close()

    assert is_account_logged_in(acc_dict) is True

def test_get_outputs_dir(tmp_path, monkeypatch):
    out = tmp_path / "outputs"
    out.mkdir()
    (out / "reel1.mp4").write_text("test")

    monkeypatch.setattr("auto_poster.common.ROOT_DIR", tmp_path)
    monkeypatch.setattr("auto_poster.common.BASE_DIR", tmp_path / "auto_poster")
    
    found = get_outputs_dir()
    assert found.exists()
