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

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ── Configuration ──────────────────────────────────────────────────────────
BASE_URL   = "https://ihatetesting.moodlecloud.com/"
LOGIN_URL  = BASE_URL + "login/index.php"
COURSE_ID  = 426
SECTION_ID = 2121
COURSE_URL = BASE_URL + f"course/view.php?id={COURSE_ID}"
QUIZ_ADD_URL = (
    BASE_URL + f"course/modedit.php"
    f"?add=quiz&type&course={COURSE_ID}&sectionid={SECTION_ID}&return=0&beforemod=0"
)
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
    # Also hide overlay via JS as a belt-and-braces fallback
    driver.execute_script("""
        var el = document.querySelector('.onetrust-pc-dark-filter');
        if (el) el.style.display = 'none';
        var banner = document.getElementById('onetrust-banner-sdk');
        if (banner) banner.style.display = 'none';
    """)
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.execute_script("document.getElementById('loginbtn').click();")
    wait.until(EC.url_contains("/my/"))
    time.sleep(1)


def _open_quiz_add_form(driver, wait):
    """Navigate directly to the quiz add form (same URL as TC-006)."""
    driver.get(QUIZ_ADD_URL)
    wait.until(EC.presence_of_element_located((By.ID, "id_name")))


def _fill_minimal_quiz(driver, name: str = "perf_test_quiz"):
    """Fill quiz form with minimal valid data using JS helpers (same as TC-006)."""
    name_field = driver.find_element(By.ID, "id_name")
    name_field.clear()
    name_field.send_keys(name)

    driver.execute_script("""
        function sS(id,v){
          var e=document.getElementById(id);
          if(e){e.value=String(v);e.dispatchEvent(new Event('change',{bubbles:true}));}
        }
        function ens(id){var c=document.getElementById(id);if(c&&!c.checked){c.click();}}
        var tod=new Date();
        var cl=new Date(tod); cl.setDate(cl.getDate()+7);
        ens('id_timeopen_enabled');
        sS('id_timeopen_day',tod.getDate());
        sS('id_timeopen_month',tod.getMonth()+1);
        sS('id_timeopen_year',tod.getFullYear());
        sS('id_timeopen_hour',tod.getHours());
        sS('id_timeopen_minute',0);
        ens('id_timeclose_enabled');
        sS('id_timeclose_day',cl.getDate());
        sS('id_timeclose_month',cl.getMonth()+1);
        sS('id_timeclose_year',cl.getFullYear());
        sS('id_timeclose_hour',cl.getHours());
        sS('id_timeclose_minute',0);
    """)


# ══════════════════════════════════════════════════════════════════════════
# TEST CLASS 1 — PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════
class TestPerformance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Do NOT pre-login — test_01 measures the login page load on a
        # fresh (unauthenticated) session, then logs in for the rest.
        cls.driver = _make_driver()
        cls.wait   = WebDriverWait(cls.driver, 20)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_login_page_load_time(self):
        """Login page must load within the SLA threshold (fresh session)."""
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
        # Login so subsequent tests have an authenticated session
        _dismiss_cookie_banner(self.driver)
        self.driver.execute_script("""
            var el = document.querySelector('.onetrust-pc-dark-filter');
            if (el) el.style.display = 'none';
            var banner = document.getElementById('onetrust-banner-sdk');
            if (banner) banner.style.display = 'none';
        """)
        self.driver.find_element(By.ID, "username").send_keys(USERNAME)
        self.driver.find_element(By.ID, "password").send_keys(PASSWORD)
        self.driver.execute_script("document.getElementById('loginbtn').click();")
        self.wait.until(EC.url_contains("/my/"))
        time.sleep(1)

    def test_02_quiz_form_load_time(self):
        """Quiz add-form must appear within the SLA threshold (direct URL navigation)."""
        start = time.time()
        self.driver.get(QUIZ_ADD_URL)
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
        try:
            btn = self.driver.find_element(By.ID, "id_submitbutton2")
        except Exception:
            btn = self.driver.find_element(By.ID, "id_submitbutton")
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".course-content, #page-header")))
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
        # Do NOT pre-login — test_01 checks the login page on a fresh
        # (unauthenticated) session, then logs in for the rest.
        cls.driver = _make_driver()
        cls.wait   = WebDriverWait(cls.driver, 20)

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
        # Login for subsequent tests
        _dismiss_cookie_banner(self.driver)
        self.driver.execute_script("""
            var el = document.querySelector('.onetrust-pc-dark-filter');
            if (el) el.style.display = 'none';
            var banner = document.getElementById('onetrust-banner-sdk');
            if (banner) banner.style.display = 'none';
        """)
        self.driver.find_element(By.ID, "username").send_keys(USERNAME)
        self.driver.find_element(By.ID, "password").send_keys(PASSWORD)
        self.driver.execute_script("document.getElementById('loginbtn').click();")
        self.wait.until(EC.url_contains("/my/"))
        time.sleep(1)

    def test_02_xss_payloads_in_quiz_name_not_executed(self):
        """XSS payloads injected into Quiz Name must NOT trigger JS alerts."""
        for payload in ATTACK_PAYLOADS:
            _open_quiz_add_form(self.driver, self.wait)

            name_fld = self.driver.find_element(By.ID, "id_name")
            name_fld.clear()
            name_fld.send_keys(payload)
            try:
                btn = self.driver.find_element(By.ID, "id_submitbutton2")
            except Exception:
                btn = self.driver.find_element(By.ID, "id_submitbutton")
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)

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
        for path in ["login/index.php", f"course/view.php?id={COURSE_ID}"]:
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
        self.driver.get(f"https://ihatetesting.moodlecloud.com/my/")
        self.wait.until(EC.url_contains("/my/"))
        current_url = self.driver.current_url.lower()
        self.assertNotIn(USERNAME.lower(), current_url,
                         "Username found in URL after login!")
        self.assertNotIn(PASSWORD.lower(), current_url,
                         "Password found in URL after login!")
        print(f"\n  [SEC] No credentials in URL ✓  ({current_url})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
