#!/usr/bin/env zsh
# ──────────────────────────────────────────────────────────────────────────────
# run_tc001.sh  —  Run a single (or a range of) TC-001 test cases
#
# Usage:
#   ./run_tc001.sh                        # interactive picker
#   ./run_tc001.sh 5                      # run TC-001-005 only
#   ./run_tc001.sh 5 10                   # run TC-001-005 through TC-001-010
#   ./run_tc001.sh 5 10 20                # run TC-001-005, TC-001-010, TC-001-020
#   ./run_tc001.sh all                    # run every TC
# ──────────────────────────────────────────────────────────────────────────────

cd "$(dirname "$0")" || exit 1

# ── helpers ──────────────────────────────────────────────────────────────────
pad()  { printf "%03d" "$1"; }           # zero-pad to 3 digits
node() { echo "test_TC_001_$(pad $1)"; } # test method name

run_nodes() {
  local nodes=("$@")
  local filter=""
  for n in "${nodes[@]}"; do
    [[ -n "$filter" ]] && filter+=" or "
    filter+="$n"
  done
  echo "▶  Running: $filter"
  echo "────────────────────────────────────────"
  python3 -m pytest test_add_user_level1.py -v -k "$filter"
}

# ── argument parsing ──────────────────────────────────────────────────────────
if [[ $# -eq 0 ]]; then
  # interactive mode
  echo "TC-001 test cases available:"
  python3 - <<'PY'
import csv, pathlib
rows = list(csv.DictReader(open("test_data_tc001.csv")))
for r in rows:
    num = r["test_case_id"].split("-")[-1]
    print(f"  {num:>3}  username={r['username'] or '(empty)':30s}  expected={r['expected_result']}")
PY
  echo ""
  echo -n "Enter test number(s) separated by spaces (or 'all'): "
  read -r input
  set -- $input
fi

if [[ "$1" == "all" ]]; then
  echo "▶  Running ALL TC-001 tests"
  echo "────────────────────────────────────────"
  python3 -m pytest test_add_user_level1.py -v
  exit $?
fi

# build list of test node names from arguments
nodes=()
if [[ $# -eq 2 && "$1" =~ ^[0-9]+$ && "$2" =~ ^[0-9]+$ && "$1" -lt "$2" ]]; then
  # two numeric args → treat as range
  for (( i=$1; i<=$2; i++ )); do
    nodes+=( "$(node $i)" )
  done
else
  # individual numbers (possibly more than two)
  for arg in "$@"; do
    if [[ "$arg" =~ ^[0-9]+$ ]]; then
      nodes+=( "$(node $arg)" )
    else
      echo "⚠  Skipping invalid argument: $arg"
    fi
  done
fi

if [[ ${#nodes[@]} -eq 0 ]]; then
  echo "No valid test numbers given. Exiting."
  exit 1
fi

run_nodes "${nodes[@]}"
