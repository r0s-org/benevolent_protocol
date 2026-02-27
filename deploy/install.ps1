# Benevolent Protocol - Windows Installation Script
# Run as Administrator
# Usage: .\install.ps1

param(
    [string]$InstallDir = "C:\Program Files\BenevolentProtocol",
    [string]$ConfigDir = "C:\ProgramData\BenevolentProtocol",
    [string]$LogFile = "C:\ProgramData\BenevolentProtocol\install.log",
    [switch]$Silent = $false
)

#Requires -RunAsAdministrator

# Version
$VERSION = "0.3.0-alpha"
$REPO_URL = "https://github.com/r0s-org/benevolent_protocol"
$RELEASE_URL = "https://github.com/r0s-org/benevolent_protocol/archive/refs/heads/main.zip"

# Colors (if not silent)
function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Write-ErrorMsg {
    param([string]$Message)
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor Red
    }
}

function Write-WarningMsg {
    param([string]$Message)
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor Yellow
    }
}

# Generate hex string (PowerShell 5.1 compatible)
function New-HexString {
    param([int]$Length = 64)
    $chars = "0123456789ABCDEF"
    $result = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $result += $chars[(Get-Random -Maximum 16)]
    }
    return $result
}

# Start logging
Start-Transcript -Path $LogFile -Force | Out-Null

Write-Status ""
Write-Status "=== Benevolent Protocol v$VERSION Installer ===" "Cyan"
Write-Status ""

# Check Windows version
$WindowsVersion = [System.Environment]::OSVersion.Version
if ($WindowsVersion.Major -lt 10) {
    Write-ErrorMsg "Windows 10 or later is required."
    Stop-Transcript | Out-Null
    exit 1
}
Write-Status "Windows $($WindowsVersion.Major).$($WindowsVersion.Minor) detected"

# Check Python
Write-Status ""
Write-Status "Checking Python installation..." "Yellow"

$PythonCmd = $null
$PythonVersion = $null
$PythonPath = $null

# Check common Python locations
$PythonPaths = @(
    "${env:LOCALAPPDATA}\Programs\Python\Python311\python.exe",
    "${env:LOCALAPPDATA}\Programs\Python\Python310\python.exe",
    "${env:LOCALAPPDATA}\Programs\Python\Python39\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe",
    "C:\Python39\python.exe"
)

# Try py launcher first (official Python installer includes this)
try {
    $pyVersion = py --version 2>&1
    if ($pyVersion -match "Python (\d+\.\d+)") {
        $PythonVersion = $Matches[1]
        $PythonCmd = "py"
        $PythonPath = (Get-Command py -ErrorAction SilentlyContinue).Source
    }
}
catch {}

# Try python command
if (-not $PythonCmd) {
    try {
        $verOutput = python --version 2>&1
        if ($verOutput -match "Python (\d+\.\d+)") {
            $PythonVersion = $Matches[1]
            $PythonCmd = "python"
            $PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        }
    }
    catch {}
}

# Check known paths
if (-not $PythonCmd) {
    foreach ($path in $PythonPaths) {
        if (Test-Path $path) {
            try {
                $verOutput = & $path --version 2>&1
                if ($verOutput -match "Python (\d+\.\d+)") {
                    $PythonVersion = $Matches[1]
                    $PythonCmd = $path
                    $PythonPath = $path
                    break
                }
            }
            catch {}
        }
    }
}

# Check if we found Python
if (-not $PythonCmd) {
    Write-ErrorMsg "Python 3.10+ is not installed."
    Write-Status ""
    Write-WarningMsg "Please install Python from:"
    Write-WarningMsg "  https://www.python.org/downloads/"
    Write-Status ""
    Write-WarningMsg "IMPORTANT: Check 'Add Python to PATH' during installation!"
    Write-Status ""
    Write-Status "Or install via winget:"
    Write-Status "  winget install Python.Python.3.12"
    Write-Status ""
    Stop-Transcript | Out-Null
    exit 1
}

# Check version
$VersionParts = $PythonVersion.Split(".")
if ([int]$VersionParts[0] -lt 3 -or ([int]$VersionParts[0] -eq 3 -and [int]$VersionParts[1] -lt 10)) {
    Write-ErrorMsg "Python 3.10+ is required. Found: $PythonVersion"
    Write-Status ""
    Write-WarningMsg "Please upgrade Python from:"
    Write-WarningMsg "  https://www.python.org/downloads/"
    Stop-Transcript | Out-Null
    exit 1
}

Write-Status "Python $PythonVersion found ($PythonCmd)"

# Create directories
Write-Status ""
Write-Status "Creating directories..." "Yellow"

$Dirs = @($InstallDir, $ConfigDir, "$ConfigDir\logs", "$ConfigDir\data")
foreach ($Dir in $Dirs) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
}
Write-Status "Directories created"

# Download protocol
Write-Status ""
Write-Status "Downloading Benevolent Protocol..." "Yellow"

$ZipFile = "$env:TEMP\benevolent_protocol.zip"
$ExtractDir = "$env:TEMP\benevolent_protocol_extract"

try {
    # Clean up old downloads
    if (Test-Path $ZipFile) { Remove-Item $ZipFile -Force }
    if (Test-Path $ExtractDir) { Remove-Item $ExtractDir -Recurse -Force }

    # Download with progress
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $RELEASE_URL -OutFile $ZipFile -UseBasicParsing
    $ProgressPreference = 'Continue'

    # Extract
    Expand-Archive -Path $ZipFile -DestinationPath $ExtractDir -Force

    # Copy files (extracted folder has -main suffix)
    $SourceDir = Get-ChildItem "$ExtractDir\benevolent_protocol*" -Directory | Select-Object -First 1

    # Copy src, config, etc
    Copy-Item -Path "$SourceDir\src" -Destination "$InstallDir\src" -Recurse -Force
    Copy-Item -Path "$SourceDir\config" -Destination "$InstallDir\config" -Recurse -Force
    Copy-Item -Path "$SourceDir\requirements.txt" -Destination "$InstallDir\" -Force
    Copy-Item -Path "$SourceDir\LICENSE" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$SourceDir\README.md" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue

    # Cleanup
    Remove-Item $ZipFile -Force
    Remove-Item $ExtractDir -Recurse -Force

    Write-Status "Protocol downloaded and extracted"
}
catch {
    Write-ErrorMsg "Failed to download: $_"
    Stop-Transcript | Out-Null
    exit 1
}

# Create virtual environment
Write-Status ""
Write-Status "Creating virtual environment..." "Yellow"

$VenvDir = "$InstallDir\venv"

try {
    & $PythonCmd -m venv $VenvDir
    if (-not (Test-Path "$VenvDir\Scripts\python.exe")) {
        throw "Virtual environment creation failed"
    }
    Write-Status "Virtual environment created"
}
catch {
    Write-ErrorMsg "Failed to create virtual environment: $_"
    Write-WarningMsg "Make sure Python was installed with 'pip' option enabled."
    Stop-Transcript | Out-Null
    exit 1
}

# Install dependencies
Write-Status ""
Write-Status "Installing dependencies..." "Yellow"

$VenvPython = "$VenvDir\Scripts\python.exe"
$VenvPip = "$VenvDir\Scripts\pip.exe"

try {
    & $VenvPython -m pip install --upgrade pip 2>&1 | Out-Null
    & $VenvPip install -r "$InstallDir\requirements.txt" 2>&1 | ForEach-Object {
        if ($_ -match "error|ERROR|failed") {
            Write-WarningMsg $_
        }
    }
    Write-Status "Dependencies installed"
}
catch {
    Write-WarningMsg "Some dependencies may have failed: $_"
}

# Generate secure secret (PowerShell 5.1 compatible)
Write-Status ""
Write-Status "Generating secure configuration..." "Yellow"

$Secret = New-HexString -Length 64

# Create configuration
$ConfigFile = "$ConfigDir\config.json"

$Config = @{
    telemetry_enabled   = $true
    telemetry_level     = "standard"
    telemetry_endpoint  = $null
    heartbeat_interval  = 60
    command_port        = 9527
    optimization_interval = 3600
    propagation_enabled = $false
    gaming_mode_auto_detect = $true
    max_cpu_percent     = 30
    max_memory_mb       = 500
    control_secret      = $Secret
    update_endpoint     = $null
    log_level           = "INFO"
    log_file            = "$ConfigDir\logs\protocol.log"
    platform_mode       = "active"
    linux_carrier_mode  = $true
    windows_active_mode = $true
    android_active_mode = $true
    allowed_networks    = @("192.168.0.0/16", "10.0.0.0/8")
    excluded_hosts      = @()
}

$Config | ConvertTo-Json -Depth 10 | Out-File -FilePath $ConfigFile -Encoding UTF8

Write-Status "Configuration created"
Write-Status ""
Write-WarningMsg "  Configuration: $ConfigDir\config.json"
Write-WarningMsg "  Secret: $Secret"
Write-WarningMsg "  Save this secret for remote commands!"

# Create start script
Write-Status ""
Write-Status "Creating helper scripts..." "Yellow"

# Use Set-Content instead of here-strings to avoid parsing issues
$StartBat = "@echo off`ncd /d `"$InstallDir`"`ncall venv\Scripts\activate.bat`npython -m src.core.orchestrator --config `"$ConfigDir\config.json`"`npause"
Set-Content -Path "$InstallDir\start.bat" -Value $StartBat -Encoding ASCII

$StatusBat = "@echo off`necho Benevolent Protocol Status`necho ==========================`ntasklist /FI `"IMAGENAME eq python.exe`" 2>nul | find `"python.exe`" >nul`nif %ERRORLEVEL%==0 (`n    echo Status: Running`n) else (`n    echo Status: Stopped`n)`necho.`necho Config: $ConfigDir\config.json`necho Logs: $ConfigDir\logs\`npause"
Set-Content -Path "$InstallDir\status.bat" -Value $StatusBat -Encoding ASCII

$StopBat = "@echo off`necho Stopping Benevolent Protocol...`ntaskkill /F /IM `"pythonw.exe`" /FI `"WINDOWTITLE eq Benevolent*`" 2>nul`nif %ERRORLEVEL%==0 (`n    echo Protocol stopped.`n) else (`n    echo Protocol was not running.`n)`npause"
Set-Content -Path "$InstallDir\stop.bat" -Value $StopBat -Encoding ASCII

Write-Status "Helper scripts created"

# Create scheduled task for auto-start
Write-Status ""
Write-Status "Setting up scheduled task..." "Yellow"

$TaskName = "BenevolentProtocol"
$TaskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($TaskExists) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction `
    -Execute "$InstallDir\venv\Scripts\pythonw.exe" `
    -Argument "-m src.core.orchestrator --config `"$ConfigDir\config.json`"" `
    -WorkingDirectory $InstallDir

$Trigger = New-ScheduledTaskTrigger -AtLogon

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Benevolent Protocol - System optimization service" | Out-Null

Write-Status "Scheduled task created (starts at login)"

# Add firewall rule
Write-Status ""
Write-Status "Configuring firewall..." "Yellow"

$FirewallRule = Get-NetFirewallRule -DisplayName "Benevolent Protocol" -ErrorAction SilentlyContinue
if ($FirewallRule) {
    Remove-NetFirewallRule -DisplayName "Benevolent Protocol"
}

New-NetFirewallRule `
    -DisplayName "Benevolent Protocol" `
    -Direction Inbound `
    -LocalPort 9527 `
    -Protocol TCP `
    -Action Allow `
    -Profile Private | Out-Null

Write-Status "Firewall configured (port 9527)"

# Create desktop shortcut
Write-Status ""
Write-Status "Creating shortcuts..." "Yellow"

try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut("$env:USERPROFILE\Desktop\Benevolent Protocol.lnk")
    $Shortcut.TargetPath = "$InstallDir\start.bat"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "Start Benevolent Protocol"
    $Shortcut.Save()
    Write-Status "Desktop shortcut created"
}
catch {
    Write-WarningMsg "Could not create desktop shortcut: $_"
}

# Summary
Write-Status ""
Write-Status "=== Installation Complete ===" "Cyan"
Write-Status ""
Write-Status "Installation Directory: $InstallDir"
Write-Status "Configuration: $ConfigDir\config.json"
Write-Status "Logs: $ConfigDir\logs\"
Write-Status ""
Write-Status "Commands:"
Write-Status "  Start:   $InstallDir\start.bat"
Write-Status "  Stop:    $InstallDir\stop.bat"
Write-Status "  Status:  $InstallDir\status.bat"
Write-Status "  Task:    Start-ScheduledTask -TaskName BenevolentProtocol"
Write-Status ""
Write-WarningMsg "IMPORTANT: Edit $ConfigDir\config.json before starting!"
Write-WarningMsg "The protocol will start automatically at login."
Write-Status ""

# Start now?
if (-not $Silent) {
    $StartNow = Read-Host "Start Benevolent Protocol now? (Y/n)"
    if ($StartNow -ne "n" -and $StartNow -ne "N") {
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
        Write-Status "Protocol started!" "Green"
    }
}

Stop-Transcript | Out-Null

Write-Status ""
Write-Status "Installation log saved to: $LogFile"
Write-Status ""
Write-Status "Protocol installed successfully!" "Green"
