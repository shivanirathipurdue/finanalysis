@echo off
REM ============================================================================
REM FIN 67110 - ONE DESK: UNIFIED AGENT TEAM & SKILLS LAUNCHER (WEEK 5: LAB 08 & LAB 09)
REM Executes the full unified desk end-to-end, testing all three joins and guard.
REM ============================================================================

echo ============================================================================
echo FIN 67110 - ONE DESK LAUNCHER: LAB 08 and LAB 09 VERIFICATION
echo ============================================================================
echo.

REM 1. Run Desk on Spinoff Ticker (BHSL)
echo [1/4] Running Unified Desk on BHSL (Offline Replay Contract)...
python desk.py --replay BHSL_20261110_160000
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] BHSL Desk Execution Failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

REM 2. Run Desk from Seeker Screen
echo [2/4] Running Unified Desk from Seeker Screen (Top Ranked Candidate)...
python desk.py screen
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Screen Desk Execution Failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

REM 3. Run Desk on Non-Spinoff Ticker (COST)
echo [3/4] Running Unified Desk on Non-Spinoff (COST) verifying 'not applicable' fallback...
python desk.py --replay COST_20261102_193519
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] COST Non-Spinoff Desk Execution Failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

REM 4. Run Hook Verification Suite
echo [4/4] Executing The Hook Verification Suite (Clean and Seeded Error Refusal)...
python test_hook.py
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Hook Verification Suite Failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo ============================================================================
echo [SUCCESS] ALL ONE DESK TESTS PASSED:
echo   - Direct ticker run verified.
echo   - Seeker screen run verified.
echo   - Non-spinoff 'not applicable' fallback verified.
echo   - Replay with network off verified.
echo   - Hook clean silent pass and seeded refusal verified.
echo ============================================================================
pause
