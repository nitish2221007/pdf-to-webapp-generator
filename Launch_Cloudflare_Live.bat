@echo off
title PDF to HTML Converter Studio - Cloudflare Live Host
echo ======================================================================
echo    Starting PDF to HTML Studio with Cloudflare Public Live URL...
echo ======================================================================

start "" /B python app.py
timeout /t 2 /nobreak >nul

echo Starting Cloudflare Tunnel...
cloudflared.exe tunnel --protocol http2 --url http://localhost:8090

pause
