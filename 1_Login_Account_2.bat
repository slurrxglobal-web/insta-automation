@echo off
title Ghost Traffic - Login Instagram Account 2
echo ============================================================
echo   GHOST TRAFFIC // INSTAGRAM ACCOUNT 2 LOGIN (insta_02)
echo ============================================================
echo.
echo Opening Google Chrome with isolated profile for Account 2...
echo.
echo [1] Apna Instagram ID aur Password daal kar login karo.
echo [2] OTP complete karo jab feed dikhne lage.
echo [3] IMPORTANT: Login hone ke baad Chrome window ko [X] CLOSE karo!
echo.
set "CHROME_EXE="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE (
    echo [!] Google Chrome nahi mila! Kripya pehle Google Chrome install karein.
    pause
    exit /b
)

start /wait "" "%CHROME_EXE%" --user-data-dir="%~dp0auto_poster\profiles\insta_02" --no-first-run --no-default-browser-check https://www.instagram.com/
echo.
echo Chrome closed. Checking session...
cd /d "%~dp0auto_poster"
python -c "from status_cli import is_account_logged_in, load_accounts; acc = load_accounts()[1]; st = is_account_logged_in(acc); print('\n[✓] SUCCESS: Account 2 is Logged In and Ready to Post!' if st is True else '\n[!] Login not detected or incomplete. Dobara login karo.')"
echo.
echo Ab aap '2_Post_Single_Reel.bat' chala sakte hain!
echo ============================================================
pause
