# Project #3 — Data-Driven Automation Testing (Group 11)

Re-testing of Project #2 test cases using Python + Selenium with a data-driven approach.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Setup](#setup)
4. [Project Structure](#project-structure)
5. [Test Suites](#test-suites)
   - [Level 1 — Data from CSV, hardcoded locators](#level-1--data-from-csv-hardcoded-locators)
   - [Level 2 — Data AND locators from CSV](#level-2--data-and-locators-from-csv)
   - [Non-Functional Tests](#non-functional-tests)
   - [Six NFR Files — Locust + OWASP ZAP + axe](#six-nfr-files--locust--owasp-zap--axe)
6. [Running the Tests](#running-the-tests)
7. [Master Test Runner (`run_all.ps1`)](#master-test-runner-run_allps1)
8. [Cleaning Up Moodle After a Test Run](#cleaning-up-moodle-after-a-test-run)
9. [Debugging a Single Test Case](#debugging-a-single-test-case)
10. [Known Moodle UI Quirks](#known-moodle-ui-quirks)
11. [Team Notes](#team-notes)
12. [Changelog](#changelog)

---

## Project Overview

| Item | Detail |
|---|---|
| **Target system** | Moodle LMS — `https://ihatetesting.moodlecloud.com/` |
| **Credentials** | `phuc.nguyen0310@hcmut.edu.vn` / `Huuphuc0310@` |
| **Framework** | Python 3.9 + Selenium 4 + unittest + pytest |
| **Features covered** | TC-001 (43) · TC-002 (27) · TC-003 (27) · TC-004 (17) · TC-005 (28) · TC-006 (27) |

---

## Prerequisites

- Python 3.9 or newer
- Google Chrome (latest)
- Internet connection to the Moodle site
- **Optional (only for OWASP ZAP security tests in the 6 NFR files):**
  - Java 17 or newer ([Adoptium Temurin 17](https://adoptium.net/temurin/releases/?version=17))
  - OWASP ZAP ([download installer](https://www.zaproxy.org/download/))

---

## Setup

```bash
# Clone the repo
git clone https://github.com/TruongMarco1305/swe-testing.git
cd swe-testing

# Install all required packages from requirements.txt
pip3 install -r requirements.txt
```

The `requirements.txt` pins:
- `selenium`, `webdriver-manager`, `pandas`, `openpyxl`, `pytest` — Level 1 & 2
- `locust`, `python-owasp-zap-v2.4`, `axe-selenium-python` — 6 NFR files

`webdriver-manager` automatically downloads the matching ChromeDriver — no manual driver installation needed.

### Verify install

```bash
python -c "import selenium, locust, zapv2, axe_selenium_python; print('OK')"
```

### One-line setup (Windows PowerShell)

```powershell
.\run_all.ps1 -Mode setup
```

This installs every dependency and probes Python, Chrome, and ZAP. See [Master Test Runner](#master-test-runner-run_allps1) below.

---

## Project Structure

```
swe-testing/
├── README.md
├── TC-001.krecorder          # Katalon Recorder source — Admin Adds a New User
├── TC-002.krecorder          # Katalon Recorder source — Admin Creates a Course
├── TC-003.krecorder          # Katalon Recorder source — Teacher Creates an Assignment
├── TC-004.krecorder          # Katalon Recorder source — Teacher Grades a Student Assignment
├── TC-005.krecorder          # Katalon Recorder source — Admin Creates a Calendar Event
├── TC-006.krecorder          # Katalon Recorder source — Teacher Creates a Quiz
├── Group_11.xlsx             # Original test case specification
├── Group_11.pdf
│
├── level1/
│   ├── test_data_tc001.csv        # TC-001 test data (43 rows)
│   ├── test_add_user_level1.py    # TC-001 Level 1 test script
│   ├── run_tc001.sh               # Helper: run individual TC-001 cases
│   ├── test_data_tc002.csv        # TC-002 test data (27 rows)
│   ├── test_course_level1.py      # TC-002 Level 1 test script
│   ├── test_data_tc003.csv        # TC-003 test data (27 rows)
│   ├── test_assign_level1.py      # TC-003 Level 1 test script
│   ├── test_data_tc004.csv        # TC-004 test data (17 rows)
│   ├── test_grade_level1.py       # TC-004 Level 1 test script
│   ├── test_data_tc005.csv        # TC-005 test data (28 rows)
│   ├── test_event_level1.py       # TC-005 Level 1 test script
│   ├── test_data_tc006.csv        # TC-006 test data (27 rows)
│   └── test_quiz_level1.py        # TC-006 Level 1 test script
│
├── level2/
│   ├── test_level2.py             # Single Level 2 script — all 6 TCs, 169 test cases
│   ├── test_data_tc001_level2.csv # TC-001 data + locators (43 rows)
│   ├── test_data_tc002_level2.csv # TC-002 data + locators (27 rows)
│   ├── test_data_tc003_level2.csv # TC-003 data + locators (27 rows)
│   ├── test_data_tc004_level2.csv # TC-004 data + locators (17 rows)
│   ├── test_data_tc005_level2.csv # TC-005 data + locators (28 rows)
│   └── test_data_tc006_level2.csv # TC-006 data + locators (27 rows)
│
├── non_functional/
│   ├── test_non_functional.py             # Performance + Security (original)
│   ├── test_nfr_01_login_perf_sec.py      # NFR #1 — Login: Locust + ZAP
│   ├── test_nfr_02_login_perf_a11y.py     # NFR #2 — Login: Locust + axe
│   ├── test_nfr_03_login_sec_a11y.py      # NFR #3 — Login: ZAP + axe
│   ├── test_nfr_04_quiz_perf_sec.py       # NFR #4 — Quiz form: Locust + ZAP
│   ├── test_nfr_05_quiz_perf_a11y.py      # NFR #5 — Quiz form: Locust + axe
│   └── test_nfr_06_quiz_sec_a11y.py       # NFR #6 — Quiz form: ZAP + axe
│
├── requirements.txt           # Pinned Python dependencies for all 3 levels
├── run_all.ps1                # Windows PowerShell master test runner
├── cleanup_moodle.py          # Delete test data from Moodle after a run
└── NFR.md                     # Spec for the 6 NFR files (Locust/ZAP/axe)
```

---

## Test Suites

### Level 1 — Data from CSV, hardcoded locators

Varying input values are read from a CSV file. Element locators are constants inside the Python script.

---

#### TC-001 — Admin Adds a New User (43 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc001.csv` | 43 rows — `username, password, firstname, lastname, email, expected_result` |
| `level1/test_add_user_level1.py` | Reads the CSV and generates one `unittest` test method per row |

**URL:** `https://ihatetesting.moodlecloud.com/user/editadvanced.php?id=-1`

**What is tested:**

| TC range | Boundary / scenario |
|---|---|
| 001 | Valid user — all fields at normal length → **success** |
| 002 | Empty username → **fail** |
| 003–004 | Username boundary lengths (min 1, min 2 chars) → **success** |
| 005 | Password too short (7 chars) → **fail** |
| 006–010 | Password boundary lengths (8 chars min → 128 chars max → over max) |
| 011 | Empty firstname → **fail** |
| 012–015 | Firstname boundary lengths |
| 016 | Empty lastname → **fail** |
| 017–020 | Lastname boundary lengths |
| 021–024 | Invalid username formats (uppercase, space, special char, reserved name) |
| 025–028 | Passwords missing required character class (no digit / no upper / no lower / no special) → **fail** |
| 029–031 | Invalid email formats (no @, truncated, embedded space) → **fail** |
| 032–033 | Normal valid re-run + "Generate password" checkbox path → **success** |
| 034 | Duplicate username → **fail** |
| 035–043 | Additional password & email edge cases |

**Special password handling:**  
Moodle's password field has a `readonly` attribute. The script bypasses it with JavaScript:
```python
driver.execute_script("""
  var i = document.getElementById('id_newpassword');
  i.removeAttribute('readonly');
  i.value = arguments[0];
  i.dispatchEvent(new Event('input', {bubbles:true}));
""", password_value)
```
Use `__generate__` as the password value in the CSV to tick the "Generate password and notify user" checkbox instead.

---

#### TC-002 — Admin Creates a New Course (27 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc002.csv` | 27 rows — `test_case_id, fullname, shortname, end_date_enabled, end_date_offset_days, end_date_offset_years, numsections, expected_result` |
| `level1/test_course_level1.py` | Reads the CSV and generates one test per row |

**URL:** `https://ihatetesting.moodlecloud.com/course/edit.php?category=1`

**What is tested:**

| TC range | Boundary / scenario |
|---|---|
| 001–004 | Course fullname boundaries (empty, 1 char, 2 chars, long) |
| 005–008 | Course shortname boundaries |
| 009–011 | End date: disabled / today / past / future |
| 012–016 | Number of sections (0, 1, 52, 53+) |
| 017–027 | Combinations of valid and invalid fields |

**Success check:** `"Announcements"` present in page source after submit.

---

#### TC-003 — Teacher Creates an Assignment (27 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc003.csv` | 27 rows — `test_case_id, name, gradepass, duedate_enabled, duedate_offset_days, duedate_offset_years, cutoff_offset_days, cutoff_offset_years, submission_file, submission_onlinetext, expected_result` |
| `level1/test_assign_level1.py` | Reads the CSV and generates one test per row |

**URL:** `https://ihatetesting.moodlecloud.com/course/modedit.php?add=assign&type&course=141&sectionid=695&return=0&beforemod=0`

**Role:** Logged in as admin, **switched to Teacher role** on course 141.

**What is tested:**

| TC range | Boundary / scenario |
|---|---|
| 001–004 | Assignment name boundaries (empty, 1 char, 2 chars, long) |
| 005–010 | Grade to pass boundaries (0, 0.01, 9.99, 10, 10.01, negative) |
| 011–016 | Due date: disabled / today / past / future |
| 017–022 | Cut-off date relative to due date |
| 023–027 | Submission type checkbox combinations (file / online text / both / neither) |

**Submit button:** `id_submitbutton2` (fallback: `id_submitbutton`).  
**Success check:** `"Announcements"` present in page source.

---

#### TC-004 — Teacher Grades a Student Assignment (17 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc004.csv` | 17 rows — `test_case_id, grade, expected_result` |
| `level1/test_grade_level1.py` | Reads the CSV and generates one test per row |

**URL:** `https://ihatetesting.moodlecloud.com/mod/assign/view.php?id=321&action=grader`

**Role:** Logged in as admin, **switched to Teacher role**.

**What is tested:**

| TC range | Boundary / scenario |
|---|---|
| 001–004 | Grade boundaries (0, 0.01, 99.99, 100) → **success** |
| 005–006 | Grade out of range (−1, 100.01) → **fail** |
| 007–010 | Non-numeric grades (letters, symbols, empty) |
| 011–017 | Decimal precision and edge values |

**React-compatible grade setter:**
```python
driver.execute_script("""
  var setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value').set;
  setter.call(el, arguments[0]);
  el.dispatchEvent(new Event('input', {bubbles: true}));
""", grade_value)
```
**Success check:** JS-injected `#__test_marker[data-has-error="no"]` element.

---

#### TC-005 — Admin Creates a Calendar Event (28 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc005.csv` | 28 rows — `test_case_id, name, duration_type, minutes, until_offset_days, repeat, expected_result` |
| `level1/test_event_level1.py` | Reads the CSV and generates one test per row |

**URL:** `https://ihatetesting.moodlecloud.com/calendar/view.php?view=month`

**What is tested:**

| TC range | Boundary / scenario |
|---|---|
| 001–004 | Event name boundaries (empty, 1 char, 2 chars, long) |
| 005–010 | Duration in minutes boundaries (0, 1, 2, 9999998, 9999999, 10000000) |
| 011–015 | Duration "until date" offset (−1, 0, +1, +364, +365 days) |
| 016–018 | Invalid minutes values (1.5 decimal, text, negative) |
| 019–024 | `duration_type` combinations: `none` / `minutes` / `until` |
| 022–024 | Repeat checkbox enabled |
| 025–028 | Mixed name + minutes edge cases |

**Duration types:** `none` (radio `0`) · `minutes` (radio `1`) · `until` (radio `2`).  
**Modal submit:** `//div[@role='dialog']//button[@data-action='save']`.  
**Success check:** modal closes and `"Calendar"` present in page source.

---

#### TC-006 — Teacher Creates a Quiz (27 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc006.csv` | 27 rows — `test_case_id, name, timeclose_enabled, close_offset_days, close_offset_years, timelimit_enabled, timelimit_number, gradepass, expected_result` |
| `level1/test_quiz_level1.py` | Reads the CSV and generates one test per row |

**URL:** `https://ihatetesting.moodlecloud.com/course/modedit.php?add=quiz&type&course=152&sectionid=750&return=0&beforemod=0`

**Role:** Logged in as admin, **switched to Teacher role** on course 152, editing mode on.

**What is tested:**

| TC range | Boundary / scenario |
|---|---|
| 001–004 | Grade to pass boundaries (5, 9.99, 10 → success; 10.01 → fail) |
| 005–010 | Time limit boundaries (−1 → fail; 0, 1, 998, 999, 1000 → success) |
| 011–016 | Close date boundaries (−1 day → fail; today, +1 day, +10/11/12 years → success) |
| 017, 027 | Empty quiz name → **fail** |
| 018–024 | Combinations of timelimit/timeclose enabled or disabled |
| 025–026 | Close date yesterday + gradepass 10.01 repeated variants → **fail** |

**Success check:** `"Announcements"` present in page source.

---

### Level 2 — Data AND locators from CSV

Everything — site URL, credentials, locator types, locator values, and test data — is read from CSV files. The Python script contains **no hardcoded selectors or URLs**.

#### Architecture

All Level 2 tests live in a single file: **`level2/test_level2.py`**.

```
test_level2.py
├── load_csv(filename)          # reads a CSV from the same directory
├── loc(row, prefix)            # resolves (By.X, "value") from two CSV columns
├── _BaseLevel2                 # shared base class (login, session recovery, teardown)
│   ├── setUpClass              # opens Chrome, logs in once for the whole suite
│   ├── _start_driver           # creates a maximised ChromeDriver instance
│   ├── _dismiss_cookie_banner  # accepts OneTrust banner
│   ├── _login                  # navigates to login URL from CSV, fills credentials
│   ├── _recover                # re-creates driver + re-logs in if session dies
│   └── setUp                   # probes current_url before each test; calls _recover if dead
│
├── TestCreateUserLevel2        # TC-001 — Admin Adds a New User       (43 tests)
├── TestCreateCourseLevel2      # TC-002 — Admin Creates a New Course   (27 tests)
├── TestAssignLevel2            # TC-003 — Teacher Creates an Assignment (27 tests)
├── TestGradeLevel2             # TC-004 — Teacher Grades an Assignment  (17 tests)
├── TestCalendarEventLevel2     # TC-005 — Admin Creates a Calendar Event (28 tests)
└── TestQuizSetupLevel2         # TC-006 — Teacher Creates a Quiz        (27 tests)
                                                              Total: 169 tests
```

#### Locator resolution

Each CSV contains a pair of columns per interactive element:
- `<prefix>_locator_type` — one of `id`, `name`, `css`, `xpath`, `link text`, `partial link text`, `tag name`, `class name`
- `<prefix>_locator_value` — the selector string

The `loc()` helper maps the type string to a `selenium.webdriver.common.by.By` constant at runtime:
```python
BY_MAP = {
    "id": By.ID, "name": By.NAME, "css": By.CSS_SELECTOR,
    "xpath": By.XPATH, "link text": By.LINK_TEXT,
    "partial link text": By.PARTIAL_LINK_TEXT,
    "tag name": By.TAG_NAME, "class name": By.CLASS_NAME,
}

def loc(row, prefix):
    return BY_MAP[row[f"{prefix}_locator_type"].strip().lower()], \
           row[f"{prefix}_locator_value"].strip()
```

#### Test factory pattern

Each TC class generates one `unittest` test method per CSV row at import time using `setattr`:
```python
def _make_user_test(row):
    def test_method(self):
        self._fill_and_submit(row)
        self.assertEqual(self._get_outcome(), row["expected_result"].strip(), ...)
    test_method.__name__ = f"test_{row['test_case_id'].replace('-','_')}"
    return test_method

for _r in load_csv("test_data_tc001_level2.csv"):
    setattr(TestCreateUserLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_user_test(_r))
```
This means pytest collects them as normal test methods — no plugin or fixture magic needed.

---

#### TC-001 Level 2 — Admin Adds a New User (43 test cases)

| File | Columns |
|---|---|
| `test_data_tc001_level2.csv` | `test_case_id, site_url, login_url_suffix, new_user_url, username, password, firstname, lastname, email, expected_result` + locator pairs for `username`, `firstname`, `lastname`, `email`, `save_btn` |

**Special:** `password = __generate__` → ticks the "Generate password" checkbox instead of injecting a value.  
**Success check:** `"Changes saved"` in page source.

---

#### TC-002 Level 2 — Admin Creates a New Course (27 test cases)

| File | Columns |
|---|---|
| `test_data_tc002_level2.csv` | `test_case_id, site_url, login_url_suffix, new_course_url, username, password, fullname, shortname, end_date_enabled, end_date_offset_days, end_date_offset_years, numsections, expected_result` + locator pairs for `fullname`, `shortname`, `save_btn` |

**End date:** computed as `today + offset_years + offset_days`; set via JS `sS()` on the day/month/year `<select>` elements. When `end_date_enabled = no`, the checkbox `id_enddate_enabled` is unchecked.  
**Success check:** `"Announcements"` in page source.

---

#### TC-003 Level 2 — Teacher Creates an Assignment (27 test cases)

| File | Columns |
|---|---|
| `test_data_tc003_level2.csv` | `test_case_id, site_url, login_url_suffix, assign_url, username, password, name, gradepass, duedate_enabled, duedate_offset_days, duedate_offset_years, cutoff_offset_days, cutoff_offset_years, submission_file, submission_onlinetext, expected_result` + locator pairs for `name`, `gradepass`, `save_btn` |

**Role switch:** `TestAssignLevel2.setUpClass` navigates to `/course/switchrole.php?id=1&switchrole=-1` and clicks "Teacher" before any tests run.  
**Dates:** all set via JS `ens()`/`dis()`/`sS()` helpers injected in one `execute_script` call.  
**Submission types:** only changed when column is not `"default"`.  
**Success check:** `"Announcements"` in page source or `.activity-header` CSS selector found.

---

#### TC-004 Level 2 — Teacher Grades a Student Assignment (17 test cases)

| File | Columns |
|---|---|
| `test_data_tc004_level2.csv` | `test_case_id, site_url, login_url_suffix, grade_url, username, password, grade, expected_result` + locator pairs for `grade_input`, `save_btn` |

**Grade injection:** React-compatible setter via JS `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` + `input`/`change` events.  
**Success check:** JS injects a sentinel element `#__test_marker`; `data-has-error="no"` → success, `"yes"` → fail.

---

#### TC-005 Level 2 — Admin Creates a Calendar Event (28 test cases)

| File | Columns |
|---|---|
| `test_data_tc005_level2.csv` | `test_case_id, site_url, login_url_suffix, calendar_url, username, password, event_name, duration_type, minutes, until_offset_days, repeat, expected_result` + locator pairs for `event_name`, `save_btn` |

**Duration types:** `none` (radio `0`) · `minutes` (radio `1`, sets minutes field) · `until` (radio `2`, sets date selects via JS offset from today).  
**Modal submit:** XPath `//div[@role='dialog']//button[@data-action='save']`.  
**Success check:** modal closes + `"Calendar"` in page source.

---

#### TC-006 Level 2 — Teacher Creates a Quiz (27 test cases)

| File | Columns |
|---|---|
| `test_data_tc006_level2.csv` | `test_case_id, site_url, login_url_suffix, quiz_url, username, password, quiz_name, timeclose_enabled, close_offset_days, close_offset_years, timelimit_enabled, timelimit_number, gradepass, expected_result` + locator pairs for all interactive elements |

**Role switch:** switches to Teacher role on course 152 before tests begin.  
**Success check:** `"Announcements"` in page source.

---

#### Running Level 2 tests

```bash
cd level2

# Collect all 169 tests (dry run)
python3 -m pytest test_level2.py --collect-only -q

# Run all Level 2 tests
python3 -m pytest test_level2.py -v

# Run a single TC class
python3 -m pytest test_level2.py -v -k "TestCreateUserLevel2"

# Run a single test case by ID
python3 -m pytest test_level2.py -v -k "TC_001_024"
```

---

### Non-Functional Tests

| File | `non_functional/test_non_functional.py` |
|---|---|
| **Feature under test** | Teacher Sets Up a Quiz (same Moodle flow as TC-006) |
| **Test classes** | `TestPerformance` · `TestSecurity` |

---

#### Performance Tests (`TestPerformance`)

SLA thresholds are defined as constants at the top of the file and can be adjusted without touching test logic.

| Constant | Default | What it guards |
|---|---|---|
| `LOGIN_PAGE_LOAD_THRESHOLD` | 5.0 s | Time from `driver.get(LOGIN_URL)` until `#loginbtn` is present on a fresh unauthenticated session |
| `QUIZ_FORM_LOAD_THRESHOLD` | 8.0 s | Time from `driver.get(QUIZ_ADD_URL)` until `#id_name` is present |
| `QUIZ_SAVE_THRESHOLD` | 6.0 s | Time from clicking **Save and return to course** until `.course-content` or `#page-header` is present |

| Test | ID | What is measured |
|---|---|---|
| `test_01_login_page_load_time` | PERF-01 | Login page full load time — measured on a **fresh unauthenticated session**; logs in afterward for subsequent tests |
| `test_02_quiz_form_load_time` | PERF-02 | Quiz creation form load time via direct URL (`modedit.php?add=quiz&...`) |
| `test_03_quiz_save_response_time` | PERF-03 | Round-trip time after clicking Save (JS click on `id_submitbutton2`) |

Each test prints a `[PERF]` line with the exact measured time and threshold for easy CI log inspection.

---

#### Security Tests (`TestSecurity`)

| Test | ID | What is verified |
|---|---|---|
| `test_01_password_field_is_masked` | SEC-01 | `<input id="password">` has `type="password"` — value is never visible in the DOM |
| `test_02_xss_payloads_in_quiz_name_not_executed` | SEC-02 | 5 XSS / SQL-injection payloads submitted as Quiz Name — no `alert()` is triggered; no `Traceback` or `Fatal error` appears in page source |
| `test_03_https_used` | SEC-03 | Login page and course page are both served over `https://` |
| `test_04_no_credentials_in_url` | SEC-04 | After login, `current_url` contains neither the username nor the password |

**XSS payloads tested:**
```
<script>alert('xss')</script>
' OR '1'='1
" OR "1"="1
<img src=x onerror=alert(1)>
'; DROP TABLE mdl_quiz; --
```

---

#### Helper functions (shared by both test classes)

| Function | Purpose |
|---|---|
| `_make_driver()` | Creates a maximised Chrome instance via `webdriver-manager` |
| `_dismiss_cookie_banner(driver)` | Tries to click `#onetrust-accept-btn-handler`; waits for the dark overlay to disappear |
| `_login(driver, wait)` | Navigates to login page, dismisses banner, hides overlay via JS, fills credentials, JS-clicks `loginbtn`, waits for `url_contains("/my/")` |
| `_open_quiz_add_form(driver, wait)` | Navigates directly to `modedit.php?add=quiz&course=152&sectionid=750` and waits for `#id_name` |
| `_fill_minimal_quiz(driver, name)` | Fills quiz name via `send_keys`; sets open/close dates via JS `sS()`/`ens()` helpers (same pattern as TC-006) |

**Session setup pattern** — neither `TestPerformance` nor `TestSecurity` pre-logs in during `setUpClass`. Instead, `test_01` in each class starts on a **fresh unauthenticated session** (so the login page is real), then logs in at the end of that test so `test_02`–`test_04` have an authenticated session to work with.

---

### Six NFR Files — Locust + OWASP ZAP + axe

In addition to `test_non_functional.py`, the project ships **6 dedicated NFR files** that implement the three Python-native NFR techniques described in [NFR.md](NFR.md):

| Technique | Tool | Pip package |
|---|---|---|
| **Performance load testing** | [Locust](https://locust.io) | `locust` |
| **Security scanning** | [OWASP ZAP Python API](https://www.zaproxy.org/docs/api/) | `python-owasp-zap-v2.4` |
| **Accessibility auditing** | [axe-selenium-python](https://github.com/mozilla-services/axe-selenium-python) | `axe-selenium-python` |

Each file applies **2 of the 3 techniques** to one of the two main user flows (Login or Quiz Setup):

| File | Flow | NFR-1 | NFR-2 |
|---|---|---|---|
| `test_nfr_01_login_perf_sec.py` | Login | Locust (Perf) | OWASP ZAP (Sec) |
| `test_nfr_02_login_perf_a11y.py` | Login | Locust (Perf) | axe (A11y) |
| `test_nfr_03_login_sec_a11y.py` | Login | OWASP ZAP (Sec) | axe (A11y) |
| `test_nfr_04_quiz_perf_sec.py` | Quiz add form | Locust (Perf) | OWASP ZAP (Sec) |
| `test_nfr_05_quiz_perf_a11y.py` | Quiz add form | Locust (Perf) | axe (A11y) |
| `test_nfr_06_quiz_sec_a11y.py` | Quiz add form | OWASP ZAP (Sec) | axe (A11y) |

#### Dual-class file layout

Each file contains both a `locust.HttpUser` subclass **and** one or two `unittest.TestCase` subclasses. They are invoked separately:

- `locust -f <file>` picks up the `HttpUser` class and opens the Locust web UI
- `python -m pytest <file>` picks up the `TestCase` classes (ZAP and/or axe tests)

There is no interference between the two — pytest silently ignores `HttpUser` (it is not a `TestCase`), and Locust ignores `TestCase` (it is not an `HttpUser`).

#### Pre-requisites by file

| Pre-requisite | Required for files | How to satisfy |
|---|---|---|
| Selenium + Chrome (already required) | All 6 | Step 3 of [Setup](#setup) |
| `locust` package | 01, 02, 04, 05 | `pip install locust` (covered by `requirements.txt`) |
| `axe-selenium-python` package | 02, 03, 05, 06 | `pip install axe-selenium-python` (covered) |
| `python-owasp-zap-v2.4` package | 01, 03, 04, 06 | `pip install python-owasp-zap-v2.4` (covered) |
| **OWASP ZAP daemon running** | 01, 03, 04, 06 | See "Running the ZAP-based tests" below |

#### Running the ZAP-based tests

Start ZAP in **daemon mode** before invoking pytest on any file that contains a ZAP test class. Open a **second PowerShell window** so the daemon stays alive:

```powershell
& "C:\Program Files\ZAP\Zed Attack Proxy\zap.bat" -daemon -port 8080 -config api.disablekey=true
```

Wait until you see `ZAP is now listening on 0.0.0.0:8080`, then verify in a third window:

```powershell
Invoke-WebRequest http://127.0.0.1:8080 -UseBasicParsing | Select-Object StatusCode
```

→ Must return `StatusCode : 200`. Now run any ZAP-dependent file:

```powershell
cd non_functional
python -m pytest test_nfr_01_login_perf_sec.py -v
```

If you **do not** want to install ZAP, run only the non-ZAP test classes:

```powershell
cd non_functional
python -m pytest . -v -k "not Zap and not SecurityHeaders and not ZapScan and not ZapInputFuzz"
```

This still runs every Locust + axe test class across all 6 files.

#### Running the Locust load tests

Locust has its own CLI — it does **not** run via `pytest`. Pick any of the 4 Locust-enabled files:

```powershell
cd non_functional
locust -f test_nfr_01_login_perf_sec.py
```

Open **http://localhost:8089** in a browser, fill in:
- **Number of users**: `50`
- **Spawn rate**: `5`
- **Host**: `https://ihatetesting.moodlecloud.com` (already set inside the file)

Click **Start swarming** → watch RPS, p95 latency, and failure rate in real time. Headless variant for CI:

```powershell
locust -f test_nfr_01_login_perf_sec.py --headless -u 50 -r 5 -t 1m
```

#### Accessibility report files

Each axe test class writes a JSON report next to itself for the QA evidence pack:

| File generated | Source |
|---|---|
| `non_functional/a11y_login_report.json` | `test_nfr_02_login_perf_a11y.py` |
| `non_functional/a11y_quiz_form_report.json` | `test_nfr_05_quiz_perf_a11y.py` |
| `non_functional/a11y_quiz_empty_report.json` | `test_nfr_06_quiz_sec_a11y.py` |
| `non_functional/a11y_quiz_errors_report.json` | `test_nfr_06_quiz_sec_a11y.py` |

#### Authenticated Locust users (files 04, 05)

Files 04 and 05 hit the authenticated Quiz add form, so their `HttpUser.on_start()` performs a real login by:
1. `GET /login/index.php` to harvest the `logintoken` hidden input
2. `POST /login/index.php` with `username`/`password`/`logintoken`

This means every virtual user counts as a real Moodle session — keep the user count modest (≤ 50) when running against the shared Moodle Cloud instance.

---

## Running the Tests

All commands should be run from **inside the relevant folder**.

### Run individual Level 1 test suites
```bash
cd level1

# TC-001 — Admin Adds a New User (43 cases)
python3 -m pytest test_add_user_level1.py -v

# TC-002 — Admin Creates a New Course (27 cases)
python3 -m pytest test_course_level1.py -v

# TC-003 — Teacher Creates an Assignment (27 cases)
python3 -m pytest test_assign_level1.py -v

# TC-004 — Teacher Grades a Student Assignment (17 cases)
python3 -m pytest test_grade_level1.py -v

# TC-005 — Admin Creates a Calendar Event (28 cases)
python3 -m pytest test_event_level1.py -v

# TC-006 — Teacher Creates a Quiz (27 cases)
python3 -m pytest test_quiz_level1.py -v
```

### Run all Level 1 tests at once
```bash
cd level1
python3 -m pytest . -v
```

### Run all Level 2 tests (169 cases across 6 TCs)
```bash
cd level2
python3 -m pytest test_level2.py -v

# Run a single TC class
python3 -m pytest test_level2.py -v -k "TestCreateUserLevel2"
python3 -m pytest test_level2.py -v -k "TestCreateCourseLevel2"
python3 -m pytest test_level2.py -v -k "TestAssignLevel2"
python3 -m pytest test_level2.py -v -k "TestGradeLevel2"
python3 -m pytest test_level2.py -v -k "TestCalendarEventLevel2"
python3 -m pytest test_level2.py -v -k "TestQuizSetupLevel2"
```

### Run all TC-006 Level 2 tests
```bash
cd level2
python3 -m pytest test_level2.py -v -k "TestQuizSetupLevel2"
```

### Run non-functional tests

#### Original Performance + Security tests
```bash
cd non_functional
python3 -m pytest test_non_functional.py -v
```

#### 6 NFR files (Security + Accessibility classes via pytest)

Start ZAP daemon first (see [Six NFR Files](#six-nfr-files--locust--owasp-zap--axe)), then:

```bash
cd non_functional

# All 6 files
python3 -m pytest test_nfr_*.py -v

# Skip ZAP-dependent classes (no ZAP install needed)
python3 -m pytest . -v -k "not Zap and not SecurityHeaders and not ZapScan and not ZapInputFuzz"

# Just the accessibility classes across all files
python3 -m pytest . -v -k "Accessibility or A11y"
```

#### 6 NFR files (Performance via Locust — interactive web UI)

```bash
cd non_functional
locust -f test_nfr_01_login_perf_sec.py     # Login load test
locust -f test_nfr_02_login_perf_a11y.py    # Login load test (a11y companion)
locust -f test_nfr_04_quiz_perf_sec.py      # Quiz form load test (authenticated)
locust -f test_nfr_05_quiz_perf_a11y.py     # Quiz form load test (a11y companion)
```

Each command opens http://localhost:8089 — configure user count there.

### Run everything at once (from repo root)

With ZAP daemon running:
```bash
python3 -m pytest level1/ level2/ non_functional/ -v
```

Without ZAP (skips 12 ZAP test methods, runs everything else):
```bash
python3 -m pytest level1/ level2/ non_functional/ -v -k "not Zap and not SecurityHeaders and not ZapScan and not ZapInputFuzz"
```

---

## Master Test Runner (`run_all.ps1`)

`run_all.ps1` is a single PowerShell entry point that handles install + ZAP daemon lifecycle + sequenced test runs. Use it instead of memorising the individual pytest/locust commands.

### Interactive menu (recommended)
```powershell
.\run_all.ps1
```

Shows a numbered menu — pick `1` to install, `2` for a smoke test, `9` to run everything end-to-end.

### Non-interactive modes
```powershell
.\run_all.ps1 -Mode setup           # Install Python deps and probe Chrome/ZAP
.\run_all.ps1 -Mode smoke           # 1-test sanity check (~30s)
.\run_all.ps1 -Mode level1          # All Level 1 tests
.\run_all.ps1 -Mode level2          # All Level 2 tests
.\run_all.ps1 -Mode nfr-old         # Original test_non_functional.py
.\run_all.ps1 -Mode nfr-new         # 6 NFR files (auto-starts/stops ZAP)
.\run_all.ps1 -Mode nfr-skip-zap    # 6 NFR files, skip ZAP test classes
.\run_all.ps1 -Mode locust          # Pick a Locust file to run
.\run_all.ps1 -Mode all             # Everything (~1h40m) with ZAP
.\run_all.ps1 -Mode all-no-zap      # Everything except ZAP tests
```

### Override ZAP path
```powershell
.\run_all.ps1 -Mode nfr-new -ZapPath "C:\Tools\ZAP\zap.bat"
```

### What the script does

1. **Setup phase** — installs from `requirements.txt`, verifies all 8 modules import.
2. **ZAP daemon lifecycle** — starts ZAP hidden, polls `http://127.0.0.1:8080` until it returns 200, kills the process on exit (even on Ctrl+C).
3. **Test sequence** — runs smoke → Level 1 → Level 2 → NFR (old) → NFR (new) in order; stops on first hard failure but always cleans up ZAP.
4. **Locust mode** — interactive: lists the 4 Locust-enabled files, prompts for choice, launches `locust -f <file>` so you can open the web UI.
5. **Cleanup mode** — invokes `cleanup_moodle.py` to delete test data from Moodle (see next section).

---

## Cleaning Up Moodle After a Test Run

By design, the test suites do **not** delete the users, courses, quizzes, assignments, or calendar events they create. This is intentional so that TC-001-034 (duplicate-username) and similar tests still work in sequence. Over many runs, however, the Moodle Cloud demo site accumulates test artifacts.

`cleanup_moodle.py` is a Selenium-driven script that logs in as admin and removes everything matching the test data patterns:

| Category | Patterns | Source |
|---|---|---|
| Users | `usr*`, `test_*`, `username*` | TC-001 |
| Courses | fullname `fn*`, shortname `sn*` | TC-002 |
| Assignments (in course 141) | `an*`, `test_assign*` | TC-003 |
| Quizzes (in course 152) | `qn*`, `perf_*`, `xss_*`, XSS payloads, SQLi payloads | TC-006 + NFR files |
| Calendar events | `t*`, `test_event*` | TC-005 |

### Safety guards

- **Never deletes** the admin account `phuc.nguyen0310@hcmut.edu.vn`, the Moodle built-in `admin`, courses `141` or `152` themselves, or the site front page (course `1`).
- Has a `--dry-run` mode that lists every match without deleting anything.
- Each deletion prints `[DEL]` with the ID and name; skipped items print `[SKIP]`; failures print `[WARN]`.

### Usage

```bash
# Dry-run: list everything that would be deleted
python cleanup_moodle.py --all --dry-run

# Real cleanup of everything
python cleanup_moodle.py --all

# Cleanup individual categories
python cleanup_moodle.py --users
python cleanup_moodle.py --courses
python cleanup_moodle.py --assignments
python cleanup_moodle.py --quizzes
python cleanup_moodle.py --events

# Run headless (no browser window — good for CI)
python cleanup_moodle.py --all --headless
```

### Via the master runner

```powershell
.\run_all.ps1 -Mode cleanup-dry     # Preview - safe
.\run_all.ps1 -Mode cleanup         # Real - asks for 'DELETE' confirmation
```

The interactive menu shows `[c]` (cleanup) and `[d]` (cleanup dry-run) as new options.

---

## Changelog

### Non-Functional Expansion + Master Runner (May 2026)

**What was added:**

| Artifact | Purpose |
|---|---|
| `non_functional/test_nfr_01_login_perf_sec.py` | Login: Locust load + OWASP ZAP active scan |
| `non_functional/test_nfr_02_login_perf_a11y.py` | Login: Locust load + axe-core accessibility audit |
| `non_functional/test_nfr_03_login_sec_a11y.py` | Login: ZAP passive header audit + axe colour-contrast & focus-order |
| `non_functional/test_nfr_04_quiz_perf_sec.py` | Quiz form: authenticated Locust load + ZAP active scan |
| `non_functional/test_nfr_05_quiz_perf_a11y.py` | Quiz form: authenticated Locust load + axe full audit |
| `non_functional/test_nfr_06_quiz_sec_a11y.py` | Quiz form: ZAP XSS/SQLi fuzz + axe on populated & error-state forms |
| `requirements.txt` | Pinned dependencies for all 3 levels |
| `run_all.ps1` | Master PowerShell runner with interactive menu and ZAP lifecycle |
| `cleanup_moodle.py` | Selenium-driven cleanup of users/courses/quizzes/events/assignments after a run |
| `NFR.md` | Spec describing the 3 NFR techniques (Locust / ZAP / axe) |

**Coverage matrix:** each of the 6 NFR files implements exactly 2 of the 3 techniques, ensuring all 3 pairwise combinations are demonstrated twice (once for Login, once for Quiz Setup) — see [Six NFR Files](#six-nfr-files--locust--owasp-zap--axe).

**Backwards compatibility:** the original `test_non_functional.py` is unchanged — pure Selenium, no Locust/ZAP/axe dependency. Anyone who only installs the original `selenium webdriver-manager pandas openpyxl pytest` stack can still run it.

---

### Level 2 — Complete Rewrite (May 2026)

**Before:** Level 2 contained a single file (`test_quiz_level2.py`) covering only TC-006 with a single CSV (`test_data_level2.csv`).

**After:** Level 2 was fully rebuilt into a unified architecture covering all 6 test cases:

| What changed | Detail |
|---|---|
| Single script | `test_quiz_level2.py` → `test_level2.py` (all TCs in one file) |
| Base class | `_BaseLevel2` shared base handles login, session recovery, cookie banner, and teardown for every TC subclass |
| New TCs added | TC-001, TC-002, TC-003, TC-004, TC-005 each got a Level 2 class and CSV |
| Test count | 27 → **169** collected tests |
| Locator pattern | Unified `loc(row, prefix)` helper reads `<prefix>_locator_type` + `<prefix>_locator_value` from CSV |
| Factory pattern | Each TC uses a `_make_XYZ_test(row)` closure + `setattr` loop — no pytest fixtures or plugins needed |
| Session recovery | `setUp()` probes `driver.current_url` before each test; calls `_recover()` on dead sessions |

**Files added:**
- `level2/test_level2.py`
- `level2/test_data_tc001_level2.csv` (43 rows)
- `level2/test_data_tc002_level2.csv` (27 rows)
- `level2/test_data_tc003_level2.csv` (27 rows)
- `level2/test_data_tc004_level2.csv` (17 rows)
- `level2/test_data_tc005_level2.csv` (28 rows)
- `level2/test_data_tc006_level2.csv` (27 rows, renamed from `test_data_level2.csv`)

**TC-003 special note:** `TestAssignLevel2.setUpClass` overrides the base to also switch the admin session to Teacher role on course 141 before any assignment tests run.

**TC-001 special note:** Password column supports `__generate__` as a sentinel value — the script ticks the "Generate password and notify user" checkbox instead of injecting a password string.

---

## Debugging a Single Test Case

A helper shell script `level1/run_tc001.sh` lets you run one or more TC-001 cases without executing the whole suite.

```bash
cd level1

# Single test case (TC-001-024)
./run_tc001.sh 24

# Range of test cases (005 through 010 inclusive)
./run_tc001.sh 5 10

# Multiple individual cases
./run_tc001.sh 5 10 20 34

# All test cases
./run_tc001.sh all

# Interactive mode — shows a table then prompts for input
./run_tc001.sh
```

For TC-006, use pytest's `-k` flag directly:
```bash
# Run a single TC-006 case
python3 -m pytest test_quiz_level1.py -v -k "TC_006_005"

# Run a range using regex
python3 -m pytest test_quiz_level1.py -v -k "TC_006_00[1-5]"
```

---

## Known Moodle UI Quirks

These issues were discovered during development and are already handled in all scripts.

| Issue | Root cause | Fix applied |
|---|---|---|
| Login button click fails | OneTrust cookie banner overlays the button | Try `#onetrust-accept-btn-handler` click first; then hide overlay via JS; finally JS-click `loginbtn` |
| Edit mode toggle not found | Moodle 4.x changed the input name from `setediting` → `setmode` | Use `input[name='setmode']`, then click its `<label>` via JS |
| "Add activity" button invisible | Moodle 4.x hides it until hover | `ActionChains.move_to_element(section).perform()` before clicking |
| Submit button intercepted | Sticky footer or banner sits on top of button when it is near the bottom | `scrollIntoView({block:'center'})` + JS click |
| Password field `readonly` | Moodle sets `readonly` on `id_newpassword` to force its own generator | Remove attribute + set value + dispatch `input`/`change`/`blur` events via JS |
| Calendar modal stays open (false fail) | `[id^="id_error_"]` spans exist in the DOM as hidden placeholders even when there's no error | Check `EC.invisibility_of_element_located("div[role='dialog']")` — if modal closes → success; if it stays → fail |
| Chrome session dies mid-suite | Injecting non-string values (e.g. `"abc"`) via the React setter can crash the renderer | `setUp()` probes `driver.current_url` before each test and calls `_new_driver()` to recover; the outcome block also catches `InvalidSessionIdException` inline |
| Non-functional test_01 times out on login page | `setUpClass` pre-logged in, so Moodle redirected away before `#loginbtn` rendered | Removed pre-login from `setUpClass`; `test_01` now runs on a fresh unauthenticated session and logs in at the end |
| `_open_quiz_add_form` timed out navigating activity chooser | Moodle 4.x hover → modal → confirm chain is too fragile | Replaced entirely with direct `modedit.php?add=quiz&...` URL navigation |

---

## Team Notes

- Tests share a **single browser session** per suite (`setUpClass` / `tearDownClass`) to avoid repeated logins and speed up execution.
- The non-functional test classes are an exception — they intentionally **do not pre-login** in `setUpClass` so that `test_01` in each class can measure/inspect the login page on a genuine unauthenticated session.
- Tests run **sequentially** in CSV order. If a test creates a user, later tests that try the same username will get a duplicate-user error — this is intentional for TC-001-034.
- To add new test cases, append a row to the relevant CSV; the Python script picks it up automatically with no code changes needed.
- Level 2 CSVs use `id`, `css`, `xpath`, etc. as the locator type string. The `loc()` helper in `test_level2.py` maps these to the correct `By.*` constant via the `BY_MAP` dictionary.
- Non-functional tests **do not** clean up quiz entries they create; run them in a test environment, not production.
- `TestAssignLevel2` overrides `setUpClass` to switch role to Teacher after logging in; all other Level 2 classes log in as admin and stay in that role.
