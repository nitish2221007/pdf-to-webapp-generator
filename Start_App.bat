@echo off
title PDF to HTML+CSS Converter Studio
cd /d "%~dp0"
echo =======================================================
echo   Starting PDF to HTML+CSS Converter WebApp Studio...
echo =======================================================
start "" http://localhost:8090
python app.py
pause
