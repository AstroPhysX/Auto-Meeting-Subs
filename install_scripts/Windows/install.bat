@echo off
echo Installing Auto-Meeting-Subs...
PowerShell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0scripts\install.ps1\"' -Verb RunAs"
echo.
pause