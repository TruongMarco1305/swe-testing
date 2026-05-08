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
| **Features covered** | TC-001 Admin Adds a New User (43 cases) · TC-006 Teacher Sets Up a Quiz (27 cases) |

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
├── TC-001.krecorder          # Original Katalon Recorder file (TC-001 source)
├── Group_11.xlsx             # Original test case specification
├── Group_11.pdf
│
├── level1/
│   ├── test_data.csv              # Test data for TC-006 (27 rows)
│   ├── test_quiz_level1.py        # TC-006  Level 1 test script
│   ├── test_data_tc001.csv        # Test data for TC-001 (43 rows)
│   ├── test_add_user_level1.py    # TC-001  Level 1 test script
│   └── run_tc001.sh               # Helper: run individual TC-001 cases
│
├── level2/
│   ├── test_data_level2.csv       # TC-006 data + ALL locators in CSV (27 rows)
│   └── test_quiz_level2.py        # TC-006  Level 2 test script
│
└── non_functional/
    └── test_non_functional.py     # Performance + Security tests
```

---

## Test Suites

### Level 1 — Data from CSV, hardcoded locators

Varying input values are read from a CSV file. Element locators are constants inside the Python script.

#### TC-001 — Admin Adds a New User (43 test cases)

| File | Purpose |
|---|---|
| `level1/test_data_tc001.csv` | 43 rows — username, password, firstname, lastname, email, expected_result |
| `level1/test_add_user_level1.py` | Reads the CSV and generates one `unittest` test method per row |

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
| 032 | Normal valid re-run → **success** |
| 033 | "Generate password" checkbox path → **success** |
| 034 | Duplicate username → **fail** |
| 035–043 | Additional password & email edge cases |

**Special password handling:**  
Moodle's password field has a `readonly` attribute. The script bypasses it with JavaScript (mirroring the original Katalon Recorder `runScript` step):
```python
driver.execute_script("""
  var i = document.getElementById('id_newpassword');
  i.removeAttribute('readonly');
  ...
  i.dispatchEvent(new Event('input', {bubbles:true}));
""", password_value)
```

Use `__generate__` as the password value in the CSV to tick the "Generate password and notify user" checkbox instead.

---

#### TC-006 — Teacher Sets Up a Quiz (27 test cases)

| File | Purpose |
|---|---|
| `level1/test_data.csv` | 27 rows — quiz_name, grade_to_pass, time_limit, close_date, expected_result |
| `level1/test_quiz_level1.py` | Reads the CSV and generates one test per row |

**What is tested:** grade boundaries (0–10), time limit boundaries, close date boundaries, and empty quiz name validation.

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

| File | `level non_functional/test_non_functional.py` |
|---|---|
| **Performance tests** | Page load time ≤ 5 s · Quiz form load ≤ 8 s · Save response ≤ 6 s |
| **Security tests** | Password field masked · XSS payload rejected · HTTPS enforced · No credentials in URL |

---

## Running the Tests

All commands should be run from **inside the relevant folder**.

### Run all TC-001 Level 1 tests
```bash
cd level1
python3 -m pytest test_add_user_level1.py -v
```

### Run all TC-006 Level 1 tests
```bash
cd level1
python3 -m pytest test_quiz_level1.py -v
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
| Login button click fails | OneTrust cookie banner overlays the button | `execute_script("arguments[0].click()", btn)` — JS click bypasses overlay |
| Edit mode toggle not found | Moodle 4.x changed the input name from `setediting` → `setmode` | Use `input[name='setmode']`, then click its `<label>` via JS |
| "Add activity" button invisible | Moodle 4.x hides it until hover | `ActionChains.move_to_element(section).perform()` before clicking |
| Submit button intercepted | Sticky footer or banner sits on top of button when it is near the bottom | `scrollIntoView({block:'center'})` + JS click |
| Password field `readonly` | Moodle sets `readonly` on `id_newpassword` to force its own generator | Remove attribute + set value + dispatch `input`/`change`/`blur` events via JS |

---

## Team Notes

- Tests share a **single browser session** per suite (`setUpClass` / `tearDownClass`) to avoid repeated logins and speed up execution.
- Tests run **sequentially** in CSV order. If a test creates a user, later tests that try the same username will get a duplicate-user error — this is intentional for TC-001-034.
- To add new test cases, append a row to the relevant CSV; the Python script picks it up automatically with no code changes needed.
- The `level2` CSV uses `css selector` as the locator type string for CSS selectors. The `BY_MAP` in `test_quiz_level2.py` maps this to `By.CSS_SELECTOR`.
- Non-functional tests **do not** clean up quiz entries they create; run them in a test environment, not production.
