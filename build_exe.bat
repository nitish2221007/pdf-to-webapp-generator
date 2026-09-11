@echo off
title Build EXE - PDF to WebApp Studio
cd /d "%~dp0"
echo =======================================================
echo   Building Standalone EXE for PDF to WebApp Studio...
echo =======================================================
pyinstaller --noconfirm --onedir --name PDF_to_WebApp_Studio --add-data "templates;templates" --add-data "static;static" app.py
echo.
echo Build completed! Output available in dist/PDF_to_WebApp_Studio/
pause
