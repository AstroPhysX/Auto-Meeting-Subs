# Requires: PowerShell 5+
# Run with:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\install.ps1
if (-not (Get-Command Start-ThreadJob -ErrorAction SilentlyContinue)){
    Install-Module ThreadJob -Scope CurrentUser
}
if (-not (Get-Command wmic -ErrorAction SilentlyContinue)){
    Enable-WindowsOptionalFeature -Online -FeatureName "WmiCmdlets"
}

try{
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
$Major, $Minor, $Patch = $PythonVersion -split '\.'
$PythonEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$PythonDir = "$InstallDir\python"
$PythonExe = "$PythonDir\python.exe"

$VCRedistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$VCRedistInstaller = "$env:TEMP\vc_redist.x64.exe"

Write-Host "Installing $AppName..."

# Get directory of this .ps1 script (like BASH_SOURCE[0])
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Set log file next to the script
$LOG_FILE = Join-Path $SCRIPT_DIR "install.log"
# Ensure directory exists (usually already does, but safe)
New-Item -ItemType Directory -Force -Path $SCRIPT_DIR | Out-Null
# Clear old log
New-Item -ItemType File -Force -Path $LOG_FILE | Out-Null

function Start-Spinner {
    param([int]$JobId)

    $spin = @('-', '\', '|', '/')
    $i = 0

    while ((Get-Job -Id $JobId).State -eq "Running") {
        $char = $spin[$i % $spin.Length]
        Write-Host -NoNewline "`r -Working... $char"
        Start-Sleep -Milliseconds 100
        $i++
    }

    Write-Host -NoNewline "`r"
}

function run-step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host "> $Label..."

    $job = Start-ThreadJob -ScriptBlock {
        param($cmd, $log)

        try {
            & $cmd *>> $log
            return 0
        }
        catch {
            $_ | Out-String | Out-File -Append -FilePath $log
            return 1
        }

    } -ArgumentList $Command, $LOG_FILE

    Start-Spinner -JobId $job.Id

    Wait-Job $job | Out-Null
    $exitCode = Receive-Job $job
    Remove-Job $job

    Write-Host -NoNewline "`r`e[0K"

    if ($exitCode -ne 0) {
        Write-Host "X Failed: $Label"
        Write-Host "   See log: $LOG_FILE"
        exit 1
    }

    Write-Host "> Done!!"
}
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

    Import-Module Microsoft.PowerShell.Utility
    run-step -Label "Downloading embedded Python $PythonVersion..." -Command {
        Invoke-WebRequest $PythonEmbedUrl -OutFile $TempZip
    }
    Expand-Archive $TempZip -DestinationPath $PythonDir -Force
    Remove-Item $TempZip

    Write-Host "Python extracted to $PythonDir"

    # Enable site-packages (required)
    $PthFile = Get-ChildItem "$PythonDir\python$Major$Minor._pth"

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
$GetPip = "$env:TEMP\get-pip.py"
run-step "Bootstrapping pip..." {Invoke-WebRequest https://bootstrap.pypa.io/get-pip.py -OutFile $GetPip
    & $PythonExe $GetPip
}
Remove-Item $GetPip

# ----------------------------
# Copy Application Files
# ----------------------------
Copy-Item -Recurse -Force ".\code\*" -Destination $InstallDir
Copy-Item -Recurse -Force ".\icons\*" -Destination "$InstallDir\icons"

# ----------------------------
# Install Requirements (into embedded Python)
# ----------------------------
run-step -Label "Installing Python dependencies..." -Command {
    & "$PythonDir\Scripts\pip.exe" install --upgrade pip --no-warn-script-location
    & "$PythonDir\Scripts\pip.exe" install -r "$InstallDir\requirements.txt" --no-warn-script-location
}
# ----------------------------
# Install Microsoft Visual C++ Redistributable
# ----------------------------
if (-not (Get-Package | Where-Object { $_.Name -like "*Visual C++*" })){
$VCRedistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$VCRedistInstaller = "$env:TEMP\vc_redist.x64.exe"


run-step -Label "Installing Microsoft Visual C++ Redistributable..." -Command {
    # Download
    Invoke-WebRequest $VCRedistUrl -OutFile $VCRedistInstaller

    # Install silently
    & $VCRedistInstaller /norestart

    # Wait for installation to complete
    Write-Host "MS Visual C++ Redistributable installer should have popped up."
}
Read-Host "Press Enter to continue once MS Visual C++ Redistributable is installed..."
}
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

# Create desktop shortcut instead of Start Menu
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$Shortcut = "$DesktopDir\$AppName.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$ShortcutObject = $WScriptShell.CreateShortcut($Shortcut)
$ShortcutObject.TargetPath = "powershell.exe"
$ShortcutObject.Arguments = "-ExecutionPolicy Bypass -File `"$Launcher`""
$ShortcutObject.IconLocation = "$IconPath"
$ShortcutObject.WorkingDirectory = $InstallDir
$ShortcutObject.Save()

Write-Host ""
Write-Host "Installation complete!"
Write-Host "Fully isolated Python environment installed."
Write-Host "To uninstall: delete $InstallDir"
}
catch{
    Write-Host " X Failed, some error occurred during installation"
    Write-Host "   See log: $LOG_FILE"
    Write-Host "   If you want to reattempt to install the program after a fix, I highly recommend that you run the uninstall script prior to attempting to run the install script again."
}