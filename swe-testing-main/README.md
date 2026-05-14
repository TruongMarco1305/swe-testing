# Project #3 — Data-Driven Automation Testing (Group 11)

Python + Selenium data-driven re-testing of TC-001 through TC-006 on Moodle LMS.

---

## Prerequisites

- Python 3.9+
- Google Chrome (latest)
- **For ZAP security tests only:** Java 17+ and [OWASP ZAP](https://www.zaproxy.org/download/)

---

## Setup

```bash
git clone https://github.com/TruongMarco1305/swe-testing.git
cd swe-testing
pip install -r requirements.txt
```

Verify:
```bash
python -c "import selenium, locust, zapv2, axe_selenium_python; print('OK')"
```

---

## Running Tests

### Master runner (Windows PowerShell — recommended)

```powershell
.\run_all.ps1                       # Interactive menu
.\run_all.ps1 -Mode setup           # Install deps and verify environment
.\run_all.ps1 -Mode smoke           # 1-test sanity check
.\run_all.ps1 -Mode level1          # All Level 1 tests
.\run_all.ps1 -Mode level2          # All Level 2 tests
.\run_all.ps1 -Mode nfr-old         # Original test_non_functional.py
.\run_all.ps1 -Mode nfr-new         # 6 NFR files (auto-starts/stops ZAP)
.\run_all.ps1 -Mode nfr-skip-zap    # 6 NFR files, skip ZAP classes
.\run_all.ps1 -Mode locust          # Pick a Locust file to run
.\run_all.ps1 -Mode all             # Everything (~1h40m) with ZAP
.\run_all.ps1 -Mode all-no-zap      # Everything except ZAP tests
```

### Level 1

```bash
cd level1

python -m pytest test_add_user_level1.py -v    # TC-001 (43 cases)
python -m pytest test_course_level1.py -v      # TC-002 (27 cases)
python -m pytest test_assign_level1.py -v      # TC-003 (27 cases)
python -m pytest test_grade_level1.py -v       # TC-004 (17 cases)
python -m pytest test_event_level1.py -v       # TC-005 (28 cases)
python -m pytest test_quiz_level1.py -v        # TC-006 (27 cases)

python -m pytest . -v                          # All Level 1 (169 cases)
```

### Level 2

```bash
cd level2

python -m pytest test_level2.py -v                              # All 169 cases
python -m pytest test_level2.py -v -k "TestCreateUserLevel2"    # TC-001
python -m pytest test_level2.py -v -k "TestCreateCourseLevel2"  # TC-002
python -m pytest test_level2.py -v -k "TestAssignLevel2"        # TC-003
python -m pytest test_level2.py -v -k "TestGradeLevel2"         # TC-004
python -m pytest test_level2.py -v -k "TestCalendarEventLevel2" # TC-005
python -m pytest test_level2.py -v -k "TestQuizSetupLevel2"     # TC-006
```

### Non-Functional

```bash
cd non_functional

# Original Performance + Security tests
python -m pytest test_non_functional.py -v

# 6 NFR files — requires ZAP daemon running on port 8080
python -m pytest test_nfr_*.py -v

# Skip ZAP-dependent classes (no ZAP install needed)
python -m pytest test_nfr_*.py -v -k "not Zap and not SecurityHeaders and not ZapScan and not ZapInputFuzz"

# Accessibility classes only
python -m pytest test_nfr_*.py -v -k "Accessibility or A11y"

# Locust load tests — opens web UI at http://localhost:8089
locust -f test_nfr_01_login_perf_sec.py
locust -f test_nfr_02_login_perf_a11y.py
locust -f test_nfr_04_quiz_perf_sec.py
locust -f test_nfr_05_quiz_perf_a11y.py
```

### Run everything at once (from repo root)

```bash
# With ZAP running
python -m pytest level1/ level2/ non_functional/ -v

# Without ZAP
python -m pytest level1/ level2/ non_functional/ -v -k "not Zap and not SecurityHeaders and not ZapScan and not ZapInputFuzz"
```

---

## Cleanup

Remove test data created in Moodle after a run:

```bash
python cleanup_moodle.py --all --dry-run   # Preview only
python cleanup_moodle.py --all             # Delete everything
python cleanup_moodle.py --users           # Users only
python cleanup_moodle.py --courses         # Courses only
python cleanup_moodle.py --assignments     # Assignments only
python cleanup_moodle.py --quizzes         # Quizzes only
python cleanup_moodle.py --events          # Calendar events only
python cleanup_moodle.py --all --headless  # Headless (CI)
```

Via master runner:
```powershell
.\run_all.ps1 -Mode cleanup-dry   # Preview
.\run_all.ps1 -Mode cleanup       # Real (requires typing 'DELETE')
```