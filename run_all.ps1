<#
================================================================================
  Project #3 - Group 11 - Software Testing 2025S2
  Master test-runner script for Windows PowerShell
================================================================================

  USAGE
    .\run_all.ps1                    # Interactive menu (recommended)
    .\run_all.ps1 -Mode setup        # Only install dependencies
    .\run_all.ps1 -Mode smoke        # 1-test smoke check (~30s)
    .\run_all.ps1 -Mode level1       # Run all Level 1 tests (6 TC files)
    .\run_all.ps1 -Mode level2       # Run all Level 2 tests (TC-ALL.py)
    .\run_all.ps1 -Mode nfr          # Run 6 NFR files (pytest portion)
    .\run_all.ps1 -Mode locust       # Launch one of 4 Locust files
    .\run_all.ps1 -Mode cleanup      # Delete test data from Moodle
    .\run_all.ps1 -Mode cleanup-dry  # Preview cleanup without deleting
    .\run_all.ps1 -Mode all          # Everything (~1h30m)

    .\run_all.ps1 -Mode tc -Tc 003   # Run TC-003 across level1 + level2 + NFR

  REQUIREMENTS
    - Python 3.9+    - Google Chrome
    (ZAP is no longer required; security tests use requests-based probes)

  FILE LAYOUT (after rename)
    level1/         TC-001_code.py + TC-001_data.csv .. TC-006_*
    level2/         TC-ALL.py + TC-001_data.csv .. TC-006_data.csv
    non_functional/ TC-001.py .. TC-006.py

================================================================================
#>

param(
    [ValidateSet("menu","setup","smoke","level1","level2","nfr",
                 "locust","cleanup","cleanup-dry","all","tc")]
    [string]$Mode = "menu",
    [string]$Tc = ""   # used with -Mode tc, e.g. "-Mode tc -Tc 003"
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

function Test-PythonPackages {
    $pkgs = @("selenium","webdriver_manager","pandas","openpyxl","pytest",
              "locust","requests","axe_selenium_python")
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
    Write-OK "Setup complete"
    return $true
}

# --- Test runners --------------------------------------------------------
function Invoke-Smoke {
    Write-Section "SMOKE TEST - TC_006_001 only (~30s)"
    Push-Location $Level1Dir
    & python -m pytest TC-006_code.py -v -k "TC_006_001"
    Pop-Location
}

function Invoke-Level1 {
    Write-Section "LEVEL 1 - all 6 TC files (TC-001_code.py .. TC-006_code.py)"
    Push-Location $Level1Dir
    & python -m pytest . -v
    Pop-Location
}

function Invoke-Level2 {
    Write-Section "LEVEL 2 - all 169 cases in TC-ALL.py (~30 min)"
    Push-Location $Level2Dir
    & python -m pytest TC-ALL.py -v
    Pop-Location
}

function Invoke-Nfr {
    Write-Section "NFR - 6 files (Locust + requests-based security + axe)"
    Push-Location $NfrDir
    & python -m pytest TC-001.py `
                       TC-002.py `
                       TC-003.py `
                       TC-004.py `
                       TC-005.py `
                       TC-006.py -v
    Pop-Location
}

function Invoke-Tc {
    param([string]$Num)
    if ($Num -notmatch "^\d{3}$") {
        Write-Fail "Bad -Tc value '$Num' (expected 3 digits, e.g. '003')"
        return
    }
    Write-Section "TC-$Num - level1 + level2 + NFR"

    Push-Location $Level1Dir
    Write-Step "Level 1: TC-${Num}_code.py"
    & python -m pytest "TC-${Num}_code.py" -v
    Pop-Location

    Push-Location $Level2Dir
    Write-Step "Level 2: TC-ALL.py -k TC_${Num}"
    & python -m pytest TC-ALL.py -v -k "TC_${Num}"
    Pop-Location

    Push-Location $NfrDir
    Write-Step "NFR: TC-${Num}.py"
    & python -m pytest "TC-${Num}.py" -v
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
        "TC-001.py",
        "TC-002.py",
        "TC-004.py",
        "TC-005.py"
    )
    $labels = @(
        "TC-001 Add-User form - authed load",
        "TC-002 New-Course form - authed load",
        "TC-004 Grader page - authed load",
        "TC-005 Calendar month view - authed load"
    )
    for ($i = 0; $i -lt $files.Count; $i++) {
        $n = $i + 1
        Write-Host ("  [{0}] {1,-15} {2}" -f $n, $files[$i], $labels[$i])
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
    Write-Host "-> Host: https://xuansang1234.moodlecloud.com" -ForegroundColor Cyan
    Write-Host "-> Press Ctrl+C in this window when done"      -ForegroundColor Cyan

    Push-Location $NfrDir
    & locust -f $file
    Pop-Location
}

# --- Orchestrators -------------------------------------------------------
function Invoke-All {
    if (-not (Invoke-Setup)) { return }
    Invoke-Smoke
    Invoke-Level1
    Invoke-Level2
    Invoke-Nfr

    Write-Section "ALL TESTS DONE"
    Write-OK "Suite complete. Locust load-tests are interactive - run them with:"
    Write-Host "    .\run_all.ps1 -Mode locust" -ForegroundColor Cyan
}

# --- Interactive menu ----------------------------------------------------
function Show-Menu {
    Write-Section "PROJECT #3 - Group 11 - Master Test Runner"
    Write-Host "  [1] Setup        - install Python packages          (~3 min)"
    Write-Host "  [2] Smoke test   - 1 test case sanity check         (~30s)"
    Write-Host "  [3] Level 1      - all TC-XXX_code.py files         (~30 min)"
    Write-Host "  [4] Level 2      - all 169 cases in TC-ALL.py       (~30 min)"
    Write-Host "  [5] NFR          - 6 files (perf + sec + a11y)      (~10 min)"
    Write-Host "  [6] Locust       - pick a load-test file (interactive)"
    Write-Host "  [7] Single TC    - run one TC-XXX across all 3 dirs"
    Write-Host "  [8] ALL          - everything                       (~1h30m)"
    Write-Host "  [c] Cleanup      - delete test data from Moodle"
    Write-Host "  [d] Cleanup DRY  - preview what cleanup would delete"
    Write-Host "  [q] Quit"
    $choice = Read-Host "`nPick"
    switch ($choice) {
        "1" { Invoke-Setup }
        "2" { Invoke-Smoke }
        "3" { Invoke-Level1 }
        "4" { Invoke-Level2 }
        "5" { Invoke-Nfr }
        "6" { Invoke-LocustMenu }
        "7" {
            $tcNum = Read-Host "Which TC? (001 / 002 / 003 / 004 / 005 / 006)"
            Invoke-Tc -Num $tcNum
        }
        "8" { Invoke-All }
        "c" { Invoke-Cleanup }
        "d" { Invoke-Cleanup -DryRun }
        "q" { return }
        default { Write-Fail "Unknown option: $choice"; Show-Menu }
    }
}

# --- Entry point ---------------------------------------------------------
switch ($Mode) {
    "menu"          { Show-Menu }
    "setup"         { Invoke-Setup }
    "smoke"         { Invoke-Smoke }
    "level1"        { Invoke-Level1 }
    "level2"        { Invoke-Level2 }
    "nfr"           { Invoke-Nfr }
    "locust"        { Invoke-LocustMenu }
    "cleanup"       { Invoke-Cleanup }
    "cleanup-dry"   { Invoke-Cleanup -DryRun }
    "all"           { Invoke-All }
    "tc"            { Invoke-Tc -Num $Tc }
}
