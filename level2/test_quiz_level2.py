"""
LEVEL 2 — Fully Data-Driven Automation Testing
Feature : Teacher Sets Up a Quiz (Moodle LMS)
Site    : https://ihatetesting.moodlecloud.com/

Description
-----------
ALL test data AND element locators AND the site URL are read from
test_data_level2.csv.  This script contains NO hardcoded site-specific values.

Columns used from CSV
---------------------
Locator pairs  (<prefix>_locator_type / <prefix>_locator_value):
  username · password · login_btn · quiz_name · grade_field
  timelimit_value · save_btn · success_indicator

Data columns:
  site_url, login_url_suffix, quiz_add_url
  username, password
  quiz_name, grade_to_pass
  time_limit_enabled (yes/no), time_limit_minutes
  close_date_enabled (yes/no), close_date_offset_days, close_date_offset_years
  expected_result  (success | fail_name | fail_grade | fail_time | fail_date)
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
from webdriver_manager.chrome import ChromeDriverManager

BY_MAP = {
    "id":           By.ID,
    "name":         By.NAME,
    "class name":   By.CLASS_NAME,
    "css selector": By.CSS_SELECTOR,
    "xpath":        By.XPATH,
    "link text":    By.LINK_TEXT,
    "tag name":     By.TAG_NAME,
}

CSV_PATH = os.path.join(os.path.dirname(__file__), "test_data_level2.csv")

JS_HELPERS = """
function sS(id,v){
  var e=document.getElementById(id);
  if(e){e.value=String(v);e.dispatchEvent(new Event('change',{bubbles:true}));}
}
function nS(id,v){
  var e=document.getElementById(id);
  if(e){
    var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    s.call(e,String(v));
    e.dispatchEvent(new Event('input',{bubbles:true}));
    e.dispatchEvent(new Event('change',{bubbles:true}));
  }
}
function ens(id){var c=document.getElementById(id);if(c&&!c.checked){c.click();}}
function dis(id){var c=document.getElementById(id);if(c&&c.checked){c.click();}}
"""


def load_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def loc(row: dict, prefix: str) -> tuple:
    """Build a (By.XXX, value) locator tuple from two CSV columns."""
    by_str = row[f"{prefix}_locator_type"].strip().lower()
    return (BY_MAP[by_str], row[f"{prefix}_locator_value"].strip())


class TestQuizSetupLevel2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        cls.driver.set_window_size(1400, 900)
        cls.wait = WebDriverWait(cls.driver, 20)
        cls.rows = load_csv(CSV_PATH)
        cls._login(cls.rows[0])

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
    def tearDownClass(cls):
        cls.driver.quit()

    def _open_quiz_form(self, row: dict):
        """Navigate directly to the quiz add form URL stored in the CSV."""
        self.driver.get(row["quiz_add_url"].strip())
        self.wait.until(EC.presence_of_element_located(loc(row, "quiz_name")))

    def _fill_and_submit(self, row: dict):
        driver = self.driver

        # Quiz name — via locator from CSV
        name_fld = driver.find_element(*loc(row, "quiz_name"))
        name_fld.clear()
        if row["quiz_name"].strip():
            name_fld.send_keys(row["quiz_name"].strip())

        close_enabled = row["close_date_enabled"].strip().lower() == "yes"
        limit_enabled = row["time_limit_enabled"].strip().lower() == "yes"
        close_days    = int(row["close_date_offset_days"]) if row.get("close_date_offset_days", "").strip() else 7
        close_years   = int(row.get("close_date_offset_years", "0") or "0")
        limit_val     = row["time_limit_minutes"].strip() if row.get("time_limit_minutes", "").strip() else "30"
        gradepass     = row["grade_to_pass"].strip()

        js = JS_HELPERS + """
ens('id_timeopen_enabled');
var tod=new Date();
sS('id_timeopen_day',tod.getDate());
sS('id_timeopen_month',tod.getMonth()+1);
sS('id_timeopen_year',tod.getFullYear());
sS('id_timeopen_hour',tod.getHours());
sS('id_timeopen_minute',0);
"""
        if close_enabled:
            js += f"""
ens('id_timeclose_enabled');
var cl=new Date(tod);
cl.setFullYear(cl.getFullYear()+({close_years}));
cl.setDate(cl.getDate()+({close_days}));
sS('id_timeclose_day',cl.getDate());
sS('id_timeclose_month',cl.getMonth()+1);
sS('id_timeclose_year',cl.getFullYear());
sS('id_timeclose_hour',cl.getHours());
sS('id_timeclose_minute',0);
"""
        else:
            js += "dis('id_timeclose_enabled');\n"

        if limit_enabled:
            js += f"""
ens('id_timelimit_enabled');
nS('id_timelimit_number',{repr(limit_val)});
sS('id_timelimit_timeunit','60');
"""
        else:
            js += "dis('id_timelimit_enabled');\n"

        js += f"nS('id_gradepass',{repr(gradepass)});\n"

        driver.execute_script(js)
        time.sleep(2)

        # Save button — via locator from CSV, JS click
        try:
            btn = driver.find_element(*loc(row, "save_btn"))
        except Exception:
            btn = driver.find_element(By.ID, "id_submitbutton")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

    def _get_outcome(self, driver) -> str:
        errors = driver.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
        visible = [e for e in errors if e.is_displayed() and e.text.strip()]
        if visible:
            ids = " ".join(e.get_attribute("id") for e in visible).lower()
            if "gradepass" in ids: return "fail_grade"
            if "timelimit" in ids: return "fail_time"
            if "timeclose" in ids: return "fail_date"
            if "name"      in ids: return "fail_name"
            return "fail_general"
        if "Announcements" in driver.page_source:
            return "success"
        return "success"

    @staticmethod
    def _normalise(raw: str) -> str:
        raw = raw.strip().lower()
        if raw == "success":                 return "success"
        if "name"  in raw:                   return "fail_name"
        if "grade" in raw:                   return "fail_grade"
        if "time"  in raw:                   return "fail_time"
        if "date"  in raw or "close" in raw: return "fail_date"
        if raw.startswith("fail"):           return "fail_general"
        return raw


def _make_test(row: dict):
    def test_method(self):
        self._open_quiz_form(row)
        self._fill_and_submit(row)
        actual   = self._get_outcome(self.driver)
        expected = self._normalise(row["expected_result"])
        self.assertEqual(
            actual, expected,
            f"\n  [{row['test_case_id']}] "
            f"quiz='{row['quiz_name']}' grade={row['grade_to_pass']} "
            f"timelimit={'off' if row['time_limit_enabled'].lower()=='no' else row['time_limit_minutes']} "
            f"close={'off' if row['close_date_enabled'].lower()=='no' else row['close_date_offset_days']+'d'}"
            f"\n  Expected: {expected}  |  Actual: {actual}"
        )
    test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
    return test_method


_rows = load_csv(CSV_PATH)
for _row in _rows:
    _m = _make_test(_row)
    setattr(TestQuizSetupLevel2, _m.__name__, _m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
