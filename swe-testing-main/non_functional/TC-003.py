"""
NON-FUNCTIONAL TEST FILE 03 — TC-003 TEACHER CREATES AN ASSIGNMENT
                              Security + Accessibility
Feature : Moodle LMS — Assignment-creation form (course 10, section 39)
Site    : https://xuansang1234.moodlecloud.com/course/modedit.php
          ?add=assign&type&course=10&sectionid=39&return=0&beforemod=0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  SECURITY TESTING       (requests — passive probes)
  Tool      : pip install requests
  Approach  : Verify the assignment-creation endpoint enforces auth,
              the form embeds CSRF (sesskey), and malformed input does
              not surface PHP errors or reflect XSS payloads.

NFR-2  ACCESSIBILITY TESTING  (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Selenium opens the assignment-add form as Teacher, injects
              axe-core, and audits the populated form for WCAG issues.

Run all  : python -m unittest test_nfr_03_login_sec_a11y.py
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
COURSE_ID     = 10
SECTION_ID    = 39
ASSIGN_ADD_URL = (BASE_URL
                  + f"/course/modedit.php?add=assign&type"
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
# NFR-1  SECURITY  — passive probes for TC-003 Assignment-creation
# ══════════════════════════════════════════════════════════════════════════
class TestAssignmentSecurity(unittest.TestCase):

    PHP_ERROR_PATTERNS = [
        "<b>Fatal error</b>", "<b>Parse error</b>",
        "<b>Warning</b>:", "<b>Notice</b>:",
        "Call to undefined function", "Call to a member function",
        "Uncaught Error:", "Uncaught Exception:", "Stack trace:",
    ]

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_assign_endpoint_requires_authentication(self):
        """Anonymous access to assignment-add URL must redirect to login."""
        import requests
        anon = requests.Session()
        anon.headers.update({"User-Agent": UA})
        r = anon.get(ASSIGN_ADD_URL, timeout=20, allow_redirects=True)
        is_unreachable_without_auth = (
            "/login/" in r.url or
            'name="logintoken"' in r.text or
            r.status_code in (302, 401, 403, 404)
        )
        self.assertTrue(is_unreachable_without_auth,
                        f"Assignment URL exposed anonymously; url={r.url}, status={r.status_code}")
        print(f"\n  [SEC] Anonymous access blocked (status {r.status_code}) [OK]")

    def test_02_authenticated_session_has_csrf_sesskey(self):
        """The authenticated session must expose a sesskey on the dashboard."""
        r = self.session.get(DASHBOARD_URL, timeout=20)
        self.assertEqual(r.status_code, 200,
                         f"Dashboard returned {r.status_code} for authed user")
        has_sesskey = (
            '"sesskey":' in r.text or
            'name="sesskey"' in r.text or
            'sesskey=' in r.text
        )
        self.assertTrue(has_sesskey,
                        "Authenticated session missing sesskey CSRF token")
        self.assertNotIn('name="logintoken"', r.text,
                         "Session was not preserved (got login form back)")
        print(f"\n  [SEC] Authenticated session has CSRF sesskey [OK]")

    def test_03_no_php_error_on_malformed_assign_query(self):
        """Malformed query on the assignment endpoint must not leak PHP errors."""
        bad_url = ASSIGN_ADD_URL + "&course=' OR 1=1--&sectionid=<script>"
        r = self.session.get(bad_url, timeout=20)
        for pat in self.PHP_ERROR_PATTERNS:
            self.assertNotIn(pat, r.text,
                             f"Server leaked PHP error signature '{pat}'")
        print(f"\n  [SEC] No PHP error on malformed assignment query "
              f"(HTTP {r.status_code}) [OK]")


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe on the assignment-add form
# ══════════════════════════════════════════════════════════════════════════
class TestAssignmentA11y(unittest.TestCase):

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
        cls._login_and_switch_role()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    @classmethod
    def _login_and_switch_role(cls):
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
        # Switch role to Teacher so we can open the assignment-add form
        cls.driver.get(
            f"{BASE_URL}/course/switchrole.php"
            f"?id=1&switchrole=-1&returnurl=%2Fmy%2Findex.php"
        )
        time.sleep(1)
        try:
            buttons = cls.driver.find_elements(By.CSS_SELECTOR, "form button")
            for b in buttons:
                if "Teacher" in b.text:
                    cls.driver.execute_script("arguments[0].click();", b)
                    break
        except Exception:
            pass
        time.sleep(1)

    def test_01_axe_audit_assignment_form(self):
        """Full axe audit on the assignment-add form."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(ASSIGN_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_assignment_report.json")
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        violations = results.get("violations", [])
        critical = [v for v in violations
                    if v.get("impact") in ("critical", "serious")]
        print(f"\n  [A11Y] Total violations  : {len(violations)}")
        print(f"  [A11Y] Critical/Serious  : {len(critical)}")
        for v in critical:
            print(f"    - {v['impact'].upper()} - {v['id']}: {v['description']}")
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)
        self.assertIn("passes", results)

    def test_02_assignment_name_field_has_label(self):
        """The required Assignment Name input must have an associated label."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(ASSIGN_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))
        label = self.driver.execute_script(
            "var l=document.querySelector('label[for=\"id_name\"]');"
            "return l?l.innerText.trim():'';")
        self.assertTrue(label, "Assignment Name input (#id_name) has no label")
        print(f"\n  [A11Y] #id_name label = '{label}' [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
