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

# ============================================================
# HELPER FUNCTIONS
# ============================================================

function Write-Success {
    param([string]$Text)
    if (-not $Silent) {
        Write-Host "  [OK] " -NoNewline -ForegroundColor Green
        Write-Host $Text
    }
}

function Write-Fail {
    param([string]$Text)
    if (-not $Silent) {
        Write-Host "  [FAIL] " -NoNewline -ForegroundColor Red
        Write-Host $Text
    }
}

function Write-Step {
    param([string]$Step, [string]$Text, [string]$Status)
    if (-not $Silent) {
        $color = "Yellow"
        if ($Status -eq "Done") { $color = "Green" }
        if ($Status -eq "Error") { $color = "Red" }
        if ($Status -eq "Warning") { $color = "DarkYellow" }
        Write-Host "  [$Step] " -NoNewline -ForegroundColor Gray
        Write-Host $Text -ForegroundColor $color
    }
}

function New-RandomHex {
    param([int]$Length = 64)
    $chars = "0123456789ABCDEF"
    $result = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $result += $chars[(Get-Random -Maximum 16)]
    }
    return $result
}

# ============================================================
# MAIN INSTALLER
# ============================================================

$ErrorActionPreference = "Continue"
$LogFile = "$ConfigDir\install.log"
$TempDir = Join-Path $env:TEMP "BP_Install_$(Get-Random)"

# Create config dir for logging
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}
Start-Transcript -Path $LogFile -Force | Out-Null

# Header
Clear-Host
Write-Host ""
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host "     Benevolent Protocol v$VERSION - Standalone Installer" -ForegroundColor Cyan
Write-Host "                                                                " -ForegroundColor Cyan
Write-Host "            No Prerequisites - Everything Included" -ForegroundColor Cyan
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host ""

# Detect architecture
$IsArm64 = $env:PROCESSOR_ARCHITECTURE -eq "ARM64"
$PythonUrl = $PYTHON_URL_X64
if ($IsArm64) { $PythonUrl = $PYTHON_URL_ARM }
$Arch = "x64"
if ($IsArm64) { $Arch = "ARM64" }

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

try {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonZip -UseBasicParsing -TimeoutSec 120
    $ProgressPreference = "Continue"
    
    if (Test-Path $PythonDir) { Remove-Item $PythonDir -Recurse -Force }
    Expand-Archive -Path $PythonZip -DestinationPath $PythonDir -Force
    Write-Success "Python extracted"
}
catch {
    Write-Fail "Python download failed: $_"
    Stop-Transcript | Out-Null
    exit 1
}

# Step 3: Configure Python environment
Write-Step "3/7" "Configuring Python environment..." "Working"

# Create ._pth file
$PthFile = Join-Path $PythonDir "python312._pth"
$PthContent = "python312.zip" + "`n." + "`nLib" + "`nLib\site-packages" + "`n" + "`nimport site" + "`n"
[System.IO.File]::WriteAllText($PthFile, $PthContent, [System.Text.Encoding]::ASCII)

# Create Lib directories
New-Item -ItemType Directory -Path "$PythonDir\Lib\site-packages" -Force | Out-Null

# Install pip
$GetPip = Join-Path $TempDir "get-pip.py"
try {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $GETPIP_URL -OutFile $GetPip -UseBasicParsing
    $ProgressPreference = "Continue"
    & "$PythonDir\python.exe" $GetPip --no-warn-script-location 2>&1 | Out-Null
    Write-Success "pip installed"
}
catch {
    Write-Step "3/7" "pip installation warning" "Warning"
}

# Step 4: Download Protocol
Write-Step "4/7" "Downloading Benevolent Protocol..." "Working"
$ProtocolZip = Join-Path $TempDir "protocol.zip"
$ExtractDir = Join-Path $TempDir "extracted"

try {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $PROTOCOL_URL -OutFile $ProtocolZip -UseBasicParsing -TimeoutSec 120
    $ProgressPreference = "Continue"
    
    Expand-Archive -Path $ProtocolZip -DestinationPath $ExtractDir -Force
    
    # Find source directory
    $SourceDir = Get-ChildItem "$ExtractDir\benevolent_protocol*" -Directory | Select-Object -First 1
    
    # Copy files - remove existing first
    if (Test-Path "$InstallDir\src") { Remove-Item "$InstallDir\src" -Recurse -Force }
    if (Test-Path "$InstallDir\config") { Remove-Item "$InstallDir\config" -Recurse -Force }
    
    Copy-Item -Path "$SourceDir\src" -Destination "$InstallDir\src" -Recurse -Force
    Copy-Item -Path "$SourceDir\config" -Destination "$InstallDir\config" -Recurse -Force
    Copy-Item -Path "$SourceDir\requirements.txt" -Destination "$InstallDir\" -Force
    Copy-Item -Path "$SourceDir\LICENSE" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$SourceDir\README.md" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue
    
    Write-Success "Protocol files copied"
}
catch {
    Write-Fail "Protocol download failed: $_"
    Stop-Transcript | Out-Null
    exit 1
}

# Step 5: Install dependencies
Write-Step "5/7" "Installing Python dependencies..." "Working"
$PythonExe = Join-Path $PythonDir "python.exe"
$RequirementsFile = Join-Path $InstallDir "requirements.txt"

if (Test-Path $RequirementsFile) {
    $env:PYTHONPATH = $InstallDir
    $pipOutput = & $PythonExe -m pip install -r $RequirementsFile --no-warn-script-location 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
    } else {
        Write-Step "5/7" "Some dependencies failed (non-critical)" "Warning"
    }
} else {
    Write-Step "5/7" "No requirements.txt - skipping" "Warning"
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

# Step 7: Create helper scripts
Write-Step "7/7" "Setting up system integration..." "Working"

# Start script with PYTHONPATH
$StartBatContent = "@echo off`ncd /d `"$InstallDir`"`nset PYTHONPATH=$InstallDir`n`"$PythonExe`" -m src.core.orchestrator --config `"$ConfigDir\config.json`"`npause"
[System.IO.File]::WriteAllText("$InstallDir\start.bat", $StartBatContent, [System.Text.Encoding]::ASCII)

# Stop script
$StopBatContent = "@echo off`necho Stopping Benevolent Protocol...`ntaskkill /F /FI `"WINDOWTITLE eq Benevolent*`" 2>nul`nwmic process where `"CommandLine like '%%orchestrator%%'`" delete 2>nul`necho Protocol stopped.`npause"
[System.IO.File]::WriteAllText("$InstallDir\stop.bat", $StopBatContent, [System.Text.Encoding]::ASCII)

# Status script
$StatusBatContent = "@echo off`necho.`necho  Benevolent Protocol Status`necho  ==========================`necho.`nwmic process where `"CommandLine like '%%orchestrator%%'`" get ProcessId 2>nul | find `"python`" >nul`nif %ERRORLEVEL%==0 (echo  Status: RUNNING) else (echo  Status: STOPPED)`necho.`necho  Install: $InstallDir`necho  Config:  $ConfigDir\config.json`necho.`npause"
[System.IO.File]::WriteAllText("$InstallDir\status.bat", $StatusBatContent, [System.Text.Encoding]::ASCII)

# Uninstall script
$UninstallBatContent = "@echo off`necho Uninstalling Benevolent Protocol...`nschtasks /delete /tn `"BenevolentProtocol`" /f 2>nul`nnetsh advfirewall firewall delete rule name=`"Benevolent Protocol`" 2>nul`nrmdir /s /q `"$InstallDir`" 2>nul`nrmdir /s /q `"$ConfigDir`" 2>nul`ndel `"%USERPROFILE%\Desktop\Benevolent Protocol.lnk`" 2>nul`necho Uninstall complete.`npause"
[System.IO.File]::WriteAllText("$InstallDir\uninstall.bat", $UninstallBatContent, [System.Text.Encoding]::ASCII)

Write-Success "Helper scripts created"

# Create scheduled task using schtasks (more compatible)
$TaskName = "BenevolentProtocol"
$TaskCmd = "cmd /c cd /d `"$InstallDir`" && set PYTHONPATH=$InstallDir && `"$PythonExe`" -m src.core.orchestrator --config `"$ConfigDir\config.json`""

# Delete existing task
schtasks /delete /tn $TaskName /f 2>&1 | Out-Null

# Create task (run at login, highest privileges)
$TaskCreate = schtasks /create /tn $TaskName /tr $TaskCmd /sc onlogon /rl highest /f 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Scheduled task created"
} else {
    Write-Step "7/7" "Scheduled task creation had issues" "Warning"
}

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
    Write-Step "7/7" "Desktop shortcut skipped" "Warning"
}

# Cleanup
Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue

# ============================================================
# SUMMARY
# ============================================================

Write-Host ""
Write-Host "  ================================================================" -ForegroundColor Green
Write-Host "                  Installation Complete!" -ForegroundColor Green
Write-Host "  ================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Installation Directory:" -ForegroundColor White
Write-Host "    $InstallDir" -ForegroundColor Gray
Write-Host ""
Write-Host "  Configuration:" -ForegroundColor White
Write-Host "    $ConfigDir\config.json" -ForegroundColor Gray
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
        if ($Response -eq "n" -or $Response -eq "N") {
            $StartNow = $false
        } else {
            $StartNow = $true
        }
    }
    
    if ($StartNow) {
        Write-Host ""
        Write-Host "  Starting protocol..." -ForegroundColor Yellow
        Start-Process -FilePath "$InstallDir\start.bat" -WorkingDirectory $InstallDir
        Start-Sleep -Seconds 3
        Write-Success "Protocol started in new window"
    }
}

Write-Host ""
Write-Host "  Installation log: $LogFile" -ForegroundColor DarkGray
Write-Host ""

Stop-Transcript | Out-Null
exit 0
