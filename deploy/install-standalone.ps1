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

function New-RandomHex {
    param([int]$Length = 64)
    $chars = "0123456789ABCDEF"
    $result = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $result += $chars[(Get-Random -Maximum 16)]
    }
    return $result
}

function Invoke-Download {
    param([string]$Url, [string]$OutFile, [string]$Description)
    try {
        $ProgressPreference = "SilentlyContinue"
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 120
        $ProgressPreference = "Continue"
        return $true
    }
    catch {
        Write-Fail "Failed to download $Description"
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

$dirsToCreate = @($InstallDir, $ConfigDir, "$ConfigDir\logs", "$ConfigDir\data", $TempDir)
foreach ($dir in $dirsToCreate) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Success "Directories created"

# Step 2: Download embedded Python
Write-Step "2/7" "Downloading Python $PYTHON_VERSION (embedded)..." "Working"

$PythonZip = Join-Path $TempDir "python_embed.zip"
$PythonDir = Join-Path $InstallDir "python"

$downloadOk = Invoke-Download -Url $PythonUrl -OutFile $PythonZip -Description "Python embedded"
if ($downloadOk) {
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
$PthContent = "python312.zip" + [char]10 + "." + [char]10 + "Lib" + [char]10 + "Lib\site-packages" + [char]10 + [char]10 + "import site" + [char]10
Set-Content -Path $PthFile -Value $PthContent -Encoding ASCII -NoNewline

# Create Lib directories
New-Item -ItemType Directory -Path "$PythonDir\Lib\site-packages" -Force | Out-Null

# Download and install pip
$GetPip = Join-Path $TempDir "get-pip.py"
$pipOk = Invoke-Download -Url $GETPIP_URL -OutFile $GetPip -Description "pip installer"
if ($pipOk) {
    $pipProc = Start-Process -FilePath "$PythonDir\python.exe" -ArgumentList $GetPip, "--no-warn-script-location" -NoNewWindow -Wait -PassThru
    Write-Success "pip installed"
}
else {
    Write-Step "3/7" "pip installation warning - some features may not work" "Warning"
}

# Step 4: Download Protocol
Write-Step "4/7" "Downloading Benevolent Protocol..." "Working"

$ProtocolZip = Join-Path $TempDir "protocol.zip"

$protoOk = Invoke-Download -Url $PROTOCOL_URL -OutFile $ProtocolZip -Description "protocol from GitHub"
if (-not $protoOk) {
    $protoOk = Invoke-Download -Url $PROTOCOL_MIRROR -OutFile $ProtocolZip -Description "protocol from mirror"
}

if (-not $protoOk) {
    Write-Fail "Protocol download failed. Aborting."
    Stop-Transcript | Out-Null
    exit 1
}

# Extract protocol
$ExtractDir = Join-Path $TempDir "extracted"
Expand-Archive -Path $ProtocolZip -DestinationPath $ExtractDir -Force

# Find the source directory
$SourceDirs = Get-ChildItem "$ExtractDir\benevolent_protocol*" -Directory
$SourceDir = $SourceDirs | Select-Object -First 1

# Copy protocol files
Copy-Item -Path "$SourceDir\src" -Destination "$InstallDir\src" -Recurse -Force
Copy-Item -Path "$SourceDir\config" -Destination "$InstallDir\config" -Recurse -Force
Copy-Item -Path "$SourceDir\requirements.txt" -Destination "$InstallDir\" -Force
Copy-Item -Path "$SourceDir\LICENSE" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "$SourceDir\README.md" -Destination "$InstallDir\" -Force -ErrorAction SilentlyContinue

Write-Success "Protocol files copied"

# Step 5: Install dependencies
Write-Step "5/7" "Installing Python dependencies..." "Working"

$RequirementsFile = Join-Path $InstallDir "requirements.txt"
$PythonExe = Join-Path $PythonDir "python.exe"

if (Test-Path $RequirementsFile) {
    $pipProc = Start-Process -FilePath $PythonExe -ArgumentList "-m", "pip", "install", "-r", $RequirementsFile, "--no-warn-script-location", "-q" -NoNewWindow -Wait -PassThru
    if ($pipProc.ExitCode -eq 0) {
        Write-Success "Dependencies installed"
    }
    else {
        Write-Step "5/7" "Some dependencies may have failed (exit code $($pipProc.ExitCode))" "Warning"
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

# Create batch scripts using Set-Content with escaped newlines
$StartBatContent = "@echo off" + "`ncd /d `"$InstallDir`"" + "`npython\python.exe -m src.core.orchestrator --config `"$ConfigDir\config.json`"" + "`npause"
Set-Content -Path "$InstallDir\start.bat" -Value $StartBatContent -Encoding ASCII

$StopBatContent = "@echo off" + "`necho Stopping Benevolent Protocol..." + "`ntaskkill /F /FI `"WINDOWTITLE eq Benevolent*`" 2>nul" + "`necho Protocol stopped." + "`npause"
Set-Content -Path "$InstallDir\stop.bat" -Value $StopBatContent -Encoding ASCII

$StatusBatContent = "@echo off" + "`necho." + "`necho  Benevolent Protocol Status" + "`necho  ==========================" + "`necho." + "`nwmic process where `"CommandLine like '%%orchestrator%%'`" get ProcessId,CommandLine 2>nul | find `"orchestrator`" >nul" + "`nif %ERRORLEVEL%==0 (echo  Status: RUNNING) else (echo  Status: STOPPED)" + "`necho." + "`necho  Install: $InstallDir" + "`necho  Config:  $ConfigDir\config.json" + "`necho  Logs:    $ConfigDir\logs\" + "`necho." + "`npause"
Set-Content -Path "$InstallDir\status.bat" -Value $StatusBatContent -Encoding ASCII

$UninstallBatContent = "@echo off" + "`necho Uninstalling Benevolent Protocol..." + "`nschtasks /delete /tn `"BenevolentProtocol`" /f 2>nul" + "`nnetsh advfirewall firewall delete rule name=`"Benevolent Protocol`" 2>nul" + "`nrmdir /s /q `"$InstallDir`" 2>nul" + "`nrmdir /s /q `"$ConfigDir`" 2>nul" + "`ndel `"%USERPROFILE%\Desktop\Benevolent Protocol.lnk`" 2>nul" + "`necho Uninstall complete." + "`npause"
Set-Content -Path "$InstallDir\uninstall.bat" -Value $UninstallBatContent -Encoding ASCII

Write-Success "Helper scripts created"

# Create scheduled task
$TaskName = "BenevolentProtocol"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$TaskArgs = "-m src.core.orchestrator --config `"$ConfigDir\config.json`""
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $TaskArgs -WorkingDirectory $InstallDir
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
        if ($Response -eq "n" -or $Response -eq "N") {
            $StartNow = $false
        }
        else {
            $StartNow = $true
        }
    }
    
    if ($StartNow) {
        Write-Host ""
        Write-Host "  Starting protocol..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
        Write-Success "Protocol started!"
    }
}

Write-Host ""
Write-Host "  Installation log: $LogFile" -ForegroundColor DarkGray
Write-Host ""

Stop-Transcript | Out-Null

exit 0
