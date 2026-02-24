@echo off
echo Uninstalling Auto-Meeting-Subs...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall.ps1"
echo.
pause