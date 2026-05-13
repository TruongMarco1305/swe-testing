<#
================================================================================
  Project #3 - Group 11 - Software Testing 2025S2
  Master test-runner script for Windows PowerShell
================================================================================

  USAGE
    .\run_all.ps1                 # Interactive menu (recommended)
    .\run_all.ps1 -Mode setup     # Only install dependencies
    .\run_all.ps1 -Mode smoke     # 1-test smoke check (~30s)
    .\run_all.ps1 -Mode level1    # Run all Level 1 tests
    .\run_all.ps1 -Mode level2    # Run all Level 2 tests
    .\run_all.ps1 -Mode nfr-old   # Run original test_non_functional.py
    .\run_all.ps1 -Mode nfr-new   # Run 6 new NFR files (pytest portion)
    .\run_all.ps1 -Mode nfr-skip-zap   # 6 NFR files, skip ZAP tests
    .\run_all.ps1 -Mode locust    # Launch one of 4 Locust files
    .\run_all.ps1 -Mode cleanup       # Delete test data from Moodle
    .\run_all.ps1 -Mode cleanup-dry   # Preview cleanup without deleting
    .\run_all.ps1 -Mode all       # Everything (~1h40m)
    .\run_all.ps1 -Mode all-no-zap   # Everything except ZAP tests

  REQUIREMENTS
    - Python 3.9+    - Google Chrome    - Java 17+ (only for ZAP)
    - OWASP ZAP installed at C:\Program Files\ZAP\Zed Attack Proxy\zap.bat
      (override with -ZapPath "<path>")

================================================================================
#>

param(
    [ValidateSet("menu","setup","smoke","level1","level2","nfr-old","nfr-new",
                 "nfr-skip-zap","locust","cleanup","cleanup-dry","all","all-no-zap")]
    [string]$Mode = "menu",
    [string]$ZapPath = "C:\Program Files\ZAP\Zed Attack Proxy\zap.bat",
    [int]$ZapPort = 8080
)

$ErrorActionPreference = "Continue"
$RepoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Level1Dir  = Join-Path $RepoRoot "level1"
$Level2Dir  = Join-Path $RepoRoot "level2"
$NfrDir     = Join-Path $RepoRoot "non_functional"

# --- Pretty printers (ASCII only to avoid encoding issues) ---------------
function Write-Section($title) {
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
}
function Write-Step($msg)  { Write-Host ">> $msg" -ForegroundColor Yellow }
function Write-OK($msg)    { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Fail($msg)  { Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Skip($msg)  { Write-Host "[SKIP] $msg" -ForegroundColor DarkGray }

# --- Prerequisite checks -------------------------------------------------
function Test-Python {
    try {
        $v = & python --version 2>&1
        if ($v -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]; $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                Write-OK "Python $v"
                return $true
            }
            Write-Fail "Python $v - need 3.9+"
            return $false
        }
    } catch {}
    Write-Fail "Python not found. Install from https://www.python.org/downloads/"
    return $false
}

function Test-Chrome {
    $paths = @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            $ver = (Get-Item $p).VersionInfo.FileVersion
            Write-OK "Chrome $ver  ($p)"
            return $true
        }
    }
    Write-Fail "Chrome not found. Install from https://www.google.com/chrome/"
    return $false
}

function Test-Zap {
    if (Test-Path $ZapPath) {
        Write-OK "ZAP found at $ZapPath"
        return $true
    }
    Write-Skip "ZAP not found at $ZapPath (security tests will fail/skip)"
    return $false
}

function Test-PythonPackages {
    $pkgs = @("selenium","webdriver_manager","pandas","openpyxl","pytest",
              "locust","zapv2","axe_selenium_python")
    $missing = @()
    foreach ($pkg in $pkgs) {
        & python -c "import $pkg" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { $missing += $pkg }
    }
    if ($missing.Count -eq 0) {
        Write-OK "All Python packages installed"
        return $true
    }
    Write-Fail "Missing packages: $($missing -join ', ')"
    return $false
}

# --- Setup phase ---------------------------------------------------------
function Invoke-Setup {
    Write-Section "SETUP - installing dependencies"

    if (-not (Test-Python))  { return $false }
    if (-not (Test-Chrome))  { Write-Skip "Continuing without Chrome check" }

    Write-Step "Installing Python packages from requirements.txt"
    $req = Join-Path $RepoRoot "requirements.txt"
    if (-not (Test-Path $req)) {
        Write-Fail "requirements.txt not found at $req"
        return $false
    }
    & python -m pip install --upgrade pip
    & python -m pip install -r $req
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "pip install failed"
        return $false
    }
    if (-not (Test-PythonPackages)) { return $false }
    Test-Zap | Out-Null
    Write-OK "Setup complete"
    return $true
}

# --- ZAP daemon lifecycle ------------------------------------------------
$Global:ZapProcess = $null

function Start-ZapDaemon {
    if (-not (Test-Path $ZapPath)) {
        Write-Skip "Skipping ZAP - not installed"
        return $false
    }
    Write-Step "Starting ZAP daemon on port $ZapPort"
    $Global:ZapProcess = Start-Process -FilePath $ZapPath `
        -ArgumentList "-daemon","-port",$ZapPort,"-config","api.disablekey=true" `
        -PassThru -WindowStyle Hidden

    Write-Step "Waiting for ZAP to listen on http://127.0.0.1:$ZapPort ..."
    $maxWait = 60
    for ($i = 0; $i -lt $maxWait; $i++) {
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:$ZapPort" `
                 -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                Write-OK "ZAP is up (PID $($Global:ZapProcess.Id))"
                return $true
            }
        } catch { Start-Sleep -Seconds 1 }
    }
    Write-Fail "ZAP did not respond within ${maxWait}s"
    return $false
}

function Stop-ZapDaemon {
    if ($Global:ZapProcess -and -not $Global:ZapProcess.HasExited) {
        Write-Step "Stopping ZAP daemon (PID $($Global:ZapProcess.Id))"
        Stop-Process -Id $Global:ZapProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

# --- Test runners --------------------------------------------------------
function Invoke-Smoke {
    Write-Section "SMOKE TEST - TC_006_001 only (~30s)"
    Push-Location $Level1Dir
    & python -m pytest test_quiz_level1.py -v -k "TC_006_001"
    Pop-Location
}

function Invoke-Level1 {
    Write-Section "LEVEL 1 - 169 test cases across 6 TCs (~30 min)"
    Push-Location $Level1Dir
    & python -m pytest . -v
    Pop-Location
}

function Invoke-Level2 {
    Write-Section "LEVEL 2 - 169 test cases (~30 min)"
    Push-Location $Level2Dir
    & python -m pytest test_level2.py -v
    Pop-Location
}

function Invoke-NfrOld {
    Write-Section "NON-FUNCTIONAL (original) - Performance + Security"
    Push-Location $NfrDir
    & python -m pytest test_non_functional.py -v
    Pop-Location
}

function Invoke-NfrNew {
    param([switch]$SkipZap)
    Write-Section "6 NFR FILES - Locust + ZAP + axe"
    Push-Location $NfrDir
    if ($SkipZap) {
        Write-Step "ZAP tests will be filtered out via -k"
        & python -m pytest . -v -k "not Zap and not SecurityHeaders and not ZapScan and not ZapInputFuzz"
    } else {
        & python -m pytest test_nfr_01_login_perf_sec.py `
                           test_nfr_02_login_perf_a11y.py `
                           test_nfr_03_login_sec_a11y.py `
                           test_nfr_04_quiz_perf_sec.py `
                           test_nfr_05_quiz_perf_a11y.py `
                           test_nfr_06_quiz_sec_a11y.py -v
    }
    Pop-Location
}

function Invoke-Cleanup {
    param([switch]$DryRun)
    if ($DryRun) {
        Write-Section "CLEANUP (dry-run) - list test data, do NOT delete"
        & python (Join-Path $RepoRoot "cleanup_moodle.py") --all --dry-run
    } else {
        Write-Section "CLEANUP - delete all test data on Moodle"
        Write-Host "This will DELETE users, courses, quizzes, assignments, and calendar events" -ForegroundColor Yellow
        Write-Host "that match the TC-001..TC-006 + NFR test patterns." -ForegroundColor Yellow
        $confirm = Read-Host "Type 'DELETE' to confirm (anything else cancels)"
        if ($confirm -ne "DELETE") {
            Write-Skip "Cleanup cancelled by user"
            return
        }
        & python (Join-Path $RepoRoot "cleanup_moodle.py") --all
    }
}

function Invoke-LocustMenu {
    Write-Section "LOCUST - Performance load testing"
    $files = @(
        "test_nfr_01_login_perf_sec.py",
        "test_nfr_02_login_perf_a11y.py",
        "test_nfr_04_quiz_perf_sec.py",
        "test_nfr_05_quiz_perf_a11y.py"
    )
    $labels = @(
        "Login - anonymous load",
        "Login - anonymous load, a11y companion",
        "Quiz form - authenticated load",
        "Quiz form - authenticated load, a11y companion"
    )
    for ($i = 0; $i -lt $files.Count; $i++) {
        $n = $i + 1
        Write-Host ("  [{0}] {1,-35} ({2})" -f $n, $files[$i], $labels[$i])
    }
    $choice = Read-Host "Pick a file (1-4)"
    $idx = 0
    if (-not [int]::TryParse($choice, [ref]$idx) -or $idx -lt 1 -or $idx -gt $files.Count) {
        Write-Fail "Invalid choice: $choice"
        return
    }
    $file = $files[$idx - 1]

    Write-Step "Starting Locust with $file"
    Write-Host "-> Open http://localhost:8089 in your browser" -ForegroundColor Cyan
    Write-Host "-> Number of users: 50,  Spawn rate: 5"        -ForegroundColor Cyan
    Write-Host "-> Host: https://ihatetesting.moodlecloud.com" -ForegroundColor Cyan
    Write-Host "-> Press Ctrl+C in this window when done"      -ForegroundColor Cyan

    Push-Location $NfrDir
    & locust -f $file
    Pop-Location
}

# --- Orchestrators -------------------------------------------------------
function Invoke-All {
    param([switch]$NoZap)

    if (-not (Invoke-Setup)) { return }

    if (-not $NoZap) {
        if (-not (Start-ZapDaemon)) {
            Write-Skip "Falling back to no-ZAP mode"
            $NoZap = $true
        }
    }

    try {
        Invoke-Smoke
        Invoke-Level1
        Invoke-Level2
        Invoke-NfrOld
        if ($NoZap) { Invoke-NfrNew -SkipZap } else { Invoke-NfrNew }

        Write-Section "ALL TESTS DONE"
        Write-OK "Suite complete. Locust load-tests are interactive - run them with:"
        Write-Host "    .\run_all.ps1 -Mode locust" -ForegroundColor Cyan
    } finally {
        Stop-ZapDaemon
    }
}

# --- Interactive menu ----------------------------------------------------
function Show-Menu {
    Write-Section "PROJECT #3 - Group 11 - Master Test Runner"
    Write-Host "  [1] Setup        - install Python packages          (~3 min)"
    Write-Host "  [2] Smoke test   - 1 test case sanity check         (~30s)"
    Write-Host "  [3] Level 1      - all 169 TC-001..006 cases        (~30 min)"
    Write-Host "  [4] Level 2      - all 169 cases in test_level2.py  (~30 min)"
    Write-Host "  [5] NFR (old)    - test_non_functional.py           (~3 min)"
    Write-Host "  [6] NFR (new 6)  - 6 new files, needs ZAP           (~10 min)"
    Write-Host "  [7] NFR (no ZAP) - 6 new files, accessibility only  (~5 min)"
    Write-Host "  [8] Locust       - pick a load-test file (interactive)"
    Write-Host "  [9] ALL          - everything with ZAP              (~1h40m)"
    Write-Host "  [0] ALL (no ZAP) - everything except ZAP tests      (~1h30m)"
    Write-Host "  [c] Cleanup      - delete test data from Moodle"
    Write-Host "  [d] Cleanup DRY  - preview what cleanup would delete"
    Write-Host "  [q] Quit"
    $choice = Read-Host "`nPick"
    switch ($choice) {
        "1" { Invoke-Setup }
        "2" { Invoke-Smoke }
        "3" { Invoke-Level1 }
        "4" { Invoke-Level2 }
        "5" { Invoke-NfrOld }
        "6" {
            if (Start-ZapDaemon) {
                try { Invoke-NfrNew } finally { Stop-ZapDaemon }
            } else { Write-Fail "ZAP could not be started" }
        }
        "7" { Invoke-NfrNew -SkipZap }
        "8" { Invoke-LocustMenu }
        "9" { Invoke-All }
        "0" { Invoke-All -NoZap }
        "c" { Invoke-Cleanup }
        "d" { Invoke-Cleanup -DryRun }
        "q" { return }
        default { Write-Fail "Unknown option: $choice"; Show-Menu }
    }
}

# --- Entry point ---------------------------------------------------------
try {
    switch ($Mode) {
        "menu"          { Show-Menu }
        "setup"         { Invoke-Setup }
        "smoke"         { Invoke-Smoke }
        "level1"        { Invoke-Level1 }
        "level2"        { Invoke-Level2 }
        "nfr-old"       { Invoke-NfrOld }
        "nfr-new"       {
            if (Start-ZapDaemon) {
                try { Invoke-NfrNew } finally { Stop-ZapDaemon }
            }
        }
        "nfr-skip-zap"  { Invoke-NfrNew -SkipZap }
        "locust"        { Invoke-LocustMenu }
        "cleanup"       { Invoke-Cleanup }
        "cleanup-dry"   { Invoke-Cleanup -DryRun }
        "all"           { Invoke-All }
        "all-no-zap"    { Invoke-All -NoZap }
    }
} finally {
    Stop-ZapDaemon
}
