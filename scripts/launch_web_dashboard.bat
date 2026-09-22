@echo off
title AI Reel Studio Dashboard
cd /d "%~dp0\.."
echo Launching AI Reel Studio Web Dashboard on http://localhost:8501...
python -m streamlit run app.py
pause
