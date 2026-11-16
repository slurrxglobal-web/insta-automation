@echo off
title Ghost Traffic Engine - Web Studio
cd /d "%~dp0"
echo Starting Ghost Traffic Studio on http://localhost:5000 ...
python web_app.py
pause
