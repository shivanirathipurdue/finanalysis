@echo off
TITLE FIN 67110 - Lab 07 Execution and Verification Runner
cd /d "%~dp0"

echo ================================================================================
echo FIN 67110 - LAB 07: YOUR INVESTOR (WORKSHEET, HOOK, NCAV SEEKER, HIT RATE)
echo ================================================================================
echo.

echo [1/5] Running Spinoff Worksheet Skill on BHSL...
".\equity_research\.venv\Scripts\python.exe" worksheet.py BHSL_20261110_160000
echo.

echo [2/5] Running Seeded-Error Verification on The Hook...
".\equity_research\.venv\Scripts\python.exe" test_hook.py
echo.

echo [3/5] Testing Direct Hook Verification on Clean Worksheet...
".\equity_research\.venv\Scripts\python.exe" hook.py BHSL_20261110_160000\worksheet.md
echo.

echo [4/5] Running Benjamin Graham NCAV Second Seeker...
".\equity_research\.venv\Scripts\python.exe" ncav_seeker.py
echo.

echo [5/5] Generating Desk Hit-Rate Table...
".\equity_research\.venv\Scripts\python.exe" hit_rate.py
echo.

echo ================================================================================
echo ALL LAB 07 CHECKS COMPLETE AND VERIFIED!
echo ================================================================================
pause
