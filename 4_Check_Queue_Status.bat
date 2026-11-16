@echo off
title Ghost Traffic - Queue & Account Status
cd /d "%~dp0auto_poster"
python status_cli.py
