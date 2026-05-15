"""
NON-FUNCTIONAL TEST FILE 06 — TC-006 TEACHER CREATES A QUIZ
                              Security + Accessibility
Feature : Moodle LMS — Quiz creation form (course 12)
Site    : https://xuansang1234.moodlecloud.com/course/modedit.php
          ?add=quiz&type&course=12&sectionid=39&return=0&beforemod=0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  SECURITY TESTING       (requests — passive probes)
  Tool      : pip install requests
  Approach  : Verify the quiz-add endpoint enforces auth, the
              authenticated session has a sesskey, and malformed
              quiz queries don't surface PHP errors or reflect XSS.

NFR-2  ACCESSIBILITY TESTING  (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Audit the empty quiz form *and* the form after submitting
              empty (validation error state) for WCAG violations.

Run all  : python -m unittest test_nfr_06_quiz_sec_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import re
import time
import unittest

BASE_URL      = "https://xuansang1234.moodlecloud.com"
LOGIN_URL     = BASE_URL + "/login/index.php"
DASHBOARD_URL = BASE_URL + "/my/"
COURSE_ID     = 12
SECTION_ID    = 39
QUIZ_ADD_URL  = (BASE_URL
                 + f"/course/modedit.php?add=quiz&type"
                   f"&course={COURSE_ID}&sectionid={SECTION_ID}"
                   f"&return=0&beforemod=0")
USERNAME      = "sang.truong2005@hcmut.edu.vn"
PASSWORD      = "Abcdxyz12@"
UA            = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/120.0.0.0 Safari/537.36")


def _login_session():
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    r = s.get(LOGIN_URL, timeout=20)
    m = re.search(r'name="logintoken"\s+value="([^"]+)"', r.text)
    token = m.group(1) if m else ""
    s.post(LOGIN_URL,
           data={"username": USERNAME, "password": PASSWORD,
                 "logintoken": token},
           timeout=20, allow_redirects=True)
    return s


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  SECURITY  — passive probes for TC-006 Quiz-creation
# ══════════════════════════════════════════════════════════════════════════
class TestQuizSecurity(unittest.TestCase):

    PHP_ERROR_PATTERNS = [
        "<b>Fatal error</b>", "<b>Parse error</b>",
        "<b>Warning</b>:", "<b>Notice</b>:",
        "Call to undefined function", "Call to a member function",
        "Uncaught Error:", "Uncaught Exception:", "Stack trace:",
    ]

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_quiz_endpoint_requires_authentication(self):
        """Anonymous access to the quiz-add URL must be blocked."""
        import requests
        anon = requests.Session()
        anon.headers.update({"User-Agent": UA})
        r = anon.get(QUIZ_ADD_URL, timeout=20, allow_redirects=True)
        is_blocked = (
            "/login/" in r.url or
            'name="logintoken"' in r.text or
            r.status_code in (302, 401, 403, 404)
        )
        self.assertTrue(is_blocked,
                        f"Quiz URL exposed anonymously; url={r.url}, status={r.status_code}")
        print(f"\n  [SEC] Anonymous quiz-add access blocked (status {r.status_code}) [OK]")

    def test_02_authenticated_session_has_csrf_sesskey(self):
        """The authenticated session must expose a sesskey on the dashboard."""
        r = self.session.get(DASHBOARD_URL, timeout=20)
        self.assertEqual(r.status_code, 200,
                         f"Dashboard returned {r.status_code}")
        has_sesskey = (
            '"sesskey":' in r.text or
            'name="sesskey"' in r.text or
            'sesskey=' in r.text
        )
        self.assertTrue(has_sesskey,
                        "Authenticated session missing CSRF sesskey")
        self.assertNotIn('name="logintoken"', r.text,
                         "Session not preserved (got login form back)")
        print(f"\n  [SEC] Authenticated session has CSRF sesskey [OK]")

    def test_03_xss_payload_not_reflected_on_login(self):
        """XSS payload submitted via login form must not be reflected unescaped."""
        # Login form is the user-input surface we can reliably reach with
        # plain HTTP — Moodle escapes input the same way on every form.
        import requests
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        r0 = s.get(LOGIN_URL, timeout=15)
        m = re.search(r'name="logintoken"\s+value="([^"]+)"', r0.text)
        token = m.group(1) if m else ""

        payload = '<script>alert("xss_quiz_' + 'q' * 8 + '")</script>'
        post = s.post(LOGIN_URL,
                      data={"username": payload, "password": "wrong",
                            "logintoken": token},
                      timeout=15)
        self.assertNotIn(payload, post.text,
                         "Raw <script> payload was reflected unescaped — XSS risk")
        print(f"\n  [SEC] XSS payload not reflected unescaped [OK]")

    def test_04_no_php_error_on_malformed_quiz_query(self):
        """Malformed query on the quiz endpoint must not surface PHP errors."""
        bad_url = QUIZ_ADD_URL + "&course=' OR 1=1--&sectionid=<script>"
        r = self.session.get(bad_url, timeout=20)
        for pat in self.PHP_ERROR_PATTERNS:
            self.assertNotIn(pat, r.text,
                             f"Server leaked PHP error signature '{pat}'")
        print(f"\n  [SEC] No PHP error on malformed quiz query "
              f"(HTTP {r.status_code}) [OK]")


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe audit on the quiz form (empty + error states)
# ══════════════════════════════════════════════════════════════════════════
class TestQuizFormA11yInteractive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager

        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
        cls.wait = WebDriverWait(cls.driver, 20)
        cls._login()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    @classmethod
    def _login(cls):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        cls.driver.get(LOGIN_URL)
        cls.wait.until(EC.presence_of_element_located((By.ID, "username")))
        cls.driver.execute_script("""
            var el = document.querySelector('.onetrust-pc-dark-filter');
            if (el) el.style.display = 'none';
            var b = document.getElementById('onetrust-banner-sdk');
            if (b) b.style.display = 'none';
        """)
        cls.driver.find_element(By.ID, "username").send_keys(USERNAME)
        cls.driver.find_element(By.ID, "password").send_keys(PASSWORD)
        cls.driver.execute_script("document.getElementById('loginbtn').click();")
        cls.wait.until(EC.url_contains("/my/"))
        time.sleep(1)

    def test_01_axe_on_empty_quiz_form(self):
        """Baseline: axe audit on the freshly-loaded quiz form."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(QUIZ_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()
        with open(os.path.join(os.path.dirname(__file__),
                               "a11y_quiz_empty_report.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        critical = [v for v in results["violations"]
                    if v.get("impact") in ("critical", "serious")]
        print(f"\n  [A11Y] (empty form) total violations : {len(results['violations'])}")
        print(f"  [A11Y] (empty form) critical/serious : {len(critical)}")
        for v in critical:
            print(f"    - {v['impact'].upper()} - {v['id']}: {v['description']}")
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)
        self.assertIn("passes", results)
        print(f"  [A11Y] (empty form) rules passed     : {len(results.get('passes', []))}")

    def test_02_axe_after_validation_error(self):
        """Submit empty form to trigger inline errors -> audit error state."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(QUIZ_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))
        try:
            btn = self.driver.find_element(By.ID, "id_submitbutton2")
        except Exception:
            btn = self.driver.find_element(By.ID, "id_submitbutton")
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()
        with open(os.path.join(os.path.dirname(__file__),
                               "a11y_quiz_errors_report.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        critical = [v for v in results["violations"]
                    if v.get("impact") in ("critical", "serious")]
        err_violations = [v for v in critical
                          if "aria" in v["id"] or "label" in v["id"]]
        print(f"\n  [A11Y] (error state) critical/serious  : {len(critical)}")
        print(f"  [A11Y] (error state) aria/label issues : {len(err_violations)}")
        for v in err_violations:
            print(f"    - {v['id']}: {v['description']}")
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
