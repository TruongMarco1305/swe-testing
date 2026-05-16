#!/usr/bin/env bash
# ==============================================================================
#   Project #3 - Group 11 - Software Testing 2025S2
#   Master test-runner script for macOS / Linux (bash)
# ==============================================================================
#
#   USAGE
#     chmod +x run_all.sh        # first time only
#     ./run_all.sh               # interactive menu (recommended)
#     ./run_all.sh setup         # install dependencies only
#     ./run_all.sh smoke         # 1-test smoke check (~30s)
#     ./run_all.sh level1        # all Level 1 tests (6 TC files)
#     ./run_all.sh level2        # all Level 2 tests (TC-ALL.py)
#     ./run_all.sh nfr           # NFR files (perf/sec/a11y/rel/compat/usab)
#     ./run_all.sh locust        # launch Locust performance test (TC-001)
#     ./run_all.sh cleanup       # delete test data from Moodle
#     ./run_all.sh cleanup-dry   # preview cleanup without deleting
#     ./run_all.sh all           # everything (~1h 30m)
#     ./run_all.sh tc 003        # run TC-003 across level1 + level2 + NFR
#
#   REQUIREMENTS
#     - Python 3.9+
#     - Google Chrome (https://www.google.com/chrome/)
#     - Internet connection (first run downloads ChromeDriver automatically)
#
#   FILE LAYOUT
#     level1/         TC-001_code.py + TC-001_data.csv .. TC-006_*
#     level2/         TC-ALL.py + TC-001_data.csv .. TC-006_data.csv
#     non_functional/ TC-001.py .. TC-006.py
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEVEL1_DIR="$REPO_ROOT/level1"
LEVEL2_DIR="$REPO_ROOT/level2"
NFR_DIR="$REPO_ROOT/non_functional"

# ── Colours ───────────────────────────────────────────────────────────────────
CYAN="\033[1;36m"; YELLOW="\033[1;33m"; GREEN="\033[1;32m"
RED="\033[1;31m";  GRAY="\033[0;90m";   RESET="\033[0m"

write_section() {
    echo -e "\n${CYAN}$(printf '=%.0s' {1..78})\n  $1\n$(printf '=%.0s' {1..78})${RESET}"
}
write_step()  { echo -e "${YELLOW}>> $1${RESET}"; }
write_ok()    { echo -e "${GREEN}[OK]   $1${RESET}"; }
write_fail()  { echo -e "${RED}[FAIL] $1${RESET}"; }
write_skip()  { echo -e "${GRAY}[SKIP] $1${RESET}"; }

# ── Prerequisite checks ───────────────────────────────────────────────────────
test_python() {
    if command -v python3 &>/dev/null; then
        local ver; ver=$(python3 --version 2>&1)
        local minor; minor=$(python3 -c "import sys; print(sys.version_info.minor)")
        if [[ $minor -ge 9 ]]; then
            write_ok "$ver"
            return 0
        fi
        write_fail "$ver — need 3.9+"
    else
        write_fail "python3 not found. Install from https://www.python.org/downloads/"
    fi
    return 1
}

test_chrome() {
    local mac_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    local linux_paths=("/usr/bin/google-chrome" "/usr/bin/chromium-browser" "/usr/bin/chromium")
    if [[ -f "$mac_path" ]]; then
        write_ok "Chrome found (macOS)"
        return 0
    fi
    for p in "${linux_paths[@]}"; do
        if [[ -f "$p" ]]; then
            write_ok "Chrome/Chromium found at: $p"
            return 0
        fi
    done
    write_fail "Chrome not found. Install from https://www.google.com/chrome/"
    return 1
}

test_packages() {
    local pkgs=("selenium" "webdriver_manager" "pandas" "openpyxl" "pytest"
                "locust" "requests" "axe_selenium_python")
    local missing=()
    for pkg in "${pkgs[@]}"; do
        python3 -c "import $pkg" &>/dev/null || missing+=("$pkg")
    done
    if [[ ${#missing[@]} -eq 0 ]]; then
        write_ok "All Python packages installed"
        return 0
    fi
    write_fail "Missing packages: ${missing[*]}"
    return 1
}

# ── Setup phase ───────────────────────────────────────────────────────────────
invoke_setup() {
    write_section "SETUP — installing dependencies"
    test_python || return 1
    test_chrome || write_skip "Continuing without Chrome check"
    write_step "Installing Python packages from requirements.txt"
    local req="$REPO_ROOT/requirements.txt"
    if [[ ! -f "$req" ]]; then
        write_fail "requirements.txt not found at $req"
        return 1
    fi
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "$req"
    test_packages || return 1
    write_ok "Setup complete"
}

# ── Cleanup helpers ───────────────────────────────────────────────────────────
invoke_cleanup_auto() {
    write_section "AUTO CLEANUP — removing test data from Moodle"
    write_step "Running cleanup (all categories)..."
    python3 "$REPO_ROOT/cleanup_moodle.py" --all \
        && write_ok "Cleanup complete" \
        || write_fail "Cleanup reported errors — continuing anyway"
}

invoke_cleanup() {
    local dry="${1:-}"
    if [[ "$dry" == "dry" ]]; then
        write_section "CLEANUP (dry-run) — list test data, do NOT delete"
        python3 "$REPO_ROOT/cleanup_moodle.py" --all --dry-run
    else
        write_section "CLEANUP — delete all test data on Moodle"
        echo -e "${YELLOW}This will DELETE users, courses, quizzes, assignments, and calendar events${RESET}"
        echo -e "${YELLOW}that match the TC-001..TC-006 + NFR test patterns.${RESET}"
        read -rp "Type 'DELETE' to confirm (anything else cancels): " confirm
        if [[ "$confirm" != "DELETE" ]]; then
            write_skip "Cleanup cancelled by user"
            return
        fi
        python3 "$REPO_ROOT/cleanup_moodle.py" --all
    fi
}

# ── Test runners ──────────────────────────────────────────────────────────────
invoke_smoke() {
    write_section "SMOKE TEST — TC_006_001 only (~30s)"
    (cd "$LEVEL1_DIR" && python3 -m pytest TC-006_code.py -v -k "TC_006_001")
    invoke_cleanup_auto
}

invoke_level1() {
    write_section "LEVEL 1 — all 6 TC files (TC-001_code.py .. TC-006_code.py)"
    (cd "$LEVEL1_DIR" && python3 -m pytest . -v)
    invoke_cleanup_auto
}

invoke_level2() {
    write_section "LEVEL 2 — all 169 cases in TC-ALL.py (~30 min)"
    (cd "$LEVEL2_DIR" && python3 -m pytest TC-ALL.py -v)
    invoke_cleanup_auto
}

invoke_nfr() {
    write_section "NFR — 6 files (Performance | Security | Accessibility | Reliability | Compatibility | Usability)"
    (cd "$NFR_DIR" && python3 -m pytest TC-001.py TC-002.py TC-003.py \
                                        TC-004.py TC-005.py TC-006.py -v)
    invoke_cleanup_auto
}

invoke_tc() {
    local num="${1:-}"
    if [[ ! "$num" =~ ^[0-9]{3}$ ]]; then
        write_fail "Bad TC number '$num' (expected 3 digits, e.g. '003')"
        return 1
    fi
    write_section "TC-$num — level1 + level2 + NFR"
    write_step "Level 1: TC-${num}_code.py"
    (cd "$LEVEL1_DIR" && python3 -m pytest "TC-${num}_code.py" -v)
    write_step "Level 2: TC-ALL.py -k TC_${num}"
    (cd "$LEVEL2_DIR" && python3 -m pytest TC-ALL.py -v -k "TC_${num}")
    write_step "NFR: TC-${num}.py"
    (cd "$NFR_DIR" && python3 -m pytest "TC-${num}.py" -v)
    invoke_cleanup_auto
}

invoke_locust() {
    write_section "LOCUST — Performance load testing (TC-001: Add-User form)"
    write_step "Starting Locust with TC-001.py"
    echo -e "${CYAN}-> Open http://localhost:8089 in your browser${RESET}"
    echo -e "${CYAN}-> Number of users: 50,  Spawn rate: 5${RESET}"
    echo -e "${CYAN}-> Host: https://xuansang1234.moodlecloud.com${RESET}"
    echo -e "${CYAN}-> Press Ctrl+C in this window when done${RESET}"
    (cd "$NFR_DIR" && locust -f TC-001.py)
}

invoke_all() {
    invoke_setup || return 1
    invoke_smoke
    invoke_level1
    invoke_level2
    invoke_nfr
    write_section "ALL TESTS DONE"
    write_ok "Suite complete. Locust load-tests are interactive — run them with:"
    echo -e "    ./run_all.sh locust"
}

# ── Interactive menu ──────────────────────────────────────────────────────────
show_menu() {
    write_section "PROJECT #3 — Group 11 — Master Test Runner"
    echo "  [1] Setup        - install Python packages          (~3 min)"
    echo "  [2] Smoke test   - 1 test case sanity check         (~30s)"
    echo "  [3] Level 1      - all TC-XXX_code.py files         (~30 min)"
    echo "  [4] Level 2      - all 169 cases in TC-ALL.py       (~30 min)"
    echo "  [5] NFR          - 6 files (perf/sec/a11y/rel/compat/usab) (~10 min)"
    echo "  [6] Locust       - TC-001 performance load-test (interactive)"
    echo "  [7] Single TC    - run one TC-XXX across all 3 dirs"
    echo "  [8] ALL          - everything                       (~1h30m)"
    echo "  [c] Cleanup      - delete test data from Moodle"
    echo "  [d] Cleanup DRY  - preview what cleanup would delete"
    echo "  [q] Quit"
    read -rp $'\nPick: ' choice
    case "$choice" in
        1) invoke_setup ;;
        2) invoke_smoke ;;
        3) invoke_level1 ;;
        4) invoke_level2 ;;
        5) invoke_nfr ;;
        6) invoke_locust ;;
        7)
            read -rp "Which TC? (001 / 002 / 003 / 004 / 005 / 006): " tcNum
            invoke_tc "$tcNum"
            ;;
        8) invoke_all ;;
        c) invoke_cleanup ;;
        d) invoke_cleanup dry ;;
        q) return ;;
        *) write_fail "Unknown option: $choice"; show_menu ;;
    esac
}

# ── Entry point ───────────────────────────────────────────────────────────────
MODE="${1:-menu}"
case "$MODE" in
    menu)        show_menu ;;
    setup)       invoke_setup ;;
    smoke)       invoke_smoke ;;
    level1)      invoke_level1 ;;
    level2)      invoke_level2 ;;
    nfr)         invoke_nfr ;;
    locust)      invoke_locust ;;
    cleanup)     invoke_cleanup ;;
    cleanup-dry) invoke_cleanup dry ;;
    all)         invoke_all ;;
    tc)
        shift
        invoke_tc "${1:-}"
        ;;
    *)
        write_fail "Unknown mode: $MODE"
        echo "Usage: ./run_all.sh [menu|setup|smoke|level1|level2|nfr|locust|cleanup|cleanup-dry|all|tc <NNN>]"
        exit 1
        ;;
esac
