"""
LEVEL 1 — Data-Driven Automation Testing
Feature : Admin Creates a New Course (Moodle LMS) — Feature 002
Converted from: TC-002.krecorder (Katalon Recorder)

How this was converted from Katalon Recorder
---------------------------------------------
Katalon step               →  Python Selenium
──────────────────────────────────────────────────────────────
open <url>                 →  driver.get(url)
pause 5000                 →  time.sleep(5)
type  id=X, val            →  driver.find_element(By.ID,"X").send_keys(val)
runScript <js>             →  driver.execute_script(js)
click id=id_saveanddisplay →  JS click (sticky footer intercept)
verifyTextPresent          →  assertIn(text, driver.page_source)
verifyElementPresent css=X →  assertTrue(driver.find_elements(By.CSS_SELECTOR, X))

Data-driven approach (Level 1)
--------------------------------
Varying values (fullname, shortname, end_date_enabled, end_date_offset_days,
end_date_offset_years, numsections) are read from test_data_tc002.csv.

All locators and the course creation URL are hardcoded here.

Key test logic
--------------
* TC-002-002 : empty fullname                     → fail (required field)
* TC-002-007 : empty shortname                    → fail (required field)
* TC-002-012/013/027 : end date in past or today  → fail (must be after start)
* TC-002-018/026 : duplicate shortname            → fail
* TC-002-019/021/025 : end_date_enabled=no        → success (no-end-date allowed)
"""

import csv
import time
import unittest
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ── Configuration (hardcoded — Level 1) ───────────────────────────────────
BASE_URL        = "https://ihatetesting.moodlecloud.com/"
LOGIN_URL       = BASE_URL + "login/index.php"
NEW_COURSE_URL  = BASE_URL + "course/edit.php?category=0"

ADMIN_USER  = "phuc.nguyen0310@hcmut.edu.vn"
ADMIN_PASS  = "Huuphuc0310@"

# Hardcoded locators (from krecorder)
LOC_FULLNAME    = (By.ID, "id_fullname")
LOC_SHORTNAME   = (By.ID, "id_shortname")
LOC_SAVE_BTN    = (By.ID, "id_saveanddisplay")

SUCCESS_TEXT    = "Announcements"          # present on course page after creation
FAIL_SELECTOR   = "[id^='id_error_']"      # validation error element


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestCreateCourseLevel1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless=new")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        cls.wait = WebDriverWait(cls.driver, 15)
        cls._login()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    @classmethod
    def _login(cls):
        """Log in as admin using JS injection (bypasses OneTrust overlay)."""
        cls.driver.get(LOGIN_URL)
        time.sleep(3)
        cls.driver.execute_script(
            f"document.getElementById('username').value = '{ADMIN_USER}';"
        )
        cls.driver.execute_script(
            f"document.getElementById('password').value = '{ADMIN_PASS}';"
        )
        cls.driver.execute_script("document.getElementById('login').submit();")
        time.sleep(4)

    def _set_end_date(self, enabled: bool, offset_days: int, offset_years: int):
        """Configure the course end-date fields via JavaScript."""
        if not enabled:
            # Uncheck the end-date checkbox if it is currently checked
            self.driver.execute_script(
                "var cb=document.getElementById('id_enddate_enabled');"
                "if(cb && cb.checked){cb.click();}"
            )
        else:
            # Compute target date: today + offset_years (year) + offset_days (day)
            today = date.today()
            target = today.replace(year=today.year + offset_years) + timedelta(days=offset_days)

            # Ensure the end-date checkbox IS checked
            self.driver.execute_script(
                "var cb=document.getElementById('id_enddate_enabled');"
                "if(cb && !cb.checked){cb.click();}"
            )
            # Set date fields via JS (same pattern as krecorder runScript)
            self.driver.execute_script(
                f"""
                function sS(id, v) {{
                    var e = document.getElementById(id);
                    if (e) {{
                        e.value = String(v);
                        e.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                }}
                sS('id_enddate_day',   {target.day});
                sS('id_enddate_month', {target.month});
                sS('id_enddate_year',  {target.year});
                sS('id_enddate_hour',  0);
                sS('id_enddate_minute', 0);
                """
            )

    def _fill_and_submit(self, fullname: str, shortname: str,
                         end_enabled: bool, offset_days: int, offset_years: int,
                         numsections: int):
        """Navigate to the new-course page, fill fields and submit."""
        driver = self.driver

        driver.get(NEW_COURSE_URL)
        time.sleep(5)  # allow page to fully render

        # Full name
        fn_field = driver.find_element(*LOC_FULLNAME)
        fn_field.clear()
        if fullname:
            fn_field.send_keys(fullname)

        # Short name
        sn_field = driver.find_element(*LOC_SHORTNAME)
        sn_field.clear()
        if shortname:
            sn_field.send_keys(shortname)

        # End date
        self._set_end_date(end_enabled, offset_days, offset_years)

        # Number of sections via JS (avoids spinner issues)
        driver.execute_script(
            f"var e=document.getElementById('id_numsections');"
            f"if(e){{e.value='{numsections}';"
            f"e.dispatchEvent(new Event('change',{{bubbles:true}}));}}"
        )

        # Submit — JS click to avoid sticky-footer interception
        save_btn = driver.find_element(*LOC_SAVE_BTN)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", save_btn)
        time.sleep(4)

    def _get_outcome(self) -> str:
        """Return 'success' or the concatenated visible error message(s)."""
        errs = self.driver.find_elements(By.CSS_SELECTOR, FAIL_SELECTOR)
        if errs:
            msgs = [(e.text or "").strip() for e in errs if (e.text or "").strip()]
            if msgs:
                return " | ".join(msgs)
        if SUCCESS_TEXT in self.driver.page_source:
            return "success"
        return "unknown"

    @staticmethod
    def _matches_expected(actual: str, expected: str) -> bool:
        a = (actual or "").lower()
        e = (expected or "").lower().strip()
        if e == "success":
            return a == "success"
        if a == "success":
            return False
        return all(c.strip() in a for c in e.split(";") if c.strip())

    @staticmethod
    def _make_test(row: dict):
        """Factory: create a bound test method from one CSV row."""
        tc_id        = row["test_case_id"]
        fullname     = row["fullname"]
        shortname    = row["shortname"]
        end_enabled  = row["end_date_enabled"].strip().lower() == "yes"
        offset_days  = int(row["end_date_offset_days"])
        offset_years = int(row["end_date_offset_years"])
        numsections  = int(row["numsections"])
        expected     = row["expected_result"].strip()

        def test_method(self):
            self._fill_and_submit(
                fullname, shortname,
                end_enabled, offset_days, offset_years,
                numsections
            )
            actual = self._get_outcome()
            self.assertTrue(
                self._matches_expected(actual, expected),
                f"[{tc_id}] Expected '{expected}' but got '{actual}'\n"
                f"  fullname={fullname!r}, shortname={shortname!r}, "
                f"end_enabled={end_enabled}, offset_days={offset_days}, "
                f"offset_years={offset_years}"
            )

        test_method.__name__ = f"test_{tc_id.replace('-', '_')}"
        return test_method


# ── Dynamically generate one test method per CSV row ──────────────────────
import os
_CSV_PATH = os.path.join(os.path.dirname(__file__), "test_data_tc002.csv")
for _row in load_csv(_CSV_PATH):
    _method = TestCreateCourseLevel1._make_test(_row)
    setattr(TestCreateCourseLevel1, _method.__name__, _method)


if __name__ == "__main__":
    unittest.main(verbosity=2)
