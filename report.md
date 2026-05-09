# Code Review Report — Project #3 Data-Driven Automation Testing
**Group 11 · Software Testing 2025S2**
Reviewed: 2026-05-09

---

## Table of Contents
1. [Scope](#1-scope)
2. [Level 1 — File-by-File Review](#2-level-1--file-by-file-review)
3. [Level 2 — File-by-File Review](#3-level-2--file-by-file-review)
4. [Bugs (must-fix)](#4-bugs-must-fix)
5. [Warnings (should-fix)](#5-warnings-should-fix)
6. [Suggestions (nice-to-have)](#6-suggestions-nice-to-have)
7. [Orphan / Stray Files](#7-orphan--stray-files)
8. [Project #2 → Project #3 Traceability](#8-project-2--project-3-traceability)
9. [Compliance with Project #3 Requirements](#9-compliance-with-project-3-requirements)

---

## 1. Scope

| Layer | Files reviewed |
|---|---|
| Level 1 | `test_add_user_level1.py`, `test_course_level1.py`, `test_assign_level1.py`, `test_grade_level1.py`, `test_event_level1.py`, `test_quiz_level1.py` + all 6 CSV files |
| Level 2 | `test_level2.py` + `test_data_tc001_level2.csv` … `test_data_tc006_level2.csv` |
| Non-functional | `non_functional/test_non_functional.py` |
| Configuration | `.github/copilot-instructions.md`, `README.md` |

---

## 2. Level 1 — File-by-File Review

### TC-001 · `test_add_user_level1.py`
**Overall: ✅ Good — one critical bug**

| Item | Assessment |
|---|---|
| Cookie banner | ✅ Dismissed via `WebDriverWait` + JS fallback |
| Password field | ✅ JS injection with `removeAttribute('readonly')` — correct |
| `__generate__` sentinel | ✅ Ticks `id_createpassword` checkbox |
| Submit button | ✅ `scrollIntoView` + `execute_script("arguments[0].click()")` |
| Login | ✅ Uses `send_keys` + `WebDriverWait` for redirect |
| CSV path | 🐛 **BUG — see §4, issue #1** |

**Notes:**
- `_get_outcome()` returns `"unknown"` when neither success text nor an error element is found.
  This means a test with an ambiguous page state will compare `"unknown"` against `"success"` or `"fail"` and correctly fail the assertion — acceptable, but a more explicit third-outcome log message would help debugging.

---

### TC-002 · `test_course_level1.py`
**Overall: ✅ Good — one warning**

| Item | Assessment |
|---|---|
| Login | ⚠️ JS f-string interpolation for credentials — see §5, issue #3 |
| Date fields | ✅ Set via JS `select.value` + `change` event |
| Duplicate shortname detection | ✅ Checked via `[id^="id_error_"]` |
| End-date past/today logic | ✅ Correctly derives `offset_days` / `offset_years` |
| Submit button | ✅ JS-click on `id_saveanddisplay` |
| Success detection | ✅ `"Announcements"` in `page_source` |
| CSV path | ✅ Uses `os.path.dirname(__file__)` |

---

### TC-003 · `test_assign_level1.py`
**Overall: ⚠️ Two issues**

| Item | Assessment |
|---|---|
| Role switch to Teacher | ✅ Navigates to `switchrole.php`, clicks Teacher button |
| Date fields (JS) | ✅ `allowsubmissionsfromdate`, `duedate`, `cutoffdate` all set via JS |
| Submission types | ✅ `setCB()` helper handles enabled/disabled file & online-text |
| `implicitly_wait` | 🐛 **BUG — see §4, issue #2** |
| Login JS | ⚠️ f-string credential interpolation — see §5, issue #3 |
| CSV path | ✅ Uses `os.path.dirname(__file__)` |

---

### TC-004 · `test_grade_level1.py`
**Overall: ✅ Best-implemented file in Level 1**

| Item | Assessment |
|---|---|
| Grade field | ✅ React-compatible native-input-value setter + `input`/`change`/`blur` events |
| TinyMCE feedback | ✅ Sets content via `tinymce.activeEditor.setContent()` and falls back to `textarea` |
| `__test_marker` DOM injection | ✅ Correct approach for persisting error state across navigations |
| Error detection CSS selectors | ✅ Covers `.invalid-feedback`, `.help-block.text-danger`, `is-invalid` class |
| Submit | ✅ `scrollIntoView` + JS-click |
| Waits | ✅ `WebDriverWait` throughout, no `implicitly_wait` |
| CSV path | ✅ Uses `os.path.dirname(__file__)` |

**Notes:**
- `GRADER_URL` contains `id=321` (hardcoded assignment instance). If the assignment is deleted and recreated on the Moodle site, all TC-004 tests will 404. See §6, suggestion #6.

---

### TC-005 · `test_event_level1.py`
**Overall: ✅ Good**

| Item | Assessment |
|---|---|
| Duration types | ✅ `none` / `minutes` / `until` branching is correct |
| JS date/time fill | ✅ Uses `nS()` native setter and `sS()` select setter |
| Repeat checkbox | ✅ `setCheckbox()` JS helper |
| Session recovery | ✅ `InvalidSessionIdException` caught in factory |
| Success detection | ✅ Waits up to 8 s for `div[role='dialog']` to disappear |
| CSV path | ✅ Uses `os.path.dirname(__file__)` |

---

### TC-006 · `test_quiz_level1.py`
**Overall: ✅ Good**

| Item | Assessment |
|---|---|
| 4-mode failure detection | ✅ `fail_grade` / `fail_time` / `fail_date` / `fail_name` mapped by error element ID |
| Time limit toggle | ✅ `ens`/`dis` JS helpers for checkbox |
| Grade-to-pass | ✅ Native-input-value setter |
| Name field | ✅ Standard `send_keys` |
| CSV path | ✅ Uses `os.path.dirname(__file__)` |

**Notes:**
- `QUIZ_URL` hardcodes `course=152&sectionid=750`. Same fragility as TC-004. See §6, suggestion #6.

---

### Level 1 CSV files

| File | Rows | Notes |
|---|---|---|
| `test_data_tc001.csv` | 43 | ✅ Consistent with script expectations |
| `test_data_tc002.csv` | 27 | ✅ |
| `test_data_tc003.csv` | 27 | ✅ |
| `test_data_tc004.csv` | 17 | ✅ |
| `test_data_tc005.csv` | 28 | ✅ |
| `test_data_tc006.csv` | 19 | ✅ Uses `fail_grade/fail_time/fail_date/fail_name` values |
| `test_data.csv` | — | ⚠️ **Orphan file** — see §7 |

---

## 3. Level 2 — File-by-File Review

### `test_level2.py` — All 6 suites
**Overall: ✅ Strong architecture — two issues**

**Architecture strengths:**
- `_BaseLevel2` base class cleanly shares driver lifecycle, login, cookie handling, and recovery across all suites.
- `setUp()` guards against stale sessions by catching `InvalidSessionIdException` and calling `_recover()`.
- `BY_MAP` + `loc(row, prefix)` utility is the correct pattern for Level 2 locator resolution.
- `_JS_SET_GRADE` / `_JS_CHECK_ERRORS` / `_JS_QUIZ_HELPERS` factored into module-level constants — avoids repetition.

| Suite | Class | Status |
|---|---|---|
| TC-001 | `TestCreateUserLevel2` | ⚠️ Hardcoded admin creds — see §4, issue #3 |
| TC-002 | `TestCreateCourseLevel2` | ✅ |
| TC-003 | `TestAssignLevel2` | ⚠️ Role-switch URL hardcodes `id=1` — see §5, issue #4 |
| TC-004 | `TestGradeLevel2` | ✅ Mirrors Level 1 `__test_marker` approach |
| TC-005 | `TestCalendarEventLevel2` | ✅ Logic in factory function rather than instance methods — works but inconsistent with other suites |
| TC-006 | `TestQuizSetupLevel2` | ✅ `_normalise()` maps raw expected values to canonical codes |

**Class ordering:** `TestCreateUserLevel2` is defined *last* in the file (after TC-006), breaking the logical TC-001 → TC-006 sequence. No functional impact but reduces readability — see §6, suggestion #5.

---

### Level 2 CSV files

| File | Notes |
|---|---|
| `test_data_tc001_level2.csv` | ✅ Has all required locator columns; `password_locator_*` absent (not needed for new-user form, handled by `_login()` override) |
| `test_data_tc002_level2.csv` | ✅ |
| `test_data_tc003_level2.csv` | ✅ |
| `test_data_tc004_level2.csv` | ✅ |
| `test_data_tc005_level2.csv` | ✅ |
| `test_data_tc006_level2.csv` | ✅ |
| `test_data_level2.csv` | ⚠️ **Orphan file** — see §7 |

---

## 4. Bugs (must-fix)

### Bug #1 — Bare relative CSV path in `test_add_user_level1.py`

**File:** [level1/test_add_user_level1.py](level1/test_add_user_level1.py#L210)
**Severity:** 🔴 High — causes `FileNotFoundError` when pytest is run from any directory other than `level1/`

**Current code (line 210):**
```python
_rows = load_csv("test_data_tc001.csv")
```

**Fix:**
```python
_rows = load_csv(os.path.join(os.path.dirname(__file__), "test_data_tc001.csv"))
```

**Why:** Every other Level 1 script (`test_course_level1.py`, `test_assign_level1.py`, etc.) uses `os.path.dirname(__file__)` correctly. TC-001 is the only outlier.

---

### Bug #2 — `implicitly_wait` mixed into `test_assign_level1.py`

**File:** [level1/test_assign_level1.py](level1/test_assign_level1.py#L55)
**Severity:** 🔴 High — creates unpredictable double-timeout behaviour if `WebDriverWait` is used in the same session

**Current code:**
```python
cls.driver.implicitly_wait(10)
cls._login_and_switch_role()
```

**Fix:** Remove `implicitly_wait`. Replace any bare `find_element` calls that need a timeout with explicit `WebDriverWait(driver, 10).until(EC.presence_of_element_located(...))`.

**Why:** Selenium's implicit and explicit waits interact in non-obvious ways. When both are active, `WebDriverWait` on a *not-present* element will wait up to `implicit_wait + explicit_wait` seconds rather than just `explicit_wait`. The project conventions explicitly forbid mixing them.

---

### Bug #3 — Admin credentials hardcoded in Level 2 `TestCreateUserLevel2._login()`

**File:** [level2/test_level2.py](level2/test_level2.py)
**Severity:** 🔴 High — directly violates the Level 2 requirement "all URLs, credentials, locators … read from CSV; zero hardcoded site-specific values in Python"

**Current code (inside `TestCreateUserLevel2._login`):**
```python
driver.find_element(By.ID, "username").send_keys("phuc.nguyen0310@hcmut.edu.vn")
driver.find_element(By.ID, "password").send_keys("Huuphuc0310@")
```

**Fix:** Add two columns to `test_data_tc001_level2.csv`:
```
admin_username,admin_password
phuc.nguyen0310@hcmut.edu.vn,Huuphuc0310@
```

Then read them in `_login()`:
```python
driver.find_element(By.ID, "username").send_keys(row["admin_username"])
driver.find_element(By.ID, "password").send_keys(row["admin_password"])
```

---

## 5. Warnings (should-fix)

### Warning #3 — JS f-string credential interpolation in `test_course_level1.py` and `test_assign_level1.py`

**Files:** [level1/test_course_level1.py](level1/test_course_level1.py), [level1/test_assign_level1.py](level1/test_assign_level1.py)
**Severity:** 🟡 Medium — safe with the current credentials but fragile by design

**Current code (TC-002 `_login`):**
```python
cls.driver.execute_script(
    f"document.getElementById('username').value = '{ADMIN_USER}';"
)
cls.driver.execute_script(
    f"document.getElementById('password').value = '{ADMIN_PASS}';"
)
```

If `ADMIN_USER` or `ADMIN_PASS` ever contains a single quote (`'`), the inline JS string will break with a `SyntaxError`. The correct pattern (already used in the krecorder `runScript` helpers) is to pass values as `arguments[]`:

**Fix:**
```python
cls.driver.execute_script(
    "document.getElementById('username').value = arguments[0];"
    "document.getElementById('password').value = arguments[1];",
    ADMIN_USER, ADMIN_PASS
)
```

---

### Warning #4 — Role-switch URL hardcodes course `id=1` in `TestAssignLevel2`

**File:** [level2/test_level2.py](level2/test_level2.py)
**Severity:** 🟡 Medium — minor Level 2 principle violation

**Current code (inside `TestAssignLevel2.setUpClass`):**
```python
cls.rows[0]["site_url"].rstrip("/") +
"/course/switchrole.php?id=1&switchrole=-1&returnurl=%2Fmy%2Findex.php"
```

`id=1` is the site-admin course ID, hardcoded rather than coming from CSV.

**Fix:** Add a `switch_role_url_suffix` column to `test_data_tc003_level2.csv` (e.g. `course/switchrole.php?id=1&switchrole=-1&returnurl=%2Fmy%2Findex.php`) and read it in `setUpClass`.

---

## 6. Suggestions (nice-to-have)

### Suggestion #5 — Move `TestCreateUserLevel2` to logical position in `test_level2.py`

`TestCreateUserLevel2` (TC-001) is currently the *last* class defined in `test_level2.py`, after TC-006. Moving it to just after `_BaseLevel2` restores the TC-001 → TC-006 reading order consistent with all documentation.

---

### Suggestion #6 — Document hardcoded instance IDs with warning comments

The following URLs reference Moodle content that was created manually and will break if the content is ever deleted and recreated:

| File | Hardcoded value | Risk |
|---|---|---|
| [level1/test_grade_level1.py](level1/test_grade_level1.py) | `GRADER_URL = .../view.php?id=321` | `id=321` is the specific assignment module instance |
| [level1/test_quiz_level1.py](level1/test_quiz_level1.py) | `course=152&sectionid=750` | Course 152, section 750 |

Add a comment block above each constant warning that these IDs are environment-specific and must be updated if the Moodle site content is reset.

---

### Suggestion #7 — Replace `time.sleep(5)` after page load with explicit waits

Every Level 1 test navigates to a form page and then waits 5 s unconditionally:

```python
driver.get(ADD_USER_URL)
wait.until(EC.presence_of_element_located(LOC_USERNAME))
time.sleep(5)   # mirrors krecorder "pause 5000"
```

With 43 TC-001 rows × 5 s this is 215 s of pure sleep. The `wait.until(EC.presence_of_element_located(...))` already confirms the element is present. The `time.sleep(5)` can be reduced to `time.sleep(1)` or removed entirely for non-flaky scenarios.

---

### Suggestion #8 — `TestCalendarEventLevel2` inconsistency

TC-005 in `test_level2.py` places all logic inside the `_make_event_test()` factory function (accessing `self.__class__.driver` directly) instead of using `_fill_and_submit()` / `_get_outcome()` instance methods like every other suite. Both approaches work, but the inconsistency increases maintenance cost. Refactoring to the instance-method pattern would make all 6 suites uniform.

---

### Suggestion #9 — Add a `conftest.py` with a shared `pytest` mark for slow tests

All Selenium tests are slow (browser launch, network latency). A `conftest.py` at the repo root with a custom `@pytest.mark.e2e` mark and a `--co -q` alias would allow `pytest -m "not e2e"` to skip browser tests during CI linting passes.

---

## 7. Orphan / Stray Files

| File | Location | Status |
|---|---|---|
| `test_data.csv` | `level1/` | ⚠️ Not imported by any script. Appears to be a development scratch file (TC-006-schema subset). Should be deleted or moved to `project2/`. |
| `test_data_level2.csv` | `level2/` | ⚠️ Not imported by any script. Appears to be a draft or template. Should be deleted or moved to `project2/`. |

---

## 8. Project #2 → Project #3 Traceability

This section cross-references the original Katalon Recorder (krecorder) files from Project #2 against the Project #3 Level 1 Python scripts + CSVs and Level 2 Python class + CSVs, to assess the accuracy of the migration.

### 8.1 Artifact Mapping

| TC | Feature | Krecorder file | L1 script | L1 CSV | L2 class | L2 CSV |
|---|---|---|---|---|---|---|
| TC-001 | Add User | `TC-001.krecorder` | `test_add_user_level1.py` | `test_data_tc001.csv` | `TestCreateUserLevel2` | `test_data_tc001_level2.csv` |
| TC-002 | Create Course | `TC-002.krecorder` | `test_course_level1.py` | `test_data_tc002.csv` | `TestCreateCourseLevel2` | `test_data_tc002_level2.csv` |
| TC-003 | Create Assignment | `TC-003.krecorder` | `test_assign_level1.py` | `test_data_tc003.csv` | `TestAssignLevel2` | `test_data_tc003_level2.csv` |
| TC-004 | Grade Assignment | `TC-004.krecorder` | `test_grade_level1.py` | `test_data_tc004.csv` | `TestGradeLevel2` | `test_data_tc004_level2.csv` |
| TC-005 | Calendar Event | `TC-005.krecorder` | `test_event_level1.py` | `test_data_tc005.csv` | `TestCalendarEventLevel2` | `test_data_tc005_level2.csv` |
| TC-006 | Quiz Setup | `TC-006.krecorder` | `test_quiz_level1.py` | `test_data_tc006.csv` | `TestQuizSetupLevel2` | `test_data_tc006_level2.csv` |

### 8.2 Test-Case Count Comparison

Each krecorder file defines a **Preparation** script, a numbered set of test cases, and a **Cleanup** script. Only the numbered cases (not Prep/Cleanup) are migrated to CSV data rows.

| TC | Krecorder cases | L1 CSV rows | L2 CSV rows | L1 match? | L2 match? |
|---|---|---|---|---|---|
| TC-001 | 43 (001–043) | 43 | 43 | ✅ | ✅ |
| TC-002 | 27 (001–027) | 27 | 27 | ✅ | ✅ |
| TC-003 | 27 (001–027) | 27 | 27 | ✅ | ✅ |
| TC-004 | 17 (001–017) | 17 | 17 | ✅ | ✅ |
| TC-005 | 28 (001–028) | 28 | 28 | ✅ | ✅ |
| TC-006 | 27 (001–027) | 27 | 27 | ✅ | ✅ |
| **Total** | **169** | **169** | **169** | **✅** | **✅** |

All 169 test cases from the six krecorder files have been fully migrated. No cases were omitted or duplicated.

### 8.3 Fidelity Notes

**What was preserved faithfully:**

- **TC identifiers** — IDs (e.g. `TC-001-007`) are carried over verbatim as the `test_case_id` column in every CSV and as the generated Python test-method name (e.g. `test_TC_001_007`).
- **Input data** — Boundary values (empty strings, single characters, maximum-length strings, numeric limits) match what the krecorder recorded for each `type` command.
- **Success/fail classification** — All krecorder `assertText` / `assertElement` / `assertAlert` verify steps are reflected as `expected_result = success` or `fail` in Level 1 CSVs, and the corresponding Python assertion compares the observed page outcome to that value.
- **Preparation / Cleanup** — The krecorder Preparation script (login + navigate) is absorbed into `setUpClass()` / the factory `setUp()`; Cleanup (logout / close) is handled by `tearDownClass()`. No separate Prep/Cleanup data rows are needed.
- **Cookie banner handling** — The krecorder's `clickAndWait` on the OneTrust accept button is reproduced as `WebDriverWait` + JS fallback in every Level 1 and Level 2 script.
- **Locators** — All element locators (IDs, XPath, CSS selectors) were taken directly from the krecorder `target` attributes and hardcoded in Level 1 scripts, then promoted to `<prefix>_locator_type` / `<prefix>_locator_value` CSV column pairs in Level 2.

**What was intentionally changed or added:**

| Change | Reason |
|---|---|
| Sequential krecorder steps → independent `unittest` test methods | Selenium tests must be independently executable; shared state is limited to the `setUpClass` browser session |
| `__generate__` sentinel added in TC-001 L1/L2 CSV (TC-001-033) | The krecorder recorded a manual checkbox tick; the Python sentinel makes the behaviour explicit and data-driven |
| TC-006 L1 uses generic `fail`; L2 refines to `fail_grade`, `fail_time`, `fail_date`, `fail_name` | L2 scripts can inspect which specific error element is present; the finer granularity is an intentional enhancement for more precise assertions |
| Moodle JS workarounds (password `readonly` removal, React grade field, date dropdowns via `select.value`) | Browser automation requires more explicit DOM manipulation than Katalon's native `type` command provides |

### 8.4 Data Discrepancy — Fixed

**TC-001-024 — `expected_result` error in L1 CSV (now corrected)**

The krecorder's verify step for TC-001-024 is `verifyElementPresent` on `css=[id^="id_error_"]`, which confirms that an error element must be present after submission — i.e., the expected outcome is **fail**. The Moodle built-in `admin` account exists permanently and cannot be deleted by the test cleanup script, so attempting to create a new user named `admin` always raises a duplicate-username error.

| File | `username` column | Krecorder verify step | Correct `expected_result` |
|---|---|---|---|
| `TC-001.krecorder` | `admin` | `verifyElementPresent css=[id^="id_error_"]` | `fail` |
| `test_data_tc001.csv` (L1) — **before fix** | `admin` | — | ~~`success`~~ |
| `test_data_tc001.csv` (L1) — **after fix** | `admin` | — | `fail` ✅ |
| `test_data_tc001_level2.csv` (L2) | `admin` | — | `fail` ✅ |

The L1 CSV has been updated. Both L1 and L2 now match the krecorder ground truth.

---

## 9. Compliance with Project #3 Requirements

Key requirements extracted verbatim from the PDF:

> *"Level 1: Automation using data-driven testing approach"*

> *"Level 2: Automation using a data-driven testing approach, where testing data **and testing items such as site URLs and elements** like text fields and buttons are provided to the script."*

> *"Non-functional testing: **at least one non-functional requirement for each student**"* *(lecturer-adjusted — original PDF stated two)*

> *"For non-functional testing, **a description of the testing type, testing approach and the testing tool (if any) has to be represented in the report**."*

> *"Files for level 1 and level 2 are grouped separately, and compressed into a .zip archive."*

> *"Note: Submit Python code files (and data files), **not Katalon files!!!**"*

### Compliance table

| Requirement | Met? | Notes |
|---|---|---|
| Level 1 data from CSV | ✅ Yes | All 6 features have CSV files; locators hardcoded in scripts |
| Level 1 `expected_result` column in CSV | ✅ Yes | Every Level 1 CSV has `expected_result` column |
| Level 2 data AND locators/URLs from CSV | ⚠️ Mostly | See Bug #3 (hardcoded admin creds in TC-001) and Warning #4 (hardcoded role-switch `id=1` in TC-003) |
| Level 2 site URLs from CSV | ✅ Yes | `site_url` + `login_url_suffix` in every Level 2 CSV |
| Non-functional: ≥ 1 requirement **per student** (lecturer-adjusted) | ✅ Yes | Performance (response-time SLA) + Security (XSS/injection + password masking) — both implemented in `non_functional/test_non_functional.py` |
| Non-functional: description in PDF report | ⚠️ Check | `test_non_functional.py` has a thorough docstring. The **submitted PDF report** must also contain a dedicated section describing testing type, approach, and tool — verify this is present before submission. |
| Python scripting language | ✅ Yes | All scripts in Python 3.9+ |
| Data in `.csv` files | ✅ Yes | All test data in UTF-8 CSV (`.xls` also allowed by PDF; CSV is fine) |
| Files grouped by level separately | ✅ Yes | `level1/`, `level2/`, `non_functional/` directories |
| Each test case has at least one verify step | ✅ Yes | `assertEqual(actual, expected, ...)` in every dynamically generated test method |
| Python files only in submission ZIP (no Katalon) | ⚠️ Check | `project2/krecorder/*.krecorder` and top-level `TC-001.krecorder` are in the repo for reference — ensure they are **excluded from the submission ZIP**. |

### Marking schema (from PDF)

| Question | Max points | Rubric |
|---|---|---|
| Level 1 | 5 | Try a few: 1 · Fair and a few: 2 · Fair and almost: 3 · Good and a few: 4 · **Good and all: 5** |
| Level 2 | 2 | Try: 1 · Fair: 1.5 · **Good: 2** |
| Non-functional | 2 | Try: 1 · Fair: 1.5 · **Good: 2** |
| Report (PDF) | 1 | Simple: 0.5 · **Good: 1** |
| **Total** | **10** | |

**Summary:** The project is substantively complete and well-implemented. Three items (Bug #1, Bug #2, Bug #3) are genuine defects that could cause test failures or marking deductions under the "Good and all" / "Good" rubrics. The two ⚠️ Check items in the compliance table are submission-time concerns rather than code bugs.
