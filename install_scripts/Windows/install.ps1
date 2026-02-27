# Requires: PowerShell 5+
# Run with:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\install.ps1

$ErrorActionPreference = "Stop"

$AppName = "Auto-Meeting-Subs"
$AppID = "auto-meeting-subs"
$UserProfile = [Environment]::GetFolderPath("UserProfile")
$InstallDir = "$UserProfile\AppData\Local\$AppID"
$StartMenuDir = "$UserProfile\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\$AppID"
$IconPath = "$InstallDir\icons\windows.ico"

# ----------------------------
# Python (Embedded)
# ----------------------------
$PythonVersion = "3.10.11"
$PythonEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$PythonDir = "$InstallDir\python"
$PythonExe = "$PythonDir\python.exe"

$VCRedistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$VCRedistInstaller = "$env:TEMP\vc_redist.x64.exe"

Write-Host "Installing $AppName..."

# ----------------------------
# Create install directory
# ----------------------------
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $PythonDir | Out-Null

# ----------------------------
# Download & Extract Embedded Python
# ----------------------------
if (!(Test-Path $PythonExe)) {

    Write-Host "Downloading embedded Python $PythonVersion..."
    $TempZip = "$env:TEMP\python-embed.zip"

    Invoke-WebRequest $PythonEmbedUrl -OutFile $TempZip
    Expand-Archive $TempZip -DestinationPath $PythonDir -Force
    Remove-Item $TempZip

    Write-Host "Python extracted to $PythonDir"

    # Enable site-packages (required)
    $PthFile = Get-ChildItem "$PythonDir\python310._pth"

    $PthContent = Get-Content $PthFile.FullName

    # Enable site
    $PthContent = $PthContent -replace "#import site", "import site"

    # Add application root to sys.path (VERY IMPORTANT)
    if ($PthContent -notcontains "..") {
        $PthContent += ".."
    }

    Set-Content $PthFile.FullName $PthContent
}

# ----------------------------
# Verify Python
# ----------------------------
& $PythonExe --version

# ----------------------------
# Install pip (embed does not include it)
# ----------------------------
Write-Host "Bootstrapping pip..."
$GetPip = "$env:TEMP\get-pip.py"
Invoke-WebRequest https://bootstrap.pypa.io/get-pip.py -OutFile $GetPip
& $PythonExe $GetPip
Remove-Item $GetPip

# ----------------------------
# Copy Application Files
# ----------------------------
Copy-Item -Recurse -Force ".\code\*" -Destination $InstallDir
Copy-Item -Recurse -Force ".\icons\*" -Destination "$InstallDir\icons"

# ----------------------------
# Install Requirements (into embedded Python)
# ----------------------------
Write-Host "Installing dependencies..."
& "$PythonDir\Scripts\pip.exe" install --upgrade pip --no-warn-script-location
& "$PythonDir\Scripts\pip.exe" install -r "$InstallDir\requirements.txt" --no-warn-script-location
# ----------------------------
# Install Microsoft Visual C++ Redistributable
# ----------------------------
Write-Host "Installing Microsoft Visual C++ Redistributable..."

$VCRedistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$VCRedistInstaller = "$env:TEMP\vc_redist.x64.exe"

# Download
Invoke-WebRequest $VCRedistUrl -OutFile $VCRedistInstaller

# Install silently
& $VCRedistInstaller /quiet /norestart

# Wait for installation to complete
Start-Sleep -Seconds 5

Write-Host "Visual C++ Redistributable installed successfully"

# ----------------------------
# Create Launcher (direct execution)
# ----------------------------
$Launcher = Join-Path $InstallDir "launch.ps1"

$LauncherContent = @"
Set-Location '$InstallDir'
& '$PythonExe' 'main.py'
"@

# Use -Encoding UTF8 explicitly
Set-Content -Path $Launcher -Value $LauncherContent -Encoding UTF8 -Force

# Ensure the file exists and is executable
if (!(Test-Path $Launcher)) {
    Write-Error "Failed to create launcher!"
}

# ----------------------------
# Create Start Menu Shortcut
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

Write-Host ""
Write-Host "Installation complete!"
Write-Host "Fully isolated Python environment installed."
Write-Host "To uninstall: delete $InstallDir"