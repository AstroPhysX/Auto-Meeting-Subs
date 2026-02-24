# Requires: PowerShell 5+ (comes with Windows 10+)
# Run with: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\install.ps1

$ErrorActionPreference = "Stop"

$AppName = "Auto-Meeting-Subs"
$AppID = "Auto-Meeting-Subs"
$UserProfile = [Environment]::GetFolderPath("UserProfile")
$InstallDir = "$UserProfile\AppData\Local\$AppID"
$PythonVersion = "3.10"
$PythonExe = "python3.10.exe"
$PythonInstallUrl = "https://www.python.org/ftp/python/3.10.15/python-3.10.15-amd64.exe"
$StartMenuDir = "$UserProfile\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\$AppID"
$IconPath = "$InstallDir\icons\windows.ico"

Write-Host "Installing $AppName..."

# Function: Install Python 3.10 if missing
function Install-Python {
    Write-Host "Python 3.10 not found. Downloading and installing..."
    $Installer = "$env:TEMP\python-3.10.15-amd64.exe"
    Invoke-WebRequest $PythonInstallUrl -OutFile $Installer
    Start-Process -FilePath $Installer -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1" -Wait
    Remove-Item $Installer
}

# Check Python
try {
    $python = & python3.10 --version
} catch {
    Install-Python
}

# Verify Python installed
try {
    & python3.10 --version
} catch {
    Write-Host "Python 3.10 installation failed. Please install manually from https://www.python.org/downloads/release/python-310/"
    exit 1
}

# Create install directory
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Copy code folder into install dir
Copy-Item -Recurse -Force -Path ".\code\*" -Destination $InstallDir

# Copy icons folder into install dir
Copy-Item -Recurse -Force -Path ".\icons\*" -Destination "$InstallDir\icons"

# --- Copy uninstall scripts ---
$UninstallPs1Source = Join-Path $PSScriptRoot "uninstall.ps1"
$UninstallPs1Dest   = Join-Path $InstallDir "uninstall.ps1"

$UninstallBatSource = Join-Path $PSScriptRoot "..\uninstall.bat"  # adjust path if needed
$UninstallBatDest   = Join-Path $InstallDir "uninstall.bat"

if (Test-Path $UninstallPs1Source) {
    Copy-Item -Path $UninstallPs1Source -Destination $UninstallPs1Dest -Force
    Write-Host "Uninstall.ps1 copied to $InstallDir"
} else {
    Write-Warning "uninstall.ps1 not found in installer directory!"
}

if (Test-Path $UninstallBatSource) {
    Copy-Item -Path $UninstallBatSource -Destination $UninstallBatDest -Force
    Write-Host "Uninstall.bat copied to $InstallDir"
} else {
    Write-Warning "uninstall.bat not found in installer directory!"
}

# Create virtual environment
Set-Location $InstallDir
& python3.10 -m venv venv

# Activate venv and install requirements
$VenvActivate = "$InstallDir\venv\Scripts\Activate.ps1"
& $VenvActivate
pip install --upgrade pip
pip install -r "$InstallDir\requirements.txt"

# Create launcher script in install dir
$Launcher = "$InstallDir\launch.ps1"
@"
`$Venv = '$InstallDir\venv\Scripts\Activate.ps1'
.`$Venv
python '$InstallDir\main.py' `$args
"@ | Set-Content $Launcher
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# Make launcher executable
# Users can double-click this launcher to run

# Create Start Menu shortcut
New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null
$Shortcut = "$StartMenuDir\$AppName.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$ShortcutObject = $WScriptShell.CreateShortcut($Shortcut)
$ShortcutObject.TargetPath = "powershell.exe"
$ShortcutObject.Arguments = "-ExecutionPolicy Bypass -File `"$Launcher`""
$ShortcutObject.IconLocation = $IconPath
$ShortcutObject.WorkingDirectory = $InstallDir
$ShortcutObject.Save()

Write-Host "Installation complete!"
Write-Host "You can launch $AppName from Start Menu or by running $Launcher"