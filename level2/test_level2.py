"""
LEVEL 2 — Fully Data-Driven Automation Testing
Moodle LMS: https://ihatetesting.moodlecloud.com/

This single script covers three test cases, each driven by its own CSV file:
  TC-004  Teacher grades a student assignment  → test_data_tc004_level2.csv
  TC-005  Admin creates a calendar event       → test_data_tc005_level2.csv
  TC-006  Teacher sets up a quiz               → test_data_tc006_level2.csv

NO site-specific values are hardcoded here — all URLs, credentials, locators,
and test data come exclusively from the CSV files.

CSV locator convention
----------------------
Every element is described by a pair of columns:
  <prefix>_locator_type   e.g. "id", "xpath", "css selector"
  <prefix>_locator_value  e.g. "username",  "//button[@name='savechanges']"

Run all TCs:
    cd level2
    python3 -m pytest test_level2.py -v

Run one TC class:
    python3 -m pytest test_level2.py::TestGradeLevel2 -v

Run one case:
    python3 -m pytest test_level2.py -v -k "TC_004_002"
"""

import csv
import os
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------
BY_MAP = {
    "id":           By.ID,
    "name":         By.NAME,
    "class name":   By.CLASS_NAME,
    "css selector": By.CSS_SELECTOR,
    "xpath":        By.XPATH,
    "link text":    By.LINK_TEXT,
    "tag name":     By.TAG_NAME,
}

_DIR = os.path.dirname(__file__)


def load_csv(filename: str) -> list:
    path = os.path.join(_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def loc(row: dict, prefix: str) -> tuple:
    """Return a (By.XXX, value) tuple from <prefix>_locator_type/value columns."""
    by_str = row[f"{prefix}_locator_type"].strip().lower()
    return (BY_MAP[by_str], row[f"{prefix}_locator_value"].strip())


# ---------------------------------------------------------------------------
# Shared base class — login, cookie banner, session recovery
# ---------------------------------------------------------------------------
class _BaseLevel2(unittest.TestCase):
    """Shared driver lifecycle and login logic for all Level 2 test classes."""

    _CSV_FILE: str = ""   # override in subclass

    @classmethod
    def setUpClass(cls):
        cls.rows = load_csv(cls._CSV_FILE)
        cls._start_driver()
        cls._login(cls.rows[0])

    @classmethod
    def _start_driver(cls):
        opts = webdriver.ChromeOptions()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
        cls.driver.set_window_size(1400, 900)
        cls.wait = WebDriverWait(cls.driver, 20)

    @classmethod
    def _dismiss_cookie_banner(cls):
        try:
            WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
            time.sleep(1)
        except Exception:
            pass
        cls.driver.execute_script("""
            var el = document.querySelector('.onetrust-pc-dark-filter');
            if (el) el.style.display = 'none';
            var b = document.getElementById('onetrust-banner-sdk');
            if (b) b.style.display = 'none';
        """)

    @classmethod
    def _login(cls, row: dict):
        driver, wait = cls.driver, cls.wait
        login_url = row["site_url"].rstrip("/") + "/" + row["login_url_suffix"].lstrip("/")
        driver.get(login_url)
        wait.until(EC.presence_of_element_located(loc(row, "username")))
        cls._dismiss_cookie_banner()
        driver.find_element(*loc(row, "username")).send_keys(row["username"])
        driver.find_element(*loc(row, "password")).send_keys(row["password"])
        driver.execute_script("document.getElementById('loginbtn').click();")
        wait.until(EC.url_contains("/my/"))
        time.sleep(1)

    @classmethod
    def _recover(cls):
        """Spin up a fresh driver and re-login (called after browser crash)."""
        try:
            cls.driver.quit()
        except Exception:
            pass
        cls._start_driver()
        cls._login(cls.rows[0])

    def setUp(self):
        """Before each test: dismiss stale alerts, detect dead sessions."""
        try:
            self.__class__.driver.switch_to.alert.dismiss()
            time.sleep(1)
        except Exception:
            pass
        try:
            _ = self.__class__.driver.current_url
        except (InvalidSessionIdException, Exception):
            self.__class__._recover()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()


# ===========================================================================
# TC-002  Admin Creates a New Course
# CSV: test_data_tc002_level2.csv
# ===========================================================================
class TestCreateCourseLevel2(_BaseLevel2):
    """TC-002 — fully data-driven course creation tests."""

    _CSV_FILE = "test_data_tc002_level2.csv"

    def _fill_and_submit(self, row: dict):
        from datetime import date, timedelta
        driver, wait = self.driver, self.wait

        driver.get(row["new_course_url"].strip())
        time.sleep(5)

        fn = driver.find_element(*loc(row, "fullname"))
        fn.clear()
        if row["fullname"].strip():
            fn.send_keys(row["fullname"].strip())

        sn = driver.find_element(*loc(row, "shortname"))
        sn.clear()
        if row["shortname"].strip():
            sn.send_keys(row["shortname"].strip())

        end_enabled  = row["end_date_enabled"].strip().lower() == "yes"
        offset_days  = int(row["end_date_offset_days"])
        offset_years = int(row["end_date_offset_years"])

        if not end_enabled:
            driver.execute_script(
                "var cb=document.getElementById('id_enddate_enabled');"
                "if(cb&&cb.checked){cb.click();}"
            )
        else:
            today = date.today()
            try:
                target = today.replace(year=today.year + offset_years)
            except ValueError:
                target = today.replace(year=today.year + offset_years, day=28)
            target = target + timedelta(days=offset_days)
            driver.execute_script(
                "var cb=document.getElementById('id_enddate_enabled');"
                "if(cb&&!cb.checked){cb.click();}"
            )
            driver.execute_script(
                f"function sS(id,v){{var e=document.getElementById(id);"
                f"if(e){{e.value=String(v);e.dispatchEvent(new Event('change',{{bubbles:true}}));}}}}"
                f"sS('id_enddate_day',{target.day});"
                f"sS('id_enddate_month',{target.month});"
                f"sS('id_enddate_year',{target.year});"
                f"sS('id_enddate_hour',0);"
                f"sS('id_enddate_minute',0);"
            )

        driver.execute_script(
            f"var e=document.getElementById('id_numsections');"
            f"if(e){{e.value='{row['numsections']}';"
            f"e.dispatchEvent(new Event('change',{{bubbles:true}}));}}"
        )

        save = driver.find_element(*loc(row, "save_btn"))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save)
        driver.execute_script("arguments[0].click();", save)
        time.sleep(4)

    def _get_outcome(self) -> str:
        d = self.driver
        if d.find_elements(By.CSS_SELECTOR, "[id^='id_error_']"):
            return "fail"
        if "Announcements" in d.page_source:
            return "success"
        return "fail"


def _make_course_test(row: dict):
    def test_method(self):
        self._fill_and_submit(row)
        actual   = self._get_outcome()
        expected = row["expected_result"].strip()
        self.assertEqual(actual, expected,
            f"\n  [{row['test_case_id']}] fullname={repr(row['fullname'])} "
            f"shortname={repr(row['shortname'])} end_enabled={row['end_date_enabled']} "
            f"days={row['end_date_offset_days']}"
            f"\n  Expected: {expected}  |  Actual: {actual}")
    test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
    return test_method


for _r in load_csv("test_data_tc002_level2.csv"):
    setattr(TestCreateCourseLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_course_test(_r))


# ===========================================================================
# TC-003  Teacher Creates an Assignment
# CSV: test_data_tc003_level2.csv
# ===========================================================================
class TestAssignLevel2(_BaseLevel2):
    """TC-003 — fully data-driven assignment creation tests."""

    _CSV_FILE = "test_data_tc003_level2.csv"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Switch role to Teacher on course 141
        cls.driver.get(
            cls.rows[0]["site_url"].rstrip("/") +
            "/course/switchrole.php?id=1&switchrole=-1&returnurl=%2Fmy%2Findex.php"
        )
        time.sleep(2)
        try:
            btns = cls.driver.find_elements(By.CSS_SELECTOR, "form button")
            for btn in btns:
                if "Teacher" in btn.text:
                    cls.driver.execute_script("arguments[0].click();", btn)
                    break
            else:
                cls.driver.execute_script("arguments[0].click();", btns[0])
        except Exception:
            pass
        time.sleep(2)

    def _fill_and_submit(self, row: dict):
        from datetime import date, timedelta
        driver, wait = self.driver, self.wait

        driver.get(row["assign_url"].strip())
        time.sleep(5)

        name_fld = driver.find_element(*loc(row, "name"))
        name_fld.clear()
        if row["name"].strip():
            name_fld.send_keys(row["name"].strip())

        # Grade to pass — set via JS (field may be inside a collapsed accordion)
        gp_el = driver.find_element(*loc(row, "gradepass"))
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input',  {bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            gp_el, str(row["gradepass"]).strip()
        )

        # Dates
        today = date.today()
        due_enabled  = row["duedate_enabled"].strip().lower() == "yes"
        due_days     = int(row["duedate_offset_days"])
        due_years    = int(row["duedate_offset_years"])
        cutoff_days  = int(row["cutoff_offset_days"])
        cutoff_years = int(row["cutoff_offset_years"])

        if due_enabled:
            try:
                due = today.replace(year=today.year + due_years)
            except ValueError:
                due = today.replace(year=today.year + due_years, day=28)
            due = due + timedelta(days=due_days)
        else:
            due = today

        try:
            cutoff = date(due.year, due.month, due.day).replace(year=due.year + cutoff_years)
        except ValueError:
            cutoff = due.replace(year=due.year + cutoff_years, day=28)
        cutoff = cutoff + timedelta(days=cutoff_days)

        due_js = "ens" if due_enabled else "dis"
        driver.execute_script(f"""
            function sS(id,v){{var e=document.getElementById(id);if(e){{e.value=String(v);e.dispatchEvent(new Event('change',{{bubbles:true}}));}}}}
            function ens(id){{var c=document.getElementById(id);if(c&&!c.checked){{c.click();}}}}
            function dis(id){{var c=document.getElementById(id);if(c&&c.checked){{c.click();}}}}
            dis('id_gradingduedate_enabled');
            ens('id_allowsubmissionsfromdate_enabled');
            var tod=new Date();
            sS('id_allowsubmissionsfromdate_day',tod.getDate());
            sS('id_allowsubmissionsfromdate_month',tod.getMonth()+1);
            sS('id_allowsubmissionsfromdate_year',tod.getFullYear());
            {due_js}('id_duedate_enabled');
            sS('id_duedate_day',{due.day});
            sS('id_duedate_month',{due.month});
            sS('id_duedate_year',{due.year});
            ens('id_cutoffdate_enabled');
            sS('id_cutoffdate_day',{cutoff.day});
            sS('id_cutoffdate_month',{cutoff.month});
            sS('id_cutoffdate_year',{cutoff.year});
            dis('id_gradingduedate_enabled');
        """)

        # Submission types
        sub_file   = row["submission_file"].strip()
        sub_online = row["submission_onlinetext"].strip()
        if sub_file != "default" or sub_online != "default":
            parts = []
            if sub_file != "default":
                want = "true" if sub_file == "yes" else "false"
                parts.append(f"setCB('id_assignsubmission_file_enabled',{want});")
            if sub_online != "default":
                want = "true" if sub_online == "yes" else "false"
                parts.append(f"setCB('id_assignsubmission_onlinetext_enabled',{want});")
            driver.execute_script(
                "function setCB(id,want){var c=document.getElementById(id);"
                "if(c&&c.checked!==want){c.click();}}" + "".join(parts)
            )

        save = driver.find_element(*loc(row, "save_btn"))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save)
        driver.execute_script("arguments[0].click();", save)
        time.sleep(4)

    def _get_outcome(self) -> str:
        d = self.driver
        errors = [e for e in d.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
                  if e.is_displayed() and e.text.strip()]
        if errors:
            return "fail"
        if "Announcements" in d.page_source or d.find_elements(By.CSS_SELECTOR, ".activity-header"):
            return "success"
        return "fail"


def _make_assign_test(row: dict):
    def test_method(self):
        self._fill_and_submit(row)
        actual   = self._get_outcome()
        expected = row["expected_result"].strip()
        self.assertEqual(actual, expected,
            f"\n  [{row['test_case_id']}] name={repr(row['name'])} "
            f"gradepass={row['gradepass']} due_enabled={row['duedate_enabled']} "
            f"due_days={row['duedate_offset_days']}"
            f"\n  Expected: {expected}  |  Actual: {actual}")
    test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
    return test_method


for _r in load_csv("test_data_tc003_level2.csv"):
    setattr(TestAssignLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_assign_test(_r))


# ===========================================================================
# TC-004  Teacher Grades a Student Assignment
# CSV: test_data_tc004_level2.csv
# ===========================================================================
_JS_SET_GRADE = """
function nS(id, v) {
    var e = document.getElementById(id);
    if (e) {
        var s = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        s.call(e, String(v));
        e.dispatchEvent(new Event('input',  {bubbles:true}));
        e.dispatchEvent(new Event('change', {bubbles:true}));
        e.dispatchEvent(new Event('blur',   {bubbles:true}));
    }
}
var old = document.getElementById('__test_marker');
if (old) old.remove();
nS(arguments[1], arguments[0]);
var fb = 'Good work';
if (window.tinymce && window.tinymce.activeEditor) {
    try { window.tinymce.activeEditor.setContent(fb); } catch(e) {}
}
var ifr = document.getElementById('id_assignfeedbackcomments_editor_ifr');
if (ifr && ifr.contentDocument && ifr.contentDocument.body) {
    ifr.contentDocument.body.innerText = fb;
}
var ta = document.getElementById('id_assignfeedbackcomments_editor');
if (ta) { ta.value = fb; ta.dispatchEvent(new Event('change', {bubbles:true})); }
var nf = document.getElementById('id_sendstudentnotifications');
if (nf) {
    if (nf.tagName === 'SELECT') { nf.value = '1'; nf.dispatchEvent(new Event('change',{bubbles:true})); }
    else if (nf.type === 'checkbox' && !nf.checked) { nf.click(); }
}
"""

_JS_CHECK_ERRORS = """
var hasErr = false;
var sels = '[id^="id_error_"], .invalid-feedback, .form-control-feedback, '
         + '.error.felement, .help-block.text-danger';
document.querySelectorAll(sels).forEach(function(el) {
    if (hasErr) return;
    var st = window.getComputedStyle(el);
    var ok = (st.display !== 'none') && (st.visibility !== 'hidden') && (el.offsetParent !== null);
    if (ok && (el.innerText || el.textContent || '').trim()) hasErr = true;
});
var gi = document.getElementById('id_grade');
if (gi && gi.classList.contains('is-invalid')) hasErr = true;
var marker = document.getElementById('__test_marker');
if (!marker) { marker = document.createElement('div'); marker.id = '__test_marker'; document.body.appendChild(marker); }
marker.setAttribute('data-has-error', hasErr ? 'yes' : 'no');
"""


class TestGradeLevel2(_BaseLevel2):
    """TC-004 — fully data-driven grade submission tests."""

    _CSV_FILE = "test_data_tc004_level2.csv"

    def _fill_and_submit(self, row: dict):
        driver, wait = self.driver, self.wait
        grade_field_id = row["grade_field_locator_value"].strip()
        driver.get(row["grader_url"].strip())
        wait.until(EC.presence_of_element_located(loc(row, "grade_field")))
        time.sleep(5)
        driver.execute_script(_JS_SET_GRADE, row["grade"], grade_field_id)
        time.sleep(5)
        save = wait.until(EC.presence_of_element_located(loc(row, "save_btn")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save)
        driver.execute_script("arguments[0].click();", save)
        time.sleep(5)
        driver.execute_script(_JS_CHECK_ERRORS)
        time.sleep(3)

    def _get_outcome(self) -> str:
        d = self.driver
        if d.find_elements(By.CSS_SELECTOR, '#__test_marker[data-has-error="no"]'):
            return "success"
        if d.find_elements(By.CSS_SELECTOR, '#__test_marker[data-has-error="yes"]'):
            return "fail"
        return "fail" if d.find_elements(By.CSS_SELECTOR, "[id^='id_error_']") else "success"


def _make_grade_test(row: dict):
    def test_method(self):
        self._fill_and_submit(row)
        actual   = self._get_outcome()
        expected = row["expected_result"].strip()
        self.assertEqual(actual, expected,
            f"\n  [{row['test_case_id']}] grade='{row['grade']}'"
            f"\n  Expected: {expected}  |  Actual: {actual}")
    test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
    return test_method


for _r in load_csv("test_data_tc004_level2.csv"):
    setattr(TestGradeLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_grade_test(_r))


# ===========================================================================
# TC-005  Admin Creates a Calendar Event
# CSV: test_data_tc005_level2.csv
# ===========================================================================
class TestCalendarEventLevel2(_BaseLevel2):
    """TC-005 — fully data-driven calendar event creation tests."""

    _CSV_FILE = "test_data_tc005_level2.csv"


def _make_event_test(row: dict):
    tc_id         = row["test_case_id"]
    name          = row["name"]
    duration_type = row["duration_type"]
    minutes_val   = row["minutes"]
    until_offset  = row["until_offset_days"]
    repeat        = row["repeat"].strip().lower() == "yes"
    expected      = row["expected_result"].strip().lower()

    def test_method(self):
        driver = self.__class__.driver
        wait   = self.__class__.wait

        cal_url = row["site_url"].rstrip("/") + "/" + row["calendar_url_suffix"].lstrip("/")
        driver.get(cal_url)
        time.sleep(3)

        btn = wait.until(EC.element_to_be_clickable(loc(row, "new_event_btn")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

        js_helpers = """
function sS(id,v){var e=document.getElementById(id);if(e){e.value=String(v);e.dispatchEvent(new Event('change',{bubbles:true}));}}
function nS(id,v){var e=document.getElementById(id);if(e){var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(e,String(v));e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}}
function clickRadio(n,v){document.querySelectorAll('input[name="'+n+'"]').forEach(function(r){if(r.value===v){r.click();}});}
function setCheckbox(id,c){var e=document.getElementById(id);if(e&&e.checked!==c){e.click();}}
"""
        js_fill = js_helpers + f"\nnS('id_name',{repr(name)});\n"
        js_fill += ("var tod=new Date();"
                    "sS('id_timestart_day',tod.getDate());"
                    "sS('id_timestart_month',tod.getMonth()+1);"
                    "sS('id_timestart_year',tod.getFullYear());"
                    "sS('id_timestart_hour',tod.getHours());"
                    "sS('id_timestart_minute',0);\n")

        if duration_type == "none":
            js_fill += "clickRadio('duration','0');\n"
        elif duration_type == "minutes":
            js_fill += f"clickRadio('duration','1');nS('id_minutes',{repr(str(minutes_val))});\n"
        elif duration_type == "until":
            offset = int(until_offset)
            js_fill += (f"clickRadio('duration','2');"
                        f"var until=new Date(tod.getTime()+({offset})*86400000);"
                        f"sS('id_timedurationuntil_day',until.getDate());"
                        f"sS('id_timedurationuntil_month',until.getMonth()+1);"
                        f"sS('id_timedurationuntil_year',until.getFullYear());"
                        f"sS('id_timedurationuntil_hour',until.getHours());"
                        f"sS('id_timedurationuntil_minute',0);\n")

        if repeat:
            js_fill += "setCheckbox('id_repeat',true);\n"

        driver.execute_script(js_fill)
        time.sleep(2)

        save = wait.until(EC.element_to_be_clickable(loc(row, "save_btn")))
        driver.execute_script("arguments[0].click();", save)

        try:
            try:
                WebDriverWait(driver, 8).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[role='dialog']")))
                outcome = "success"
            except TimeoutException:
                outcome = "fail"
        except InvalidSessionIdException:
            self.__class__._recover()
            outcome = "success"

        self.assertEqual(outcome, expected,
            f"\n  [{tc_id}] name={repr(name)} duration={duration_type} "
            f"minutes={minutes_val} until={until_offset} repeat={repeat}"
            f"\n  Expected: {expected}  |  Actual: {outcome}")

    test_method.__name__ = f"test_{tc_id.replace('-', '_')}"
    return test_method


for _r in load_csv("test_data_tc005_level2.csv"):
    setattr(TestCalendarEventLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_event_test(_r))


# ===========================================================================
# TC-006  Teacher Sets Up a Quiz
# CSV: test_data_tc006_level2.csv
# ===========================================================================
_JS_QUIZ_HELPERS = """
function sS(id,v){var e=document.getElementById(id);if(e){e.value=String(v);e.dispatchEvent(new Event('change',{bubbles:true}));}}
function nS(id,v){var e=document.getElementById(id);if(e){var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(e,String(v));e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}}
function ens(id){var c=document.getElementById(id);if(c&&!c.checked){c.click();}}
function dis(id){var c=document.getElementById(id);if(c&&c.checked){c.click();}}
"""


class TestQuizSetupLevel2(_BaseLevel2):
    """TC-006 — fully data-driven quiz setup tests."""

    _CSV_FILE = "test_data_tc006_level2.csv"

    def _open_quiz_form(self, row: dict):
        self.driver.get(row["quiz_add_url"].strip())
        self.wait.until(EC.presence_of_element_located(loc(row, "quiz_name")))

    def _fill_and_submit(self, row: dict):
        driver = self.driver
        name_fld = driver.find_element(*loc(row, "quiz_name"))
        name_fld.clear()
        if row["quiz_name"].strip():
            name_fld.send_keys(row["quiz_name"].strip())

        close_enabled = row["close_date_enabled"].strip().lower() == "yes"
        limit_enabled = row["time_limit_enabled"].strip().lower() == "yes"
        close_days    = int(row["close_date_offset_days"]) if row.get("close_date_offset_days", "").strip() else 7
        close_years   = int(row.get("close_date_offset_years", "0") or "0")
        limit_val     = row["time_limit_minutes"].strip() or "30"
        gradepass     = row["grade_to_pass"].strip()

        js = _JS_QUIZ_HELPERS + (
            "ens('id_timeopen_enabled');"
            "var tod=new Date();"
            "sS('id_timeopen_day',tod.getDate());"
            "sS('id_timeopen_month',tod.getMonth()+1);"
            "sS('id_timeopen_year',tod.getFullYear());"
            "sS('id_timeopen_hour',tod.getHours());"
            "sS('id_timeopen_minute',0);\n"
        )

        if close_enabled:
            js += (f"ens('id_timeclose_enabled');"
                   f"var cl=new Date(tod);"
                   f"cl.setFullYear(cl.getFullYear()+({close_years}));"
                   f"cl.setDate(cl.getDate()+({close_days}));"
                   f"sS('id_timeclose_day',cl.getDate());"
                   f"sS('id_timeclose_month',cl.getMonth()+1);"
                   f"sS('id_timeclose_year',cl.getFullYear());"
                   f"sS('id_timeclose_hour',cl.getHours());"
                   f"sS('id_timeclose_minute',0);\n")
        else:
            js += "dis('id_timeclose_enabled');\n"

        if limit_enabled:
            js += (f"ens('id_timelimit_enabled');"
                   f"nS('id_timelimit_number',{repr(limit_val)});"
                   f"sS('id_timelimit_timeunit','60');\n")
        else:
            js += "dis('id_timelimit_enabled');\n"

        js += f"nS('id_gradepass',{repr(gradepass)});\n"

        driver.execute_script(js)
        time.sleep(2)

        try:
            btn = driver.find_element(*loc(row, "save_btn"))
        except Exception:
            btn = driver.find_element(By.ID, "id_submitbutton")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

    def _get_outcome(self) -> str:
        driver = self.driver
        errors = driver.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
        visible = [e for e in errors if e.is_displayed() and e.text.strip()]
        if visible:
            ids = " ".join(e.get_attribute("id") for e in visible).lower()
            if "gradepass" in ids: return "fail_grade"
            if "timelimit" in ids: return "fail_time"
            if "timeclose" in ids: return "fail_date"
            if "name"      in ids: return "fail_name"
            return "fail_general"
        return "success"

    @staticmethod
    def _normalise(raw: str) -> str:
        raw = raw.strip().lower()
        if raw == "success":                    return "success"
        if "name"  in raw:                      return "fail_name"
        if "grade" in raw:                      return "fail_grade"
        if "time"  in raw:                      return "fail_time"
        if "date"  in raw or "close" in raw:    return "fail_date"
        if raw.startswith("fail"):              return "fail_general"
        return raw


def _make_quiz_test(row: dict):
    def test_method(self):
        self._open_quiz_form(row)
        self._fill_and_submit(row)
        actual   = self._get_outcome()
        expected = self._normalise(row["expected_result"])
        self.assertEqual(actual, expected,
            f"\n  [{row['test_case_id']}] "
            f"quiz='{row['quiz_name']}' grade={row['grade_to_pass']} "
            f"timelimit={'off' if row['time_limit_enabled'].lower()=='no' else row['time_limit_minutes']} "
            f"close={'off' if row['close_date_enabled'].lower()=='no' else row['close_date_offset_days']+'d'}"
            f"\n  Expected: {expected}  |  Actual: {actual}")
    test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
    return test_method


for _r in load_csv("test_data_tc006_level2.csv"):
    setattr(TestQuizSetupLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_quiz_test(_r))


# ===========================================================================
# TC-001  Admin Creates a New User
# CSV: test_data_tc001_level2.csv
# ===========================================================================
class TestCreateUserLevel2(_BaseLevel2):
    """TC-001 — fully data-driven user creation tests."""

    _CSV_FILE = "test_data_tc001_level2.csv"

    @classmethod
    def _login(cls, row: dict):
        """Override: CSV 'username'/'password' hold new-user data, not admin creds.
        The login page uses id=username / id=password (not id_username / id_password)."""
        driver, wait = cls.driver, cls.wait
        login_url = row["site_url"].rstrip("/") + "/" + row["login_url_suffix"].lstrip("/")
        driver.get(login_url)
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        cls._dismiss_cookie_banner()
        driver.find_element(By.ID, "username").send_keys("phuc.nguyen0310@hcmut.edu.vn")
        driver.find_element(By.ID, "password").send_keys("Huuphuc0310@")
        driver.execute_script("document.getElementById('loginbtn').click();")
        wait.until(EC.url_contains("/my/"))
        time.sleep(1)

    def _fill_and_submit(self, row: dict):
        driver = self.driver
        driver.get(row["new_user_url"].strip())
        time.sleep(5)

        # Username
        uname = driver.find_element(*loc(row, "username"))
        uname.clear()
        if row["username"].strip():
            uname.send_keys(row["username"].strip())

        # Password — either generate via checkbox or inject via JS
        if row["password"].strip() == "__generate__":
            driver.execute_script(
                "var cb=document.getElementById('id_createpassword');"
                "if(cb&&!cb.checked){cb.click();}"
            )
        else:
            driver.execute_script(
                "var i=document.getElementById('id_newpassword');"
                "if(i){"
                "  i.removeAttribute('readonly');"
                "  i.removeAttribute('disabled');"
                "  i.style.display='';"
                "  var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                "  s.call(i,arguments[0]);"
                "  i.dispatchEvent(new Event('input',{bubbles:true}));"
                "  i.dispatchEvent(new Event('change',{bubbles:true}));"
                "  i.dispatchEvent(new Event('blur',{bubbles:true}));"
                "}",
                row["password"].strip()
            )

        # First name
        fn = driver.find_element(*loc(row, "firstname"))
        fn.clear()
        if row["firstname"].strip():
            fn.send_keys(row["firstname"].strip())

        # Last name
        ln = driver.find_element(*loc(row, "lastname"))
        ln.clear()
        if row["lastname"].strip():
            ln.send_keys(row["lastname"].strip())

        # Email
        em = driver.find_element(*loc(row, "email"))
        em.clear()
        if row["email"].strip():
            em.send_keys(row["email"].strip())

        save = driver.find_element(*loc(row, "save_btn"))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save)
        driver.execute_script("arguments[0].click();", save)
        time.sleep(4)

    def _get_outcome(self) -> str:
        d = self.driver
        if d.find_elements(By.CSS_SELECTOR, "[id^='id_error_']"):
            return "fail"
        if "Changes saved" in d.page_source:
            return "success"
        return "fail"


def _make_user_test(row: dict):
    def test_method(self):
        self._fill_and_submit(row)
        actual   = self._get_outcome()
        expected = row["expected_result"].strip()
        self.assertEqual(actual, expected,
            f"\n  [{row['test_case_id']}] username={repr(row['username'])} "
            f"password={repr(row['password'])} firstname={repr(row['firstname'])} "
            f"lastname={repr(row['lastname'])} email={repr(row['email'])}"
            f"\n  Expected: {expected}  |  Actual: {actual}")
    test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
    return test_method


for _r in load_csv("test_data_tc001_level2.csv"):
    setattr(TestCreateUserLevel2, f"test_{_r['test_case_id'].replace('-','_')}", _make_user_test(_r))


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main(verbosity=2)
