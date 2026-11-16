@echo off
title Ghost Traffic - Quick Setup & Requirements Installer
echo ============================================================
echo   GHOST TRAFFIC // ONE-CLICK SETUP & INSTALLER
echo ============================================================
echo.
echo [1/3] Python installation check kar rahe hain...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Python install nahi hai ya PATH me add nahi hai!
    echo     Kripya python.org se Python 3.10 ya newer install karein.
    echo     NOTE: Install karte waqt 'Add Python to PATH' par tick zaroor karein!
    echo.
    pause
    exit /b 1
)

python --version
echo [✓] Python detected!
echo.
echo [2/3] Python dependencies install kar rahe hain...
pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo [!] ERROR: Pip package install fail ho gaya. Internet connection check karein.
    pause
    exit /b 1
)
echo [✓] Dependencies installed!
echo.
echo [3/3] Playwright Chromium browser install kar rahe hain...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [!] ERROR: Playwright browser install fail ho gaya.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [✓] SUCCESS: SETUP COMPLETELY DONE!
echo.
echo Ab aap:
echo 1. 'outputs' folder me apni vertical .mp4 reels daalo.
echo 2. '1_Login_Account_1.bat' chala kar Instagram login karo.
echo 3. '2_Post_Single_Reel.bat' se reels post karna shuru karo!
echo ============================================================
echo.
pause
