@echo off
title AI Reel Studio Dashboard
cd /d "%~dp0\.."
echo Launching AI Reel Studio on http://localhost:8501...
python scripts\launch_desktop_app.py
pause

