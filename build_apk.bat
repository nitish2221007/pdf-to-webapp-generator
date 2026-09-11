@echo off
title Build Android APK - PDF to WebApp Studio
cd /d "%~dp0"

set "JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot"
set "ANDROID_HOME=C:\Users\yniti\AppData\Local\Android\Sdk"
set "PATH=%JAVA_HOME%\bin;C:\Users\yniti\AppData\Local\Programs\Gradle\gradle-9.6.0\bin;%PATH%"

echo =======================================================
echo   Building PDF to WebApp Studio Android APK...
echo =======================================================

cd android
cmd /c gradle assembleDebug

if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo.
    echo Copying APK to dist/PDF_to_WebApp_Studio.apk...
    if not exist "..\dist" mkdir "..\dist"
    copy /y "app\build\outputs\apk\debug\app-debug.apk" "..\dist\PDF_to_WebApp_Studio.apk"
    echo.
    echo SUCCESS! APK Generated at: dist/PDF_to_WebApp_Studio.apk
) else (
    echo.
    echo APK Build failed or APK not found in expected folder.
)

pause
