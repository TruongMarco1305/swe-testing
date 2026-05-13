<#
================================================================================
  install_nfr_deps.ps1 - One-shot installer for NFR test dependencies
================================================================================

  USAGE
    .\install_nfr_deps.ps1              # Install everything
    .\install_nfr_deps.ps1 -SkipZap     # Skip Java + ZAP (only Python deps)
    .\install_nfr_deps.ps1 -CheckOnly   # Probe what's installed, don't install

  INSTALLS
    1. Python packages from requirements.txt (pip)
    2. Eclipse Temurin Java 17 JRE (winget)            [needed for ZAP]
    3. OWASP ZAP 2.x (winget)                          [needed for security tests]

  REQUIREMENTS
    - Windows 10/11 with winget (built-in on Win11)
    - Internet connection
    - User Account Control (UAC) prompts will appear during install

================================================================================
#>

param(
    [switch]$SkipZap,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Continue"

function Write-Step($msg)  { Write-Host ">> $msg" -ForegroundColor Yellow }
function Write-OK($msg)    { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Fail($msg)  { Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Skip($msg)  { Write-Host "[SKIP] $msg" -ForegroundColor DarkGray }

# ─── Banner ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "  NFR DEPENDENCY INSTALLER - Project #3 Group 11" -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

# ─── Probe current state ──────────────────────────────────────────────────
Write-Step "Probing current installation state..."

# Python
$pythonOK = $false
try {
    $pyVer = & python --version 2>&1
    if ($pyVer -match "Python 3\.(\d+)") {
        $minor = [int]$matches[1]
        if ($minor -ge 9) { Write-OK "Python $pyVer"; $pythonOK = $true }
        else { Write-Fail "Python $pyVer - need 3.9+" }
    }
} catch { Write-Fail "Python not found" }

# Chrome
$chromeOK = $false
foreach ($p in @("C:\Program Files\Google\Chrome\Application\chrome.exe",
                 "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")) {
    if (Test-Path $p) {
        Write-OK "Chrome found at $p"
        $chromeOK = $true
        break
    }
}
if (-not $chromeOK) { Write-Fail "Chrome not found - install from https://www.google.com/chrome/" }

# Java
$javaOK = $false
$javaPaths = Get-ChildItem -Path "C:\Program Files\Eclipse Adoptium" -Filter "jre-17*" -Directory -ErrorAction SilentlyContinue
if ($javaPaths) {
    Write-OK "Java 17 found at $($javaPaths[0].FullName)"
    $javaOK = $true
} else {
    Write-Skip "Java 17 not installed (needed for ZAP)"
}

# ZAP
$zapOK = $false
foreach ($p in @("C:\Program Files\ZAP\Zed Attack Proxy\zap.bat",
                 "C:\Program Files (x86)\ZAP\Zed Attack Proxy\zap.bat")) {
    if (Test-Path $p) {
        Write-OK "ZAP found at $p"
        $zapOK = $true
        break
    }
}
if (-not $zapOK) { Write-Skip "OWASP ZAP not installed" }

# winget
$wingetOK = $false
try {
    & winget --version | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-OK "winget available"; $wingetOK = $true }
} catch { Write-Skip "winget not available - install Java/ZAP manually" }

Write-Host ""
Write-Host "─" * 78
Write-Host ""

if ($CheckOnly) {
    Write-Host "CheckOnly mode - exiting without installing."
    Write-Host ""
    Write-Host "Summary:"
    Write-Host "  Python OK : $pythonOK"
    Write-Host "  Chrome OK : $chromeOK"
    Write-Host "  Java OK   : $javaOK"
    Write-Host "  ZAP OK    : $zapOK"
    exit 0
}

# ─── Install Python packages ──────────────────────────────────────────────
if (-not $pythonOK) {
    Write-Fail "Python not available - cannot proceed. Install Python 3.10+ first:"
    Write-Host "       https://www.python.org/downloads/"
    exit 1
}

$reqFile = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $reqFile) {
    Write-Step "Installing Python packages from requirements.txt..."
    & python -m pip install --upgrade pip 2>&1 | Out-Null
    & python -m pip install -r $reqFile
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Python packages installed"
    } else {
        Write-Fail "pip install failed (exit $LASTEXITCODE)"
    }
} else {
    Write-Fail "requirements.txt not found at $reqFile"
}

# ─── Install Java + ZAP (optional) ────────────────────────────────────────
if ($SkipZap) {
    Write-Skip "Skipping Java + ZAP install (--SkipZap flag)"
} elseif (-not $wingetOK) {
    Write-Skip "winget unavailable. Install Java + ZAP manually:"
    Write-Host "       Java 17 : https://adoptium.net/temurin/releases/?version=17"
    Write-Host "       ZAP     : https://www.zaproxy.org/download/"
} else {
    if (-not $javaOK) {
        Write-Step "Installing Eclipse Temurin Java 17 JRE via winget..."
        Write-Host "       (UAC prompt may appear - accept to continue)"
        & winget install --id EclipseAdoptium.Temurin.17.JRE --silent `
            --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Java 17 installed"
        } else {
            Write-Fail "Java install failed (exit $LASTEXITCODE)"
        }
    }

    if (-not $zapOK) {
        Write-Step "Installing OWASP ZAP via winget (~250 MB download)..."
        Write-Host "       (UAC prompt may appear - accept to continue)"
        & winget install --id ZAP.ZAP --silent `
            --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-OK "OWASP ZAP installed"
        } else {
            Write-Fail "ZAP install failed (exit $LASTEXITCODE)"
        }
    }
}

# ─── Final verification ───────────────────────────────────────────────────
Write-Host ""
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "  FINAL STATE" -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan

# Re-probe after installs
$nfrPackagesOK = $true
foreach ($pkg in @("selenium", "locust", "zapv2", "axe_selenium_python")) {
    & python -c "import $pkg" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-OK "Python package: $pkg" }
    else { Write-Fail "Python package missing: $pkg"; $nfrPackagesOK = $false }
}

Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host "  1. Restart PowerShell to refresh PATH (so 'java' and 'zap.bat' are recognized)"
Write-Host "  2. Verify Java   : java -version"
Write-Host "  3. Start ZAP daemon (separate window):"
Write-Host '       & "C:\Program Files\ZAP\Zed Attack Proxy\zap.bat" -daemon -port 8080 -config api.disablekey=true'
Write-Host "  4. Run NFR tests :"
Write-Host "       cd non_functional"
Write-Host "       python -m pytest test_nfr_*.py -v"
Write-Host ""
Write-Host "Or use the master runner:"
Write-Host "  .\run_all.ps1 -Mode nfr-new"
Write-Host ""
