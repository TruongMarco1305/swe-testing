"""
LEVEL 2 — Fully Data-Driven Automation Testing
Feature : Teacher Sets Up a Quiz (Moodle LMS)
Site    : https://ihatetesting.moodlecloud.com/
Tester  : Trương Gia Kỳ Nam

Description
-----------
ALL test data AND element locators AND the site URL are read from
test_data_level2.csv.  This script contains NO hardcoded site-specific values.
"""

import csv
import time
import unittest
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
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


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def loc(row: dict, prefix: str) -> tuple:
    """Build a (By.XXX, value) tuple from two CSV columns <prefix>_locator_type/value."""
    by_str = row[f"{prefix}_locator_type"].strip().lower()
    return (BY_MAP[by_str], row[f"{prefix}_locator_value"].strip())


def set_date_from_row(driver, field_prefix: str, target: datetime):
    """Set a Moodle date-time picker using named <select> elements."""
    Select(driver.find_element(By.NAME, f"{field_prefix}[day]")
           ).select_by_value(str(target.day))
    Select(driver.find_element(By.NAME, f"{field_prefix}[month]")
           ).select_by_value(str(target.month))
    Select(driver.find_element(By.NAME, f"{field_prefix}[year]")
           ).select_by_value(str(target.year))


class TestQuizSetupLevel2(unittest.TestCase):

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
        cls.rows = load_csv("test_data_level2.csv")
        cls._login(cls.rows[0])   # use first row's credentials/locators

    @classmethod
    def _dismiss_cookie_banner(cls):
        """Dismiss OneTrust / cookie consent overlay if present."""
        try:
            accept_btn = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                    "#onetrust-accept-btn-handler, "
                    ".onetrust-accept-btn-handler, "
                    "button[id*='accept'], "
                    "button[class*='accept-all']"))
            )
            accept_btn.click()
            WebDriverWait(cls.driver, 5).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".onetrust-pc-dark-filter"))
            )
        except Exception:
            pass

    @classmethod
    def _login(cls, row: dict):
        driver, wait = cls.driver, cls.wait
        driver.get(row["site_url"] + row["login_url_suffix"])
        wait.until(EC.presence_of_element_located(loc(row, "username")))
        cls._dismiss_cookie_banner()
        driver.find_element(*loc(row, "username")).send_keys(row["username"])
        driver.find_element(*loc(row, "password")).send_keys(row["password"])
        btn = driver.find_element(*loc(row, "login_btn"))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ── Open quiz add form using locators from the row ────────────────────
    def _open_quiz_form(self, row: dict):
        driver, wait = self.driver, self.wait

        driver.get(row["course_url"])
        wait.until(EC.presence_of_element_located(loc(row, "success_indicator")))

        # ── Step 1: Turn on Edit mode via the top-right toggle label ───────
        # HTML: <input name="setmode" id="...-editingswitch">
        #       <label for="...-editingswitch">Edit mode</label>
        edit_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[name='setmode']")
        ))
        if not edit_input.is_selected():
            input_id = edit_input.get_attribute("id")
            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
            driver.execute_script("arguments[0].click();", label)
            wait.until(lambda d: d.find_element(
                By.CSS_SELECTOR, "input[name='setmode']"
            ).is_selected())
            time.sleep(1)

        # ── Step 2: Hover over a section to reveal the "+" button, then click ─
        # The button is hidden until mouseover in Moodle 4.x edit mode
        section = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "li.section, [data-for='section']")
        ))
        ActionChains(driver).move_to_element(section).perform()
        time.sleep(0.5)
        add_btn = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[data-action='open-addingcontent']")
        ))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        driver.execute_script("arguments[0].click();", add_btn)

        # ── Step 3: Click "Activity or resource" from the dropdown ─────────
        activity_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-action='open-chooser']")
        ))
        driver.execute_script("arguments[0].click();", activity_btn)

        # ── Step 4: Wait for the activity chooser modal ────────────────────
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".modchooser, [data-region='chooser-container']")
        ))

        # ── Step 5: Click "Quiz" in the modal ──────────────────────────────
        quiz_item = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             "[data-modname='quiz'] .modchooser-module-name, "
             "[data-modname='quiz'] a, "
             ".modchoosercontainer [title='Quiz']")
        ))
        quiz_item.click()

        # ── Step 6: Click the "Add" button at the bottom of the modal ──────
        add_confirm = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             ".chooser-footer [data-action='add-chooser-option'], "
             ".modal-footer .btn-primary, "
             "button.addbutton")
        ))
        add_confirm.click()

        # ── Wait for the quiz settings form to load ────────────────────────
        wait.until(EC.presence_of_element_located((By.ID, "id_name")))
        time.sleep(1)

    # ── Fill form entirely from row locators ──────────────────────────────
    def _fill_and_submit(self, row: dict):
        driver, wait = self.driver, self.wait
        today = datetime.today()

        # Name
        name_fld = wait.until(EC.presence_of_element_located(loc(row, "quiz_name")))
        name_fld.clear()
        name_fld.send_keys(row["quiz_name"])

        # Open date — always on, today
        open_chk = driver.find_element(
            By.CSS_SELECTOR, "input[name='timeopen[enabled]']")
        if not open_chk.is_selected():
            open_chk.click()
        set_date_from_row(driver, "timeopen", today)

        # Close date
        close_chk = driver.find_element(
            By.CSS_SELECTOR, "input[name='timeclose[enabled]']")
        if row["close_date_enabled"].strip().lower() == "yes":
            if not close_chk.is_selected():
                close_chk.click()
            close_date = today + timedelta(days=int(row["close_date_offset_days"]))
            set_date_from_row(driver, "timeclose", close_date)
        else:
            if close_chk.is_selected():
                close_chk.click()

        # Time limit
        tl_chk = driver.find_element(
            By.CSS_SELECTOR, "input[name='timelimit[enabled]']")
        if row["time_limit_enabled"].strip().lower() == "yes":
            if not tl_chk.is_selected():
                tl_chk.click()
            tl_fld = driver.find_element(*loc(row, "timelimit_value"))
            tl_fld.clear()
            tl_fld.send_keys(str(row["time_limit_minutes"]))
        else:
            if tl_chk.is_selected():
                tl_chk.click()

        # Grade to pass
        grade_fld = driver.find_element(*loc(row, "grade_field"))
        grade_fld.clear()
        grade_fld.send_keys(str(row["grade_to_pass"]))

        # Save
        driver.find_element(*loc(row, "save_btn")).click()

    # ── Determine outcome ─────────────────────────────────────────────────
    def _get_outcome(self, row: dict) -> str:
        driver = self.driver
        time.sleep(2)

        if driver.find_elements(By.CSS_SELECTOR, "#id_error_name,.error[id*='name']"):
            return "fail_name"
        if driver.find_elements(By.CSS_SELECTOR,
                                 "#id_error_gradepass,.error[id*='gradepass']"):
            return "fail_grade"
        if driver.find_elements(By.CSS_SELECTOR,
                                 ".error[id*='timelimit'],#id_error_timelimit_number"):
            return "fail_time"
        if driver.find_elements(By.CSS_SELECTOR,
                                 ".error[id*='timeclose'],#id_error_timeclose"):
            return "fail_date"
        if driver.find_elements(By.CSS_SELECTOR, ".alert-danger,.error"):
            return "fail_general"
        if driver.find_elements(*loc(row, "success_indicator")):
            return "success"
        return "unknown"

    @staticmethod
    def _normalise(raw: str) -> str:
        raw = raw.strip().lower()
        if raw == "success":        return "success"
        if "name"  in raw:          return "fail_name"
        if "grade" in raw:          return "fail_grade"
        if "time"  in raw:          return "fail_time"
        if "date"  in raw or "close" in raw: return "fail_date"
        return raw


def _make_test(row: dict):
    def test_method(self):
        self._open_quiz_form(row)
        self._fill_and_submit(row)
        actual   = self._get_outcome(row)
        expected = self._normalise(row["expected_result"])
        self.assertEqual(
            actual, expected,
            f"\n  [{row['test_case_id']}] "
            f"quiz='{row['quiz_name']}' grade={row['grade_to_pass']} "
            f"time={'disabled' if row['time_limit_enabled']=='no' else row['time_limit_minutes']} "
            f"close={'disabled' if row['close_date_enabled']=='no' else row['close_date_offset_days']+'d'}"
            f"\n  Expected: {expected}  |  Actual: {actual}"
        )
    return test_method


_rows = load_csv("test_data_level2.csv")
for _row in _rows:
    _tc = _row["test_case_id"].replace("-", "_")
    setattr(TestQuizSetupLevel2, f"test_{_tc}", _make_test(_row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
