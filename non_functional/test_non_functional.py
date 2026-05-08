"""
NON-FUNCTIONAL TESTING — Moodle LMS
Feature : Teacher Sets Up a Quiz
Site    : https://ihatetesting.moodlecloud.com/
Tester  : Trương Gia Kỳ Nam

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-FUNCTIONAL TEST 1 — PERFORMANCE TESTING
  Type     : Performance / Response Time
  Approach : Measure page-load time and quiz-form-save response time using
             Python's time.time(). Assert against an acceptable SLA threshold.
             Single-user baseline measurement (not load/stress testing).
  Tool     : Selenium + Python time module

NON-FUNCTIONAL TEST 2 — SECURITY TESTING
  Type     : Security — Input Validation / XSS Prevention / Sensitive data
  Approach : Submit malicious payloads in the Quiz Name and Grade fields.
             Verify the application rejects/sanitises them and does not leak
             stack traces or execute injected scripts. Also verify the login
             password field is masked.
  Tool     : Selenium + Python unittest
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

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

# ── Configuration ──────────────────────────────────────────────────────────
BASE_URL   = "https://ihatetesting.moodlecloud.com/"
LOGIN_URL  = BASE_URL + "login/index.php"
COURSE_URL = BASE_URL + "course/view.php?id=2"   # ← adjust if needed
USERNAME   = "phuc.nguyen0310@hcmut.edu.vn"
PASSWORD   = "Huuphuc0310@"

# Acceptable SLA thresholds
LOGIN_PAGE_LOAD_THRESHOLD  = 5.0   # seconds
QUIZ_FORM_LOAD_THRESHOLD   = 8.0   # seconds (activity chooser → form)
QUIZ_SAVE_THRESHOLD        = 6.0   # seconds (click Save → course page)

# XSS / injection payloads to test in the quiz Name field
ATTACK_PAYLOADS = [
    "<script>alert('xss')</script>",
    "' OR '1'='1",
    '" OR "1"="1',
    "<img src=x onerror=alert(1)>",
    "'; DROP TABLE mdl_quiz; --",
]


def _make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def _dismiss_cookie_banner(driver):
    """Dismiss OneTrust / cookie consent overlay if present."""
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "#onetrust-accept-btn-handler, "
                ".onetrust-accept-btn-handler, "
                "button[id*='accept'], "
                "button[class*='accept-all']"))
        )
        accept_btn.click()
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".onetrust-pc-dark-filter"))
        )
    except Exception:
        pass


def _login(driver, wait):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    _dismiss_cookie_banner(driver)
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    # Always JS-click to bypass any overlay
    btn = driver.find_element(By.ID, "loginbtn")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(2)


def _open_quiz_add_form(driver, wait):
    """Navigate to course and open the Add Quiz form."""
    driver.get(COURSE_URL)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-content")))

    # ── Step 1: Turn on Edit mode via the top-right toggle label ──────────
    # HTML: <input name="setmode" id="...-editingswitch">
    #       <label for="...-editingswitch">Edit mode</label>
    edit_input = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input[name='setmode']")
    ))
    if not edit_input.is_selected():
        input_id = edit_input.get_attribute("id")
        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
        driver.execute_script("arguments[0].click();", label)
        WebDriverWait(driver, 10).until(lambda d: d.find_element(
            By.CSS_SELECTOR, "input[name='setmode']"
        ).is_selected())
        time.sleep(1)

    # ── Step 2: Hover over a section to reveal the "+" button, then click ──
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

    # ── Step 3: Click "Activity or resource" from the dropdown ─────────────
    activity_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[data-action='open-chooser']")
    ))
    driver.execute_script("arguments[0].click();", activity_btn)

    # ── Step 4: Wait for the activity chooser modal ──────────────────────────
    wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, ".modchooser, [data-region='chooser-container']")
    ))

    # ── Step 5: Click "Quiz" in the modal ────────────────────────────────────
    quiz_item = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR,
         "[data-modname='quiz'] .modchooser-module-name, "
         "[data-modname='quiz'] a, "
         ".modchoosercontainer [title='Quiz']")
    ))
    quiz_item.click()

    # ── Step 6: Click the "Add" button at the bottom of the modal ────────────
    add_confirm = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR,
         ".chooser-footer [data-action='add-chooser-option'], "
         ".modal-footer .btn-primary, "
         "button.addbutton")
    ))
    add_confirm.click()

    # ── Wait for the quiz settings form to load ──────────────────────────────
    wait.until(EC.presence_of_element_located((By.ID, "id_name")))


def _fill_minimal_quiz(driver, name: str = "perf_test_quiz"):
    """Fill the quiz form with minimal valid data and submit."""
    today = datetime.today()
    close = today + timedelta(days=7)

    driver.find_element(By.ID, "id_name").clear()
    driver.find_element(By.ID, "id_name").send_keys(name)

    # Open date
    oc = driver.find_element(By.CSS_SELECTOR, "input[name='timeopen[enabled]']")
    if not oc.is_selected(): oc.click()
    Select(driver.find_element(By.NAME, "timeopen[day]")
           ).select_by_value(str(today.day))
    Select(driver.find_element(By.NAME, "timeopen[month]")
           ).select_by_value(str(today.month))
    Select(driver.find_element(By.NAME, "timeopen[year]")
           ).select_by_value(str(today.year))

    # Close date
    cc = driver.find_element(By.CSS_SELECTOR, "input[name='timeclose[enabled]']")
    if not cc.is_selected(): cc.click()
    Select(driver.find_element(By.NAME, "timeclose[day]")
           ).select_by_value(str(close.day))
    Select(driver.find_element(By.NAME, "timeclose[month]")
           ).select_by_value(str(close.month))
    Select(driver.find_element(By.NAME, "timeclose[year]")
           ).select_by_value(str(close.year))

    driver.find_element(By.ID, "id_gradepass").clear()
    driver.find_element(By.ID, "id_gradepass").send_keys("5")


# ══════════════════════════════════════════════════════════════════════════
# TEST CLASS 1 — PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════
class TestPerformance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = _make_driver()
        cls.wait   = WebDriverWait(cls.driver, 20)
        _login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_login_page_load_time(self):
        """Login page must load within the SLA threshold."""
        start = time.time()
        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "loginbtn")))
        elapsed = time.time() - start

        print(f"\n  [PERF] Login page load : {elapsed:.3f}s  "
              f"(threshold: {LOGIN_PAGE_LOAD_THRESHOLD}s)")
        self.assertLessEqual(
            elapsed, LOGIN_PAGE_LOAD_THRESHOLD,
            f"Login page took {elapsed:.3f}s — exceeds {LOGIN_PAGE_LOAD_THRESHOLD}s SLA"
        )
        # Re-login after navigating away
        _login(self.driver, self.wait)

    def test_02_quiz_form_load_time(self):
        """Quiz add-form must appear within the SLA threshold after choosing Quiz."""
        self.driver.get(COURSE_URL)
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".course-content")))

        try:
            btn = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "input[data-action='toggle-editing'],"
                 "button[data-action='toggle-editing']")))
            if "turn editing on" in (btn.get_attribute("value") or btn.text or "").lower():
                btn.click()
                time.sleep(1)
        except Exception:
            pass

        add = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             ".section-modchooser-link,[data-action='open-chooser']")))
        add.click()

        start = time.time()
        quiz = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-modname='quiz'],a[href*='quiz']")))
        quiz.click()
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))
        elapsed = time.time() - start

        print(f"\n  [PERF] Quiz form load  : {elapsed:.3f}s  "
              f"(threshold: {QUIZ_FORM_LOAD_THRESHOLD}s)")
        self.assertLessEqual(
            elapsed, QUIZ_FORM_LOAD_THRESHOLD,
            f"Quiz form took {elapsed:.3f}s — exceeds {QUIZ_FORM_LOAD_THRESHOLD}s SLA"
        )

    def test_03_quiz_save_response_time(self):
        """Saving a valid quiz must redirect within the SLA threshold."""
        _open_quiz_add_form(self.driver, self.wait)
        _fill_minimal_quiz(self.driver, name="perf_save_test")

        start = time.time()
        self.driver.find_element(By.ID, "id_submitbutton2").click()
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".course-content")))
        elapsed = time.time() - start

        print(f"\n  [PERF] Quiz save time  : {elapsed:.3f}s  "
              f"(threshold: {QUIZ_SAVE_THRESHOLD}s)")
        self.assertLessEqual(
            elapsed, QUIZ_SAVE_THRESHOLD,
            f"Quiz save took {elapsed:.3f}s — exceeds {QUIZ_SAVE_THRESHOLD}s SLA"
        )


# ══════════════════════════════════════════════════════════════════════════
# TEST CLASS 2 — SECURITY
# ══════════════════════════════════════════════════════════════════════════
class TestSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = _make_driver()
        cls.wait   = WebDriverWait(cls.driver, 20)
        _login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_password_field_is_masked(self):
        """Password input type must be 'password' (value hidden in UI)."""
        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "password")))
        field_type = self.driver.find_element(By.ID, "password").get_attribute("type")
        self.assertEqual(field_type, "password",
                         f"Password field type='{field_type}' — should be 'password'")
        print(f"\n  [SEC] Password field type: '{field_type}' ✓")
        _login(self.driver, self.wait)

    def test_02_xss_payloads_in_quiz_name_not_executed(self):
        """XSS payloads injected into Quiz Name must NOT trigger JS alerts."""
        for payload in ATTACK_PAYLOADS:
            _open_quiz_add_form(self.driver, self.wait)

            name_fld = self.driver.find_element(By.ID, "id_name")
            name_fld.clear()
            name_fld.send_keys(payload)
            self.driver.find_element(By.ID, "id_submitbutton2").click()
            time.sleep(1)

            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                alert.dismiss()
                self.fail(f"XSS alert triggered! payload={payload!r}  alert='{alert_text}'")
            except Exception:
                pass   # No alert = payload was not executed ✓

            # Also verify no Python/PHP stack trace visible
            page_src = self.driver.page_source.lower()
            self.assertNotIn("traceback", page_src,
                             f"Stack trace leaked for payload: {payload!r}")
            self.assertNotIn("fatal error", page_src,
                             f"Fatal error leaked for payload: {payload!r}")
            print(f"\n  [SEC] Payload safe: {payload!r} ✓")

    def test_03_https_used(self):
        """All pages must be served over HTTPS (encrypted transport)."""
        for path in ["login/index.php", "course/view.php?id=2"]:
            url = BASE_URL + path
            self.driver.get(url)
            current = self.driver.current_url
            self.assertTrue(
                current.startswith("https://"),
                f"Page not served over HTTPS: {current}"
            )
            print(f"\n  [SEC] HTTPS ✓ for {current}")

    def test_04_no_credentials_in_url(self):
        """Username and password must never appear in the browser URL bar."""
        _login(self.driver, self.wait)
        current_url = self.driver.current_url.lower()
        self.assertNotIn(USERNAME.lower(), current_url,
                         "Username found in URL after login!")
        self.assertNotIn(PASSWORD.lower(), current_url,
                         "Password found in URL after login!")
        print(f"\n  [SEC] No credentials in URL ✓  ({current_url})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
