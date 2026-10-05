# job-hunt installer for Windows (PowerShell). Run in PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass; iwr https://raw.githubusercontent.com/rayprastya/job-hunt/main/install.ps1 -OutFile install.ps1; .\install.ps1
# It asks where to install, checks Git/Python/Node/browser, creates your private me\ folder, then runs the onboarding interview.

$ErrorActionPreference = "Stop"
function Ask($q, $def) { $a = Read-Host "$q [$def]"; if ([string]::IsNullOrWhiteSpace($a)) { $def } else { $a } }
function Need($cmd, $name, $url) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "MISSING: $name. Install it from $url (or: winget install $name), then re-run this script." -ForegroundColor Yellow
    return $false }
  return $true }

Write-Host "`n1/5  Checking tools" -ForegroundColor Cyan
$okGit = Need "git" "Git.Git" "https://git-scm.com/download/win"
$okPy = Need "python" "Python.Python.3.12" "https://www.python.org/downloads/ (tick 'Add python.exe to PATH')"
$okNode = Need "node" "OpenJS.NodeJS.LTS" "https://nodejs.org (LTS, version 22 or newer)"
if (-not ($okGit -and $okPy -and $okNode)) { exit 1 }
$nodeMajor = [int]((node --version).TrimStart('v').Split('.')[0])
if ($nodeMajor -lt 22) { Write-Host "Node $nodeMajor found; version 22+ is required (winget upgrade OpenJS.NodeJS.LTS)." -ForegroundColor Yellow; exit 1 }

Write-Host "`n2/5  Where should job-hunt live?" -ForegroundColor Cyan
$dest = Ask "Install folder" "$env:USERPROFILE\job-hunt"
if (Test-Path "$dest\.git") { git -C $dest pull --ff-only } else { git clone https://github.com/rayprastya/job-hunt.git $dest }
Set-Location $dest

Write-Host "`n3/5  Your private folder (me\). It is gitignored: nothing in it is ever pushed." -ForegroundColor Cyan
$me = Ask "Private data folder (put it in OneDrive/Google Drive or a private repo to use it on other PCs)" "$dest\me"
New-Item -ItemType Directory -Force -Path "$me\cv" | Out-Null
if ($me -ne "$dest\me") {
  if ((Test-Path "$dest\me") -and -not ((Get-Item "$dest\me").Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    Write-Host "NOTE: $dest\me already exists as a real folder, so I won't link it. Using $dest\me." -ForegroundColor Yellow; $me = "$dest\me"
  } else { cmd /c mklink /J "$dest\me" "$me" | Out-Null } }
if (-not (Test-Path "$me\tracker.csv")) { Copy-Item "templates\tracker.csv" "$me\tracker.csv" }
if (-not (Test-Path "$me\learnings.md")) { Copy-Item "templates\learnings.md" "$me\learnings.md" }
if (-not (Test-Path "$me\.gitignore")) { Copy-Item "templates\me.gitignore" "$me\.gitignore" }
if (-not (Test-Path "$me\preferences.md")) { Copy-Item "templates\preferences.md" "$me\preferences.md" }
if (Test-Path ".git") { Set-Content -Path ".git\hooks\pre-commit" -Value "#!/bin/sh`nexec python tools/guard_commit.py" -NoNewline }

Write-Host "`n4/5  A few questions so the agent can fill applications for you (Enter to skip)" -ForegroundColor Cyan
python tools\onboard.py "$me"

Write-Host "`n5/5  Done. Next steps:" -ForegroundColor Cyan
Write-Host "  1. Put your CV (PDF) in $me\cv\ and set files.cv in me\profile.json"
Write-Host "  2. Create the tracker sheet: docs\SHEETS.md"
Write-Host "  3. Connect your browser: docs\BROWSER.md (Windows section) - e.g. .\tools\browser-separate.ps1"
Write-Host "  4. Check everything: python tools\selftest.py"
Write-Host "  5. Open your AI agent in $dest and say: find me jobs and apply, 5 for now"
