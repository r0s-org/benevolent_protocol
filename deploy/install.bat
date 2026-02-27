@echo off
:: Benevolent Protocol - Windows Bootstrap Installer
:: No prerequisites required - bundles Python automatically
:: Run as Administrator

title Benevolent Protocol Installer

:: Check admin
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo This installer requires Administrator privileges.
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Version info
set VERSION=0.3.0-alpha
set PYTHON_VERSION=3.12.4
set PYTHON_EMBED_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set PYTHON_EMBED_URL_ARM=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-arm64.zip
set PROTOCOL_URL=https://github.com/r0s-org/benevolent_protocol/archive/refs/heads/main.zip
set PIP_URL=https://bootstrap.pypa.io/get-pip.py

:: Directories
set INSTALL_DIR=%ProgramFiles%\BenevolentProtocol
set CONFIG_DIR=%ProgramData%\BenevolentProtocol
set TEMP_DIR=%TEMP%\BP_Install

echo.
echo  ================================================================
echo       Benevolent Protocol v%VERSION% - Windows Installer
echo  ================================================================
echo.
echo  This installer includes everything needed - no prerequisites!
echo.

:: Detect architecture
if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set PYTHON_URL=%PYTHON_EMBED_URL_ARM%
    echo  Detected: ARM64 Windows
) else (
    set PYTHON_URL=%PYTHON_EMBED_URL%
    echo  Detected: x64 Windows
)

:: Create temp directory
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

:: Create install directories
echo.
echo  [1/7] Creating directories...
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%CONFIG_DIR%" 2>nul
mkdir "%CONFIG_DIR%\logs" 2>nul
mkdir "%CONFIG_DIR%\data" 2>nul
echo       Done.

:: Download embedded Python
echo.
echo  [2/7] Downloading Python %PYTHON_VERSION% (embedded)...
echo       This may take a moment...

certutil -urlcache -split -f "%PYTHON_URL%" "%TEMP_DIR%\python_embed.zip" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       ERROR: Failed to download Python.
    echo       Please check your internet connection.
    pause
    exit /b 1
)
echo       Done.

:: Extract Python
echo.
echo  [3/7] Extracting Python...
powershell -Command "Expand-Archive -Path '%TEMP_DIR%\python_embed.zip' -DestinationPath '%INSTALL_DIR%\python' -Force"
if %ERRORLEVEL% neq 0 (
    echo       ERROR: Failed to extract Python.
    pause
    exit /b 1
)
echo       Done.

:: Configure embedded Python to use site-packages
echo.
echo  [4/7] Configuring Python environment...
echo       Setting up pip...

:: Create python312._pth to enable site-packages
echo python312.zip> "%INSTALL_DIR%\python\python312._pth"
echo .>> "%INSTALL_DIR%\python\python312._pth"
echo Lib>> "%INSTALL_DIR%\python\python312._pth"
echo Lib\site-packages>> "%INSTALL_DIR%\python\python312._pth"
echo.>> "%INSTALL_DIR%\python\python312._pth"
echo import site>> "%INSTALL_DIR%\python\python312._pth"

:: Create directories for packages
mkdir "%INSTALL_DIR%\python\Lib" 2>nul
mkdir "%INSTALL_DIR%\python\Lib\site-packages" 2>nul

:: Download get-pip.py
certutil -urlcache -split -f "%PIP_URL%" "%TEMP_DIR%\get-pip.py" >nul 2>&1

:: Install pip
"%INSTALL_DIR%\python\python.exe" "%TEMP_DIR%\get-pip.py" --no-warn-script-location >nul 2>&1
echo       Done.

:: Download protocol
echo.
echo  [5/7] Downloading Benevolent Protocol...
certutil -urlcache -split -f "%PROTOCOL_URL%" "%TEMP_DIR%\protocol.zip" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       ERROR: Failed to download protocol.
    pause
    exit /b 1
)

:: Extract protocol
powershell -Command "Expand-Archive -Path '%TEMP_DIR%\protocol.zip' -DestinationPath '%TEMP_DIR%\protocol' -Force"

:: Find extracted folder and copy files
for /d %%i in ("%TEMP_DIR%\protocol\benevolent_protocol*") do set PROTOCOL_SRC=%%i

:: Copy protocol files
xcopy "%PROTOCOL_SRC%\src" "%INSTALL_DIR%\src" /E /I /Q >nul
xcopy "%PROTOCOL_SRC%\config" "%INSTALL_DIR%\config" /E /I /Q >nul
copy "%PROTOCOL_SRC%\requirements.txt" "%INSTALL_DIR%\" >nul
copy "%PROTOCOL_SRC%\LICENSE" "%INSTALL_DIR%\" >nul 2>&1
copy "%PROTOCOL_SRC%\README.md" "%INSTALL_DIR%\" >nul 2>&1
echo       Done.

:: Install dependencies
echo.
echo  [6/7] Installing dependencies...
"%INSTALL_DIR%\python\python.exe" -m pip install -r "%INSTALL_DIR%\requirements.txt" --no-warn-script-location -q 2>nul
if %ERRORLEVEL% neq 0 (
    echo       WARNING: Some dependencies may have failed.
)
echo       Done.

:: Generate configuration
echo.
echo  [7/7] Creating configuration...

:: Generate random secret
set SECRET=
for /L %%i in (1,1,64) do (
    set /a HEX=!RANDOM! %% 16
    if !HEX! equ 10 set HEX=A
    if !HEX! equ 11 set HEX=B
    if !HEX! equ 12 set HEX=C
    if !HEX! equ 13 set HEX=D
    if !HEX! equ 14 set HEX=E
    if !HEX! equ 15 set HEX=F
    set SECRET=!SECRET!!HEX!
)

:: Create config.json using PowerShell for proper JSON
powershell -Command ^
"$config = @{telemetry_enabled=$true; telemetry_level='standard'; telemetry_endpoint=$null; heartbeat_interval=60; command_port=9527; optimization_interval=3600; propagation_enabled=$false; gaming_mode_auto_detect=$true; max_cpu_percent=30; max_memory_mb=500; control_secret='%SECRET%'; update_endpoint=$null; log_level='INFO'; log_file='%CONFIG_DIR%\logs\protocol.log'; platform_mode='active'; linux_carrier_mode=$true; windows_active_mode=$true; android_active_mode=$true; allowed_networks=@('192.168.0.0/16','10.0.0.0/8'); excluded_hosts=@()}; $config | ConvertTo-Json -Depth 10 | Out-File '%CONFIG_DIR%\config.json' -Encoding UTF8"

:: Create batch scripts
echo @echo off> "%INSTALL_DIR%\start.bat"
echo cd /d "%INSTALL_DIR%">> "%INSTALL_DIR%\start.bat"
echo python\python.exe -m src.core.orchestrator --config "%CONFIG_DIR%\config.json">> "%INSTALL_DIR%\start.bat"
echo pause>> "%INSTALL_DIR%\start.bat"

echo @echo off> "%INSTALL_DIR%\stop.bat"
echo taskkill /F /IM python.exe /FI "WINDOWTITLE eq Benevolent*" 2^>nul>> "%INSTALL_DIR%\stop.bat"
echo echo Protocol stopped.>> "%INSTALL_DIR%\stop.bat"
echo pause>> "%INSTALL_DIR%\stop.bat"

echo @echo off> "%INSTALL_DIR%\status.bat"
echo echo Benevolent Protocol Status>> "%INSTALL_DIR%\status.bat"
echo echo ==========================>> "%INSTALL_DIR%\status.bat"
echo tasklist /FI "IMAGENAME eq python.exe" 2^>nul ^| find "python.exe" ^>nul>> "%INSTALL_DIR%\status.bat"
echo if %%ERRORLEVEL%%==0 (echo Status: Running) else (echo Status: Stopped)>> "%INSTALL_DIR%\status.bat"
echo echo.>> "%INSTALL_DIR%\status.bat"
echo echo Config: %CONFIG_DIR%\config.json>> "%INSTALL_DIR%\status.bat"
echo pause>> "%INSTALL_DIR%\status.bat"

echo       Done.

:: Create scheduled task
echo.
echo  Setting up scheduled task...
schtasks /create /tn "BenevolentProtocol" /tr "\"%INSTALL_DIR%\python\pythonw.exe\" -m src.core.orchestrator --config \"%CONFIG_DIR%\config.json\"" /sc onlogon /rl highest /f >nul 2>&1
echo       Done.

:: Configure firewall
echo  Configuring firewall...
netsh advfirewall firewall add rule name="Benevolent Protocol" dir=in action=allow protocol=tcp localport=9527 >nul 2>&1
echo       Done.

:: Create desktop shortcut
echo  Creating shortcuts...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Benevolent Protocol.lnk'); $s.TargetPath = '%INSTALL_DIR%\start.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()" 2>nul
echo       Done.

:: Cleanup
echo.
echo  Cleaning up...
rmdir /s /q "%TEMP_DIR%" 2>nul
echo       Done.

:: Summary
echo.
echo  ================================================================
echo                    Installation Complete!
echo  ================================================================
echo.
echo  Installation Directory: %INSTALL_DIR%
echo  Configuration: %CONFIG_DIR%\config.json
echo  Logs: %CONFIG_DIR%\logs\
echo.
echo  Your Secret Key: %SECRET%
echo  (Save this for remote commands!)
echo.
echo  Commands:
echo    Start:   %INSTALL_DIR%\start.bat
echo    Stop:    %INSTALL_DIR%\stop.bat
echo    Status:  %INSTALL_DIR%\status.bat
echo.
echo  The protocol will start automatically when you log in.
echo.

set /p START_NOW="Start Benevolent Protocol now? (Y/n): "
if /i "%START_NOW%" neq "n" (
    echo.
    echo  Starting protocol...
    schtasks /run /tn "BenevolentProtocol" >nul 2>&1
    timeout /t 2 >nul
    echo  Protocol started!
)

echo.
echo  Installation complete!
echo.
pause
