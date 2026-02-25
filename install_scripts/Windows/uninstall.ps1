# Requires: PowerShell 5+
# Run with: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\uninstall.ps1

$ErrorActionPreference = "Stop"

$AppName = "Auto-Meeting-Subs"
$AppID = "auto-meeting-subs"
$UserProfile = [Environment]::GetFolderPath("UserProfile")
$InstallDir = "$UserProfile\AppData\Local\$AppID"
$StartMenuDir = "$UserProfile\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\$AppID"

Write-Host "Uninstalling $AppName..."

# Remove install directory
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
    Write-Host "Removed install directory: $InstallDir"
} else {
    Write-Host "Install directory not found: $InstallDir"
}

# Remove Start Menu shortcut
if (Test-Path $StartMenuDir) {
    Remove-Item -Recurse -Force $StartMenuDir
    Write-Host "Removed Start Menu shortcuts: $StartMenuDir"
} else {
    Write-Host "Start Menu shortcuts not found: $StartMenuDir"
}

Write-Host "Uninstallation complete!"
Write-Host "This did not uninstall ollama as other app might depend on them"