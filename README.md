# Project #3 - Data-Driven Automation Testing (Group 11)

## Setup

Install all dependencies:

```bash
pip install -r requirements.txt
```

Requires Python 3.9+ and Google Chrome (latest). `webdriver-manager` handles ChromeDriver automatically.

Or use the PowerShell helper (Windows):

```powershell
.\install_nfr_deps.ps1
```

---

## Quick Start (PowerShell — Windows)

The `run_all.ps1` script provides an interactive menu covering every mode:

```powershell
.\run_all.ps1              # interactive menu
.\run_all.ps1 -Mode setup  # install dependencies only
.\run_all.ps1 -Mode smoke  # 1-test smoke check (~30 s)
.\run_all.ps1 -Mode level1 # all Level 1 tests
.\run_all.ps1 -Mode level2 # all Level 2 tests
.\run_all.ps1 -Mode nfr    # all non-functional tests (pytest portion)
.\run_all.ps1 -Mode locust # interactive Locust load-test launcher
.\run_all.ps1 -Mode all    # everything (~1 h 30 m)

# Run one TC across all levels
.\run_all.ps1 -Mode tc -Tc 003
```

---

## Level 1

Each TC has its own script and CSV data file in `level1/`.

```bash
cd level1

python -m pytest TC-001_code.py -v   # TC-001  Admin Adds a New User         (43 cases)
python -m pytest TC-002_code.py -v   # TC-002  Admin Creates a New Course     (27 cases)
python -m pytest TC-003_code.py -v   # TC-003  Teacher Creates an Assignment  (27 cases)
python -m pytest TC-004_code.py -v   # TC-004  Teacher Grades an Assignment   (17 cases)
python -m pytest TC-005_code.py -v   # TC-005  User Creates a Calendar Event  (28 cases)
python -m pytest TC-006_code.py -v   # TC-006  Teacher Sets Up a Quiz         (27 cases)

# All Level 1 at once
python -m pytest . -v
```

Run a single test case by ID:

```bash
python -m pytest TC-001_code.py -v -k "TC_001_001"
```

---

## Level 2

All 6 TCs live in a single script (`TC-ALL.py`). Total: 169 cases.

```bash
cd level2

# All TCs
python -m pytest TC-ALL.py -v

# One TC class
python -m pytest TC-ALL.py -v -k "TestCreateUserLevel2"     # TC-001
python -m pytest TC-ALL.py -v -k "TestCreateCourseLevel2"   # TC-002
python -m pytest TC-ALL.py -v -k "TestAssignLevel2"         # TC-003
python -m pytest TC-ALL.py -v -k "TestGradeLevel2"          # TC-004
python -m pytest TC-ALL.py -v -k "TestCalendarEventLevel2"  # TC-005
python -m pytest TC-ALL.py -v -k "TestQuizSetupLevel2"      # TC-006
```

Run a single test case by ID:

```bash
python -m pytest TC-ALL.py -v -k "TC_004_002"
```

---

## Non-Functional Tests

Each TC file in `non_functional/` is dedicated to a single non-functional test type:

| File        | NFR Type        | Tool                        | Feature                  |
|-------------|-----------------|-----------------------------|--------------------------|
| `TC-001.py` | Performance     | `requests` + SLA timers     | Admin Adds a New User    |
| `TC-002.py` | Security        | `requests` passive probes   | Admin Creates a Course   |
| `TC-003.py` | Accessibility   | `axe-selenium-python` (WCAG)| Teacher Creates Assignment|
| `TC-004.py` | Reliability     | `requests` repeated loads   | Teacher Grades a Student |
| `TC-005.py` | Compatibility   | Selenium viewport resize    | Admin Creates Calendar Event|
| `TC-006.py` | Usability       | Selenium keyboard nav/focus | Teacher Creates a Quiz   |

### Run all NFR tests (pytest)

```bash
cd non_functional

python -m pytest TC-001.py -v   # Performance  — SLA checks
python -m pytest TC-002.py -v   # Security     — auth + CSRF + XSS probes
python -m pytest TC-003.py -v   # Accessibility — axe WCAG audit
python -m pytest TC-004.py -v   # Reliability  — repeated load consistency
python -m pytest TC-005.py -v   # Compatibility — Desktop / Tablet / Mobile viewports
python -m pytest TC-006.py -v   # Usability    — keyboard nav + focus indicators

# All at once
python -m pytest . -v
```

### Run Locust load test (Performance — TC-001 only, interactive)

Locust opens a browser UI at `http://localhost:8089`. Recommended settings:
users **50**, spawn rate **5**, host `https://xuansang1234.moodlecloud.com`.

```bash
cd non_functional
locust -f TC-001.py
```

Press `Ctrl+C` in the terminal to stop Locust.

---

## Run Everything

```bash
# From repo root
python -m pytest level1/ level2/ non_functional/ -v
```

Note: Locust load tests are interactive and are not included in the pytest run above.
Use `run_all.ps1 -Mode locust` or the `locust -f` commands above to run them.

---

## Cleanup

Delete test data created in Moodle during test runs:

```bash
python cleanup_moodle.py --all               # delete everything
python cleanup_moodle.py --users             # only users
python cleanup_moodle.py --courses           # only courses
python cleanup_moodle.py --assignments       # only assignments (course 10)
python cleanup_moodle.py --quizzes           # only quizzes (course 12)
python cleanup_moodle.py --events            # only calendar events

python cleanup_moodle.py --dry-run --all     # preview without deleting
```

Or via the PowerShell helper:

```powershell
.\run_all.ps1 -Mode cleanup      # delete all test data
.\run_all.ps1 -Mode cleanup-dry  # preview without deleting
```
