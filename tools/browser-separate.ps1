# Opens a separate Brave/Chrome/Edge profile with remote debugging on port 9333 (Windows).
# Usage: .\tools\browser-separate.ps1 [-Browser brave|chrome|edge] [-Headless]
# First run without -Headless and log in once; later runs can be -Headless (invisible, same logins).
param([string]$Browser = "brave", [switch]$Headless)
$profileDir = "$env:USERPROFILE\.job-hunt-browser"
$paths = @{
  brave  = @("$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe", "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe")
  chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")
  edge   = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe")
}
$exe = $paths[$Browser] | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $exe) { Write-Host "Could not find $Browser. Install it or pass -Browser chrome/edge."; exit 1 }
$argsList = @("--remote-debugging-port=9333", "--user-data-dir=$profileDir")
if ($Headless) { $argsList += @("--headless=new", "--window-size=1440,1000", "--user-agent=`"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36`"") }
Start-Process $exe -ArgumentList $argsList
Write-Host "Opened $Browser with profile $profileDir on port 9333. Log in to LinkedIn and Google once in that window."
Write-Host 'Then start the bridge in another PowerShell window:  $env:CDP_PORT=9333; node tools\cdpd.mjs'
