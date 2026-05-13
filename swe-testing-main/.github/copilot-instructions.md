# GitHub Copilot Instructions — SWE-Testing Project #3
# Group 11 · Software Testing 2025S2

## Project Overview

Data-driven automation testing of Moodle LMS (`https://ihatetesting.moodlecloud.com/`)
using Python + Selenium 4 + unittest + pytest.

This is a re-implementation of Project #2 Katalon Recorder test cases in two
escalating levels of data-driven automation, plus non-functional tests.

---

## Tech Stack & Versions

- **Language**: Python 3.9+
- **Browser automation**: Selenium 4 (`selenium>=4.0`)
- **Driver management**: `webdriver-manager` (auto-downloads ChromeDriver — no manual install)
- **Test framework**: `unittest` (test classes) + `pytest` (runner)
- **Data format**: CSV (`.csv` files, UTF-8 encoded, `csv.DictReader`)
- **Assertions**: `unittest.TestCase` assert methods (e.g. `assertEqual`, `assertIn`, `assertTrue`)

Install all dependencies:
```bash
pip3 install selenium webdriver-manager pytest
```

---

## Application Under Test

| Property | Value |
|---|---|
| Site | `https://ihatetesting.moodlecloud.com/` |
| Admin login | `phuc.nguyen0310@hcmut.edu.vn` |
| Features | TC-001 Add User · TC-002 Create Course · TC-003 Create Assignment · TC-004 Grade Assignment · TC-005 Calendar Event · TC-006 Quiz Setup |
| Test cases per TC | 17–43 rows per CSV |

---

## Repository Structure

```
swe-testing/
├── project2/
│   ├── krecorder/           # Original Katalon Recorder source files (TC-001 … TC-006)
│   ├── Project #2 description.pdf
│   └── 4_Black-box testing.pdf
│
├── level1/                  # Level 1: data from CSV, locators/URLs hardcoded in script
│   ├── test_add_user_level1.py     # TC-001
│   ├── test_course_level1.py       # TC-002
│   ├── test_assign_level1.py       # TC-003
│   ├── test_grade_level1.py        # TC-004
│   ├── test_event_level1.py        # TC-005
│   ├── test_quiz_level1.py         # TC-006
│   ├── test_data_tc001.csv … test_data_tc006.csv
│   └── run_tc001.sh                # zsh helper to run selected TC-001 cases
│
├── level2/                  # Level 2: ALL values (URLs, locators, creds, data) from CSV
│   ├── test_level2.py       # Single file — all 6 test suites
│   └── test_data_tc001_level2.csv … test_data_tc006_level2.csv
│
└── non_functional/
    └── test_non_functional.py  # Performance + Security tests for TC-006 (Quiz)
```

---

## Level 1 — Conventions

- **Purpose**: data (varying inputs + expected results) in CSV; locators and URLs hardcoded.
- **Pattern**: one `unittest.TestCase` class per TC; test methods generated dynamically.
- **CSV loading**: always use `os.path.dirname(__file__)` to build the path so tests run
  correctly from any working directory:
  ```python
  CSV_PATH = os.path.join(os.path.dirname(__file__), "test_data_tcXXX.csv")
  rows = list(csv.DictReader(open(CSV_PATH, newline="", encoding="utf-8")))
  ```
- **Dynamic test generation** (factory pattern):
  ```python
  def _make_test(row: dict):
      def test_method(self):
          ...
      test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
      return test_method

  for _row in rows:
      setattr(TestClass, f"test_{_row['test_case_id'].replace('-','_')}", _make_test(_row))
  ```
- **CSV columns** always include: `test_case_id`, `expected_result`.
- **Expected result values**: `success` or `fail` (lowercase). TC-006 uses `fail_grade`,
  `fail_time`, `fail_date`, `fail_name` for specific failure types.
- **Special sentinel**: `password = __generate__` → tick the Moodle
  "Generate password and notify user" checkbox instead of injecting a value.
- **Login**: performed once in `setUpClass`; browser session shared across all test methods.
- **Driver init**: use `webdriver.Chrome(service=Service(ChromeDriverManager().install()))`.
- **Waits**: prefer `WebDriverWait` (explicit) over `time.sleep` wherever possible.
  Do NOT mix `implicitly_wait` with `WebDriverWait` in the same driver session.
- **JS submit clicks**: use `driver.execute_script("arguments[0].click();", element)`
  to bypass sticky-footer/overlay interception.

---

## Level 2 — Conventions

- **Purpose**: everything — site URL, login suffix, locators, credentials, test data —
  read from CSV. Zero hardcoded site-specific values in the Python code.
- **All 6 test suites live in `level2/test_level2.py`** — one file, multiple classes.
- **Base class** `_BaseLevel2(unittest.TestCase)`:
  - Shared `_start_driver()`, `_login(row)`, `_dismiss_cookie_banner()`, `_recover()`.
  - `setUp()` handles dead sessions (re-spins driver + re-logs in).
  - Override `_CSV_FILE` class variable in each subclass.
- **Locator columns** follow the `<prefix>_locator_type` / `<prefix>_locator_value` convention:
  ```
  username_locator_type  = "id"
  username_locator_value = "username"
  ```
- **`loc(row, prefix)`** utility resolves a `(By.XXX, value)` tuple from those columns.
- **`BY_MAP`** maps string → `By` constant:
  ```python
  BY_MAP = {
      "id": By.ID, "name": By.NAME, "class name": By.CLASS_NAME,
      "css selector": By.CSS_SELECTOR, "xpath": By.XPATH,
      "link text": By.LINK_TEXT, "tag name": By.TAG_NAME,
  }
  ```
- **CSV columns** always include: `test_case_id`, `site_url`, `login_url_suffix`,
  `username`, `password`, `expected_result` plus feature-specific locator pairs.
- **Admin credentials** for TC-001 Level 2 are overridden in `TestCreateUserLevel2._login()`
  because the `username`/`password` columns hold new-user test data, not admin creds.

---

## Moodle-Specific Quirks — Always Apply

1. **Cookie / OneTrust banner**: dismiss on every new browser session.
   ```python
   WebDriverWait(driver, 5).until(
       EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
   ).click()
   ```
   Also inject JS to hide overlay as belt-and-braces:
   ```js
   document.querySelector('.onetrust-pc-dark-filter').style.display = 'none';
   document.getElementById('onetrust-banner-sdk').style.display = 'none';
   ```

2. **Password field** (`id_newpassword`) is `readonly`/`disabled` — must use JS:
   ```python
   driver.execute_script("""
       var i = document.getElementById('id_newpassword');
       i.removeAttribute('readonly'); i.removeAttribute('disabled'); i.style.display='';
       var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
       s.call(i, arguments[0]);
       i.dispatchEvent(new Event('input',{bubbles:true}));
       i.dispatchEvent(new Event('change',{bubbles:true}));
       i.dispatchEvent(new Event('blur',{bubbles:true}));
   """, password_value)
   ```

3. **Date fields**: always set via JS `select.value = N` + dispatch `change` event.
   Do not use `Select()` or `send_keys()` on Moodle date dropdowns.

4. **Grade / number fields** (React-controlled): use native-input-value setter + events:
   ```js
   var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
   s.call(element, String(value));
   element.dispatchEvent(new Event('input',{bubbles:true}));
   element.dispatchEvent(new Event('change',{bubbles:true}));
   ```

5. **Error detection**:
   - Validation errors: `[id^="id_error_"]` CSS selector.
   - Grade test uses `__test_marker` DOM injection to persist error state across navigations.

6. **Success detection** (per TC):
   | TC | Success indicator |
   |---|---|
   | TC-001 | `"Changes saved"` in `page_source` |
   | TC-002 | `"Announcements"` in `page_source` |
   | TC-003 | `"Announcements"` or `.activity-header` present |
   | TC-004 | `__test_marker[data-has-error="no"]` |
   | TC-005 | Dialog (`div[role='dialog']`) disappears within 8 s |
   | TC-006 | No visible `[id^="id_error_"]` after save |

7. **Role switching** (TC-003): navigate to `/course/switchrole.php?id=1&switchrole=-1&…`
   and click "Teacher" button to switch from Admin to Teacher role.

---

## Naming Conventions

| Item | Convention |
|---|---|
| Test case IDs | `TC-XXX-YYY` (feature-serial, 3-digit each) |
| Test method names | `test_TC_XXX_YYY` (dashes → underscores) |
| CSV files (L1) | `test_data_tcXXX.csv` in `level1/` |
| CSV files (L2) | `test_data_tcXXX_level2.csv` in `level2/` |
| Test classes (L1) | `Test<FeatureName>Level1` |
| Test classes (L2) | `Test<FeatureName>Level2` |

---

## Running Tests

```bash
# Level 1 — run all tests for one feature
cd level1
python3 -m pytest test_add_user_level1.py -v        # TC-001
python3 -m pytest test_course_level1.py  -v        # TC-002
python3 -m pytest test_assign_level1.py  -v        # TC-003
python3 -m pytest test_grade_level1.py   -v        # TC-004
python3 -m pytest test_event_level1.py   -v        # TC-005
python3 -m pytest test_quiz_level1.py    -v        # TC-006

# Run a single test case
python3 -m pytest test_add_user_level1.py -v -k "TC_001_005"

# Level 2 — run all
cd level2
python3 -m pytest test_level2.py -v

# Run one class
python3 -m pytest test_level2.py::TestCreateUserLevel2 -v

# Non-functional
cd non_functional
python3 -m pytest test_non_functional.py -v
```

---

## Non-Functional Tests

**Workload rule (lecturer-adjusted):** Each student must implement *at least one* non-functional
requirement (original PDF stated two; lecturer has since reduced this to one). The project PDF
also requires that the PDF report contains a dedicated section describing the testing type,
testing approach, and testing tool for each non-functional test.

Two categories currently implemented (both in `non_functional/test_non_functional.py`, targeting TC-006 Quiz Setup):

1. **Performance**: measures page-load and form-save time against SLA thresholds
   (login ≤ 5 s, quiz form load ≤ 8 s, save ≤ 6 s). Uses `time.time()`.

2. **Security**: submits XSS/injection payloads (`<script>alert('xss')</script>`,
   SQL injection strings, HTML injection) into quiz Name/Grade fields. Verifies the
   application rejects/sanitises them. Also checks that the password field is masked
   (`type="password"` attribute).

**Submission note:** Submit Python + CSV files only. Do **not** include `.krecorder` files
in the submission ZIP. Level 1 and Level 2 files must be in separate groups/directories.

---

## Copilot Guidance

- When generating new test methods, follow the `_make_test(row)` factory pattern.
- When adding a new TC to Level 2, add a new `_BaseLevel2` subclass in `test_level2.py`
  and a corresponding `test_data_tcXXX_level2.csv` in `level2/`.
- Do NOT hardcode site-specific values (URLs, locators, credentials) in Level 2 scripts.
- Always call `driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)`
  before clicking submit buttons to avoid sticky-footer interception.
- Use `time.sleep()` only when explicitly mirroring a Katalon `pause` step or waiting for
  Moodle's JS to settle after a page load. Prefer `WebDriverWait` everywhere else.
- Credentials (`phuc.nguyen0310@hcmut.edu.vn` / `Huuphuc0310@`) are for the shared
  Moodle test instance only — never commit real production credentials.
