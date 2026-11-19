@echo off
cd /d "C:\Users\cashi\Desktop\MS Finance\Mod 2\67110 Mastering AI for Finance"
echo ========================================================
echo RUNNING SEEKER UNIT TEST SUITE
echo ========================================================
".\equity_research\.venv\Scripts\python.exe" test_seeker.py
echo.
echo ========================================================
echo RUNNING SPINOFF SEEKER (START DATE: 2025-11-01)
echo ========================================================
".\equity_research\.venv\Scripts\python.exe" seeker.py --start-date 2025-11-01
echo.
pause
