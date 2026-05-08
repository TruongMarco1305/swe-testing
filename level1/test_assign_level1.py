"""
TC-003 – Teacher Creates an Assignment (Level 1)
=================================================
Data-driven Selenium test: one unittest method per CSV row.
Preparation: logs in as admin and switches role to Teacher on course 141.
Each test case navigates to the "Add Assignment" form, fills fields, submits,
and asserts the expected outcome (success / fail).

Run all:
    cd level1
    python3 -m pytest test_assign_level1.py -v

Run single:
    python3 -m pytest test_assign_level1.py -v -k "TC_003_001"
"""

import csv
import os
import time
import unittest
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL    = "https://ihatetesting.moodlecloud.com"
LOGIN_URL   = f"{BASE_URL}/login/index.php"
ASSIGN_URL  = (
    f"{BASE_URL}/course/modedit.php"
    "?add=assign&type&course=141&sectionid=695&return=0&beforemod=0"
)
ADMIN_USER  = "phuc.nguyen0310@hcmut.edu.vn"
ADMIN_PASS  = "Huuphuc0310@"

CSV_PATH = os.path.join(os.path.dirname(__file__), "test_data_tc003.csv")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------
class TestAssignLevel1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        cls.driver.implicitly_wait(10)
        cls._login_and_switch_role()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ------------------------------------------------------------------
    # Preparation helpers
    # ------------------------------------------------------------------
    @classmethod
    def _login_and_switch_role(cls):
        """Login as admin and switch role to Teacher on course 141."""
        driver = cls.driver
        driver.get(LOGIN_URL)
        driver.execute_script(
            """
            document.getElementById('username').value = arguments[0];
            document.getElementById('password').value = arguments[1];
            document.getElementById('login').submit();
            """,
            ADMIN_USER,
            ADMIN_PASS,
        )
        time.sleep(3)
        # Switch role to Teacher
        driver.get(
            f"{BASE_URL}/course/switchrole.php"
            "?id=1&switchrole=-1&returnurl=%2Fmy%2Findex.php"
        )
        time.sleep(2)
        # Click the "Teacher" button if present
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, "form button")
            for btn in btns:
                if "Teacher" in btn.text or btn.get_attribute("value") == "Teacher":
                    driver.execute_script("arguments[0].click();", btn)
                    break
            else:
                # click the first submit button on the switch-role page
                driver.execute_script("arguments[0].click();", btns[0])
        except Exception:
            pass
        time.sleep(2)
        driver.get(f"{BASE_URL}/my/index.php")
        time.sleep(2)

    # ------------------------------------------------------------------
    # Per-test helpers
    # ------------------------------------------------------------------
    def _set_dates(self, duedate_enabled, due_off_days, due_off_years,
                   cutoff_off_days, cutoff_off_years):
        """
        Configure dates via JS.
        - allowsubmissionsfromdate = today (always enabled)
        - duedate: enabled/disabled per param; offset from today
        - cutoffdate: base = duedate (if enabled) else today; offset applied
        - gradingduedate: always disabled
        """
        today = date.today()

        # Compute due date
        if duedate_enabled:
            try:
                due = today.replace(year=today.year + due_off_years)
            except ValueError:
                due = today.replace(year=today.year + due_off_years, day=28)
            due = due + timedelta(days=due_off_days)
            due_day, due_mon, due_yr = due.day, due.month, due.year
        else:
            due_day, due_mon, due_yr = today.day, today.month, today.year

        # Compute cutoff base
        base_date = date(due_yr, due_mon, due_day) if duedate_enabled else today
        try:
            cutoff = base_date.replace(year=base_date.year + cutoff_off_years)
        except ValueError:
            cutoff = base_date.replace(year=base_date.year + cutoff_off_years, day=28)
        cutoff = cutoff + timedelta(days=cutoff_off_days)

        due_enable_js   = "ens" if duedate_enabled else "dis"
        script = f"""
            function sS(id, v) {{
                var e = document.getElementById(id);
                if (e) {{ e.value = String(v); e.dispatchEvent(new Event('change', {{bubbles:true}})); }}
            }}
            function ens(id) {{
                var c = document.getElementById(id);
                if (c && !c.checked) {{ c.click(); }}
            }}
            function dis(id) {{
                var c = document.getElementById(id);
                if (c && c.checked) {{ c.click(); }}
            }}
            // Grading due date – always disabled
            dis('id_gradingduedate_enabled');
            // Allow submissions from date – always today
            ens('id_allowsubmissionsfromdate_enabled');
            var tod = new Date();
            sS('id_allowsubmissionsfromdate_day',   tod.getDate());
            sS('id_allowsubmissionsfromdate_month', tod.getMonth() + 1);
            sS('id_allowsubmissionsfromdate_year',  tod.getFullYear());
            // Due date
            {due_enable_js}('id_duedate_enabled');
            sS('id_duedate_day',   {due_day});
            sS('id_duedate_month', {due_mon});
            sS('id_duedate_year',  {due_yr});
            // Cutoff date
            ens('id_cutoffdate_enabled');
            sS('id_cutoffdate_day',   {cutoff.day});
            sS('id_cutoffdate_month', {cutoff.month});
            sS('id_cutoffdate_year',  {cutoff.year});
            // Ensure grading due date is still disabled
            dis('id_gradingduedate_enabled');
        """
        self.driver.execute_script(script)

    def _set_submission_types(self, sub_file, sub_onlinetext):
        """Set submission type checkboxes if not 'default'."""
        if sub_file == "default" and sub_onlinetext == "default":
            return
        want_file   = (sub_file        == "yes") if sub_file        != "default" else None
        want_online = (sub_onlinetext  == "yes") if sub_onlinetext  != "default" else None
        script_parts = []
        if want_file is not None:
            script_parts.append(
                f"setCB('id_assignsubmission_file_enabled', {'true' if want_file else 'false'});"
            )
        if want_online is not None:
            script_parts.append(
                f"setCB('id_assignsubmission_onlinetext_enabled', {'true' if want_online else 'false'});"
            )
        js = (
            "function setCB(id, want) {"
            "  var c = document.getElementById(id);"
            "  if (c && c.checked !== want) { c.click(); }"
            "}"
        ) + "".join(script_parts)
        self.driver.execute_script(js)

    def _fill_and_submit(self, row):
        driver = self.driver
        driver.get(ASSIGN_URL)
        time.sleep(5)  # wait for page JS to settle

        # Assignment name
        name = row["name"].strip()
        if name:
            name_field = driver.find_element(By.ID, "id_name")
            name_field.clear()
            name_field.send_keys(name)

        # Dates
        duedate_enabled   = row["duedate_enabled"].strip().lower() == "yes"
        due_off_days      = int(row["duedate_offset_days"])
        due_off_years     = int(row["duedate_offset_years"])
        cutoff_off_days   = int(row["cutoff_offset_days"])
        cutoff_off_years  = int(row["cutoff_offset_years"])
        self._set_dates(duedate_enabled, due_off_days, due_off_years,
                        cutoff_off_days, cutoff_off_years)

        # Grade to pass
        gradepass = row["gradepass"].strip()
        driver.execute_script(
            """
            var g = document.getElementById('id_gradepass');
            if (g) {
                g.value = arguments[0];
                g.dispatchEvent(new Event('input',  {bubbles:true}));
                g.dispatchEvent(new Event('change', {bubbles:true}));
            }
            """,
            gradepass,
        )

        # Submission types
        self._set_submission_types(
            row["submission_file"].strip(),
            row["submission_onlinetext"].strip(),
        )

        # Ensure grading due date disabled one more time
        driver.execute_script(
            "var c=document.getElementById('id_gradingduedate_enabled');"
            "if(c && c.checked){c.click();}"
        )

        # Submit
        try:
            btn = driver.find_element(By.ID, "id_submitbutton2")
        except Exception:
            btn = driver.find_element(By.ID, "id_submitbutton")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

    def _get_outcome(self):
        """Return 'success' or 'fail' based on the current page."""
        driver = self.driver
        errors = driver.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
        if errors:
            return "fail"
        if "Announcements" in driver.page_source:
            return "success"
        return "fail"

    # ------------------------------------------------------------------
    # Dynamic test generation
    # ------------------------------------------------------------------
    @classmethod
    def _make_test(cls, row):
        def test_method(self):
            self._fill_and_submit(row)
            actual   = self._get_outcome()
            expected = row["expected_result"].strip()
            self.assertEqual(
                actual,
                expected,
                f"{row['test_case_id']}: expected '{expected}' but got '{actual}'"
                f" (name='{row['name'][:30]}...', gradepass={row['gradepass']})",
            )
        test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
        test_method.__doc__  = (
            f"{row['test_case_id']}: name='{row['name'][:40]}', "
            f"gradepass={row['gradepass']}, expected={row['expected_result']}"
        )
        return test_method


def _load_tests():
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            method_name = f"test_{row['test_case_id'].replace('-', '_')}"
            setattr(
                TestAssignLevel1,
                method_name,
                TestAssignLevel1._make_test(row),
            )


_load_tests()

if __name__ == "__main__":
    unittest.main(verbosity=2)
