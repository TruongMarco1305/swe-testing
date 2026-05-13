"""
LEVEL 1 — Data-Driven Automation Testing
Feature : Admin Adds a New User (Moodle LMS) — Feature 001
Tester  : Nguyễn Hữu Phúc
Converted from: TC-001.krecorder (Katalon Recorder)

How this was converted from Katalon Recorder
---------------------------------------------
Katalon step        →  Python Selenium
────────────────────────────────────────────
open <url>          →  driver.get(url)
pause 5000          →  time.sleep(5)
click id=X          →  driver.find_element(By.ID, "X").click()
type  id=X, val     →  driver.find_element(By.ID, "X").send_keys(val)
runScript <js>      →  driver.execute_script(js)
verifyTextPresent   →  self.assertIn(text, driver.page_source)
verifyElementPresent css=X → self.assertTrue(driver.find_elements(By.CSS_SELECTOR, X))

Data-driven approach (Level 1)
--------------------------------
The VARYING values across TC-001-001 … TC-001-010:
  username, password, email, expected_result
are extracted into test_data_tc001.csv.

Everything else (firstname, lastname, locators, URLs) is hardcoded here.
"""

import csv
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ── Configuration (hardcoded — Level 1) ───────────────────────────────────
BASE_URL    = "https://ihatetesting.moodlecloud.com/"
LOGIN_URL   = BASE_URL + "login/index.php"
ADD_USER_URL = BASE_URL + "user/editadvanced.php?id=-1"

ADMIN_USER  = "phuc.nguyen0310@hcmut.edu.vn"
ADMIN_PASS  = "Huuphuc0310@"

# Hardcoded locators (from krecorder)
LOC_LOGIN_USERNAME = (By.ID, "username")
LOC_LOGIN_PASSWORD = (By.ID, "password")
LOC_LOGIN_BTN      = (By.ID, "loginbtn")

LOC_USERNAME   = (By.ID, "id_username")
LOC_FIRSTNAME  = (By.ID, "id_firstname")
LOC_LASTNAME   = (By.ID, "id_lastname")
LOC_EMAIL      = (By.ID, "id_email")
LOC_SUBMIT     = (By.ID, "id_submitbutton")

# Success indicator: "Changes saved" text
SUCCESS_TEXT   = "Changes saved"
# Failure indicator: any error element whose id starts with "id_error_"
FAIL_SELECTOR  = "[id^='id_error_']"


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestAddUserLevel1(unittest.TestCase):

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
    def _login(cls):
        """Login once for the whole test suite (from krecorder Preparation block)."""
        cls.driver.get(LOGIN_URL)
        cls.wait.until(EC.presence_of_element_located(LOC_LOGIN_USERNAME))

        # Dismiss OneTrust cookie banner if present
        try:
            accept = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
            )
            cls.driver.execute_script("arguments[0].click();", accept)
        except Exception:
            pass

        cls.driver.find_element(*LOC_LOGIN_USERNAME).send_keys(ADMIN_USER)
        cls.driver.find_element(*LOC_LOGIN_PASSWORD).send_keys(ADMIN_PASS)
        cls.driver.execute_script(
            "arguments[0].click();",
            cls.driver.find_element(*LOC_LOGIN_BTN)
        )
        cls.wait.until(EC.url_contains("/my"))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ── Helper: set password via JS (mirrors krecorder runScript) ─────────
    def _set_password(self, password: str):
        """
        Moodle's password field has readonly/disabled attributes that prevent
        normal send_keys. The krecorder used runScript to bypass this.
        We replicate that exact JS here.
        """
        js = """
        var i = document.getElementById('id_newpassword');
        if (i) {
            i.removeAttribute('readonly');
            i.removeAttribute('disabled');
            i.style.display = '';
            var s = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
            s.call(i, arguments[0]);
            i.dispatchEvent(new Event('input',  {bubbles: true}));
            i.dispatchEvent(new Event('change', {bubbles: true}));
            i.dispatchEvent(new Event('blur',   {bubbles: true}));
        }
        """
        self.driver.execute_script(js, password)

    # ── Helper: fill and submit the Add User form ─────────────────────────
    def _fill_and_submit(self, row: dict):
        driver, wait = self.driver, self.wait

        # Navigate to Add User page (mirrors krecorder "open" step)
        driver.get(ADD_USER_URL)
        wait.until(EC.presence_of_element_located(LOC_USERNAME))
        time.sleep(5)   # mirrors krecorder "pause 5000"

        # Username
        u = driver.find_element(*LOC_USERNAME)
        u.clear()
        u.send_keys(row["username"])

        # Password: "__generate__" → tick the "Generate password and notify user"
        # checkbox (mirrors krecorder TC-001-033 `click id=id_createpassword`).
        # Otherwise use JS runScript to bypass the readonly attribute.
        if row["password"].strip() == "__generate__":
            cb = driver.find_element(By.ID, "id_createpassword")
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
        else:
            self._set_password(row["password"])

        # First name
        f = driver.find_element(*LOC_FIRSTNAME)
        f.clear()
        f.send_keys(row["firstname"])

        # Last name
        ln = driver.find_element(*LOC_LASTNAME)
        ln.clear()
        ln.send_keys(row["lastname"])

        # Email
        e = driver.find_element(*LOC_EMAIL)
        e.clear()
        e.send_keys(row["email"])

        # Submit — scroll into view first, then JS-click to avoid overlay interception
        submit_btn = driver.find_element(*LOC_SUBMIT)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(2)

    # ── Helper: read actual outcome ───────────────────────────────────────
    def _get_outcome(self) -> str:
        """
        Return either "success" or the concatenated error message text(s)
        rendered by Moodle. Empty string if neither marker is present.
        """
        if SUCCESS_TEXT in self.driver.page_source:
            return "success"
        # Collect visible error message text from all id_error_* elements
        msgs = []
        for el in self.driver.find_elements(By.CSS_SELECTOR, FAIL_SELECTOR):
            txt = (el.text or "").strip()
            if txt:
                msgs.append(txt)
        if msgs:
            return " | ".join(msgs)
        return "unknown"


def _matches_expected(actual: str, expected: str) -> bool:
    """Compare actual outcome string to the expected CSV value.

    Rules:
      * expected == "success"      -> actual must be exactly "success"
      * any other value            -> actual must NOT be "success" AND every
                                      semicolon-separated chunk of expected
                                      must appear as a substring of actual
                                      (case-insensitive).
    """
    a = (actual or "").lower()
    e = (expected or "").lower().strip()
    if e == "success":
        return a == "success"
    if a == "success":
        return False
    chunks = [c.strip() for c in e.split(";") if c.strip()]
    return all(c in a for c in chunks)


# ── Factory: one test method per CSV row ──────────────────────────────────
def _make_test(row: dict):
    def test_method(self):
        self._fill_and_submit(row)
        actual   = self._get_outcome()
        expected = row["expected_result"].strip()
        self.assertTrue(
            _matches_expected(actual, expected),
            f"\n  [{row['test_case_id']}]"
            f"\n  username = '{row['username']}'"
            f"\n  password = '{row['password'][:10]}…'"
            f"\n  email    = '{row['email']}'"
            f"\n  Expected : {expected}  |  Actual : {actual}"
        )
    return test_method


_rows = load_csv("test_data_tc001.csv")
for _row in _rows:
    _tc = _row["test_case_id"].replace("-", "_")
    setattr(TestAddUserLevel1, f"test_{_tc}", _make_test(_row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
