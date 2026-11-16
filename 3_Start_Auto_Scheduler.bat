@echo off
title Ghost Traffic - Autonomous Drip Scheduler
cd /d "%~dp0auto_poster"
python scheduler_cli.py
