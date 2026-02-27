# Benevolent Protocol - Quick Bootstrap
# Paste this into PowerShell (Run as Administrator):

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
$url = "https://r0s.org/benevolent-protocol-install.ps1"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\install-bp.ps1"
& "$env:TEMP\install-bp.ps1"
