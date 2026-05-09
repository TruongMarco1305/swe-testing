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
6. [Running the Tests](#running-the-tests)
7. [Debugging a Single Test Case](#debugging-a-single-test-case)
8. [Known Moodle UI Quirks](#known-moodle-ui-quirks)
9. [Team Notes](#team-notes)

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

---

## Setup

```bash
# Clone the repo
git clone https://github.com/TruongMarco1305/swe-testing.git
cd swe-testing

# Install all required packages
pip3 install selenium webdriver-manager pandas openpyxl pytest
```

`webdriver-manager` automatically downloads the matching ChromeDriver — no manual driver installation needed.

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
│   ├── test_data_level2.csv       # TC-006 data + ALL locators in CSV (27 rows)
│   └── test_quiz_level2.py        # TC-006 Level 2 test script
│
└── non_functional/
    └── test_non_functional.py     # Performance + Security tests
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

Everything — site URL, credentials, locator types, locator values, and test data — is read from a single CSV. The Python script contains **no hardcoded selectors**.

| File | Purpose |
|---|---|
| `level2/test_data_level2.csv` | 27 rows × 30 columns (TC-006 data + all locators) |
| `level2/test_quiz_level2.py` | Resolves locator types at runtime via a `BY_MAP` dictionary |

**CSV columns include:** `site_url`, `login_url_suffix`, `username_locator_type`, `username_locator_value`, `password_locator_type` … and so on for every element touched in the test flow.

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

### Run all TC-006 Level 2 tests
```bash
cd level2
python3 -m pytest test_quiz_level2.py -v
```

### Run non-functional tests
```bash
cd non_functional
python3 -m pytest test_non_functional.py -v
```

### Run everything at once (from repo root)
```bash
python3 -m pytest level1/ level2/ non_functional/ -v
```

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
- The `level2` CSV uses `css selector` as the locator type string for CSS selectors. The `BY_MAP` in `test_quiz_level2.py` maps this to `By.CSS_SELECTOR`.
- Non-functional tests **do not** clean up quiz entries they create; run them in a test environment, not production.
