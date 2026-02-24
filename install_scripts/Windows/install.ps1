# Requires: PowerShell 5+ (comes with Windows 10+)
# Run with: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\install.ps1

$ErrorActionPreference = "Stop"

$AppName = "Auto-Meeting-Subs"
$AppID = "Auto-Meeting-Subs"
$UserProfile = [Environment]::GetFolderPath("UserProfile")
$InstallDir = "$UserProfile\AppData\Local\$AppID"
$StartMenuDir = "$UserProfile\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\$AppID"
$IconPath = "$InstallDir\icons\windows.ico"

# Python settings
$PythonVersion = "3.10.11"
$PythonEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$PythonDir = "$InstallDir\python"
$PythonExe = "$PythonDir\python.exe"

Write-Host "Installing $AppName..."

# ----------------------------
# Function: Install Python via embeddable ZIP
# ----------------------------
function Install-Python {
    Write-Host "Python 3.10 not found. Downloading embeddable zip..."
    $TempZip = "$env:TEMP\python-$PythonVersion-embed-amd64.zip"
    Invoke-WebRequest $PythonEmbedUrl -OutFile $TempZip
    Expand-Archive -Path $TempZip -DestinationPath $PythonDir
    Remove-Item $TempZip
    Write-Host "Python 3.10 extracted to $PythonDir"
}

# ----------------------------
# Check if Python exists
# ----------------------------
if (!(Test-Path $PythonExe)) {
    Install-Python
}

# Verify Python works
try {
    & $PythonExe --version
} catch {
    Write-Host "Python installation failed. Please install manually."
    exit 1
}

# ----------------------------
# Prepare installation directory
# ----------------------------
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Copy code folder into install dir
Copy-Item -Recurse -Force -Path ".\code\*" -Destination $InstallDir

# Copy icons folder into install dir
Copy-Item -Recurse -Force -Path ".\icons\*" -Destination "$InstallDir\icons"

# ----------------------------
# Copy uninstall scripts
# ----------------------------
$UninstallPs1Source = Join-Path $PSScriptRoot "uninstall.ps1"
$UninstallPs1Dest   = Join-Path $InstallDir "uninstall.ps1"

$UninstallBatSource = Join-Path $PSScriptRoot "..\uninstall.bat"
$UninstallBatDest   = Join-Path $InstallDir "uninstall.bat"

if (Test-Path $UninstallPs1Source) { Copy-Item $UninstallPs1Source -Destination $UninstallPs1Dest -Force }
if (Test-Path $UninstallBatSource) { Copy-Item $UninstallBatSource -Destination $UninstallBatDest -Force }

# ----------------------------
# Create virtual environment
# ----------------------------
Set-Location $InstallDir
& $PythonExe -m venv venv

# Upgrade pip and install requirements
$VenvPython = "$InstallDir\venv\Scripts\python.exe"
$VenvPip = "$InstallDir\venv\Scripts\pip.exe"
& $VenvPip install --upgrade pip
& $VenvPip install -r "$InstallDir\requirements.txt"

# ----------------------------
# Create launcher script
# ----------------------------
$Launcher = "$InstallDir\launch.ps1"
@"
`$Venv = '$InstallDir\venv\Scripts\Activate.ps1'
.`$Venv
python '$InstallDir\main.py' `$args
"@ | Set-Content $Launcher
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# ----------------------------
# Create Start Menu shortcut
# ----------------------------
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