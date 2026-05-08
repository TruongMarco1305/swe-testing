"""
LEVEL 1 — Data-Driven Automation Testing
Feature : Teacher Sets Up a Quiz (Moodle LMS)
Site    : https://ihatetesting.moodlecloud.com/
Tester  : Trương Gia Kỳ Nam

Description
-----------
Test DATA is read from test_data.csv.
Element locators and the site URL are hardcoded in this script.
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

# ── Site / account configuration ──────────────────────────────────────────
BASE_URL   = "https://ihatetesting.moodlecloud.com/"
USERNAME   = "phuc.nguyen0310@hcmut.edu.vn"
PASSWORD   = "Huuphuc0310@"
COURSE_URL = "https://ihatetesting.moodlecloud.com/course/view.php?id=141"  # ← adjust id

# ── Hardcoded locators ─────────────────────────────────────────────────────
LOC_USERNAME_FIELD  = (By.ID,   "username")
LOC_PASSWORD_FIELD  = (By.ID,   "password")
LOC_LOGIN_BTN       = (By.ID,   "loginbtn")

LOC_EDIT_MODE_BTN   = (By.CSS_SELECTOR, "input[data-action='toggle-editing'],"
                                         "button[data-action='toggle-editing']")
LOC_ADD_ACTIVITY    = (By.CSS_SELECTOR, ".section-modchooser-link, "
                                         "[data-action='open-chooser']")
LOC_QUIZ_OPTION     = (By.CSS_SELECTOR, "[data-modname='quiz'], "
                                         "a[href*='quiz']")
LOC_QUIZ_NAME       = (By.ID,   "id_name")
LOC_OPEN_ENABLE     = (By.CSS_SELECTOR, "input[name='timeopen[enabled]']")
LOC_CLOSE_ENABLE    = (By.CSS_SELECTOR, "input[name='timeclose[enabled]']")
LOC_TIMELIMIT_ENABLE= (By.CSS_SELECTOR, "input[name='timelimit[enabled]']")
LOC_TIMELIMIT_VALUE = (By.CSS_SELECTOR, "input[name='timelimit[number]']")
LOC_GRADE_TO_PASS   = (By.ID,   "id_gradepass")
LOC_SAVE_BTN        = (By.ID,   "id_submitbutton2")

# Error/success indicators
LOC_ERROR_NAME      = (By.CSS_SELECTOR, "#id_error_name, .error[id*='name']")
LOC_ERROR_GRADE     = (By.CSS_SELECTOR, "#id_error_gradepass, .error[id*='gradepass']")
LOC_ERROR_TIME      = (By.CSS_SELECTOR, ".error[id*='timelimit'], #id_error_timelimit_number")
LOC_ERROR_DATE      = (By.CSS_SELECTOR, ".error[id*='timeclose'], #id_error_timeclose")
LOC_GENERAL_ERROR   = (By.CSS_SELECTOR, ".alert-danger, .error, [data-region='notice']")
LOC_COURSE_PAGE     = (By.CSS_SELECTOR, ".course-content, #page-course-view-topics")


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def set_date(driver, wait, field_prefix: str, target_date: datetime):
    """Set a Moodle date-time picker (day/month/year/hour/minute selects)."""
    Select(driver.find_element(By.NAME, f"{field_prefix}[day]")
           ).select_by_value(str(target_date.day))
    Select(driver.find_element(By.NAME, f"{field_prefix}[month]")
           ).select_by_value(str(target_date.month))
    Select(driver.find_element(By.NAME, f"{field_prefix}[year]")
           ).select_by_value(str(target_date.year))


class TestQuizSetupLevel1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless=new")  # uncomment for headless
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        cls.wait = WebDriverWait(cls.driver, 15)
        cls.data = load_csv("test_data.csv")
        cls._login()

    @classmethod
    def _dismiss_cookie_banner(cls):
        """Dismiss OneTrust / cookie consent overlay if present."""
        try:
            # Wait up to 5 s for the accept button to appear
            accept_btn = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                    "#onetrust-accept-btn-handler, "
                    ".onetrust-accept-btn-handler, "
                    "button[id*='accept'], "
                    "button[class*='accept-all']"))
            )
            accept_btn.click()
            # Wait for the overlay to disappear
            WebDriverWait(cls.driver, 5).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".onetrust-pc-dark-filter"))
            )
        except Exception:
            pass  # No banner present — continue normally

    @classmethod
    def _login(cls):
        cls.driver.get(BASE_URL + "login/index.php")
        cls.wait.until(EC.presence_of_element_located(LOC_USERNAME_FIELD))
        cls._dismiss_cookie_banner()
        cls.driver.find_element(*LOC_USERNAME_FIELD).send_keys(USERNAME)
        cls.driver.find_element(*LOC_PASSWORD_FIELD).send_keys(PASSWORD)
        # Always use JS click — bypasses any overlay (OneTrust, etc.)
        btn = cls.driver.find_element(*LOC_LOGIN_BTN)
        cls.driver.execute_script("arguments[0].click();", btn)
        cls.wait.until(EC.url_contains("/my"))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ── Helper: navigate to quiz add form ─────────────────────────────────
    def _open_quiz_form(self):
        driver, wait = self.driver, self.wait

        # Go to course
        driver.get(COURSE_URL)
        wait.until(EC.presence_of_element_located(LOC_COURSE_PAGE))

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
        wait.until(EC.presence_of_element_located(LOC_QUIZ_NAME))
        time.sleep(1)

    # ── Helper: fill quiz form from row dict ──────────────────────────────
    def _fill_quiz_form(self, row: dict):
        driver, wait = self.driver, self.wait
        today = datetime.today()

        # Quiz Name
        name_field = wait.until(EC.presence_of_element_located(LOC_QUIZ_NAME))
        name_field.clear()
        name_field.send_keys(row["quiz_name"])

        # Open date — always enable + set to today
        open_chk = driver.find_element(*LOC_OPEN_ENABLE)
        if not open_chk.is_selected():
            open_chk.click()
        set_date(driver, wait, "timeopen", today)

        # Close date
        close_chk = driver.find_element(*LOC_CLOSE_ENABLE)
        if row["close_date_enabled"].strip().lower() == "yes":
            if not close_chk.is_selected():
                close_chk.click()
            offset = int(row["close_date_offset_days"])
            close_date = today + timedelta(days=offset)
            set_date(driver, wait, "timeclose", close_date)
        else:
            if close_chk.is_selected():
                close_chk.click()

        # Time limit
        tl_chk = driver.find_element(*LOC_TIMELIMIT_ENABLE)
        if row["time_limit_enabled"].strip().lower() == "yes":
            if not tl_chk.is_selected():
                tl_chk.click()
            tl_field = driver.find_element(*LOC_TIMELIMIT_VALUE)
            tl_field.clear()
            tl_field.send_keys(str(row["time_limit_minutes"]))
        else:
            if tl_chk.is_selected():
                tl_chk.click()

        # Grade to pass
        grade_field = driver.find_element(*LOC_GRADE_TO_PASS)
        grade_field.clear()
        grade_field.send_keys(str(row["grade_to_pass"]))

        # Submit
        driver.find_element(*LOC_SAVE_BTN).click()

    # ── Helper: determine actual outcome ─────────────────────────────────
    def _get_outcome(self) -> str:
        driver, wait = self.driver, self.wait
        time.sleep(2)

        if driver.find_elements(*LOC_ERROR_NAME):
            return "fail_name"
        if driver.find_elements(*LOC_ERROR_GRADE):
            return "fail_grade"
        if driver.find_elements(*LOC_ERROR_TIME):
            return "fail_time"
        if driver.find_elements(*LOC_ERROR_DATE):
            return "fail_date"
        if driver.find_elements(*LOC_GENERAL_ERROR):
            return "fail_general"
        # If redirected back to course page → success
        if driver.find_elements(*LOC_COURSE_PAGE):
            return "success"
        return "unknown"

    # ── Map expected_result column → normalised key ───────────────────────
    @staticmethod
    def _normalise_expected(raw: str) -> str:
        raw = raw.strip().lower()
        if raw == "success":
            return "success"
        if "name" in raw:
            return "fail_name"
        if "grade" in raw:
            return "fail_grade"
        if "time" in raw:
            return "fail_time"
        if "date" in raw or "close" in raw or "open" in raw:
            return "fail_date"
        return raw  # fallback (e.g. fail_general)


def _make_test(row: dict):
    def test_method(self):
        self._open_quiz_form()
        self._fill_quiz_form(row)
        actual   = self._get_outcome()
        expected = self._normalise_expected(row["expected_result"])
        self.assertEqual(
            actual, expected,
            f"\n  [{row['test_case_id']}] quiz='{row['quiz_name']}' "
            f"grade={row['grade_to_pass']} "
            f"time={'disabled' if row['time_limit_enabled']=='no' else row['time_limit_minutes']} "
            f"close={'disabled' if row['close_date_enabled']=='no' else row['close_date_offset_days']+'d'}"
            f"\n  Expected: {expected}  |  Actual: {actual}"
        )
    return test_method


# ── Dynamically attach one test method per CSV row ────────────────────────
_rows = load_csv("test_data.csv")
for _row in _rows:
    _tc = _row["test_case_id"].replace("-", "_")
    setattr(TestQuizSetupLevel1, f"test_{_tc}", _make_test(_row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
