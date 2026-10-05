# Opens a separate Brave/Chrome/Edge profile with remote debugging on port 9333 (Windows).
# Usage: .\tools\browser-separate.ps1 [-Browser brave|chrome|edge]
param([string]$Browser = "brave")
$profileDir = "$env:USERPROFILE\.job-hunt-browser"
$paths = @{
  brave  = @("$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe", "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe")
  chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")
  edge   = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe")
}
$exe = $paths[$Browser] | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $exe) { Write-Host "Could not find $Browser. Install it or pass -Browser chrome/edge."; exit 1 }
Start-Process $exe -ArgumentList "--remote-debugging-port=9333", "--user-data-dir=$profileDir"
Write-Host "Opened $Browser with profile $profileDir on port 9333. Log in to LinkedIn and Google once in that window."
Write-Host 'Then start the bridge in another PowerShell window:  $env:CDP_PORT=9333; node tools\cdpd.mjs'
