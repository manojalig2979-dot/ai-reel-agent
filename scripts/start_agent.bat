@echo off
title AI Reel Agent Daily Scheduler
cd /d "%~dp0\.."
echo ========================================================
echo        AI REEL GENERATOR - 24/7 DAILY SCHEDULER
echo ========================================================
echo.
echo Starting daily automation scheduler (Runs daily at 09:00 PM)...
echo.
python run_cli.py --schedule --time 21:00
pause
