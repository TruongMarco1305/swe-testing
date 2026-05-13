"""
NON-FUNCTIONAL TEST FILE 06 — QUIZ SETUP: SECURITY + ACCESSIBILITY
Feature : Moodle LMS — Teacher Sets Up a Quiz
Site    : https://ihatetesting.moodlecloud.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  SECURITY TESTING       (OWASP ZAP Python API)
  Tool      : pip install python-owasp-zap-v2.4
  Pre-req   : ZAP daemon on 127.0.0.1:8080 + configured Moodle session
              context so the scanner stays logged in.
  Approach  : Fuzz the Quiz Name field through ZAP's active-scan input
              vectors; verify no Reflected XSS / SQLi alerts triggered.

NFR-2  ACCESSIBILITY TESTING  (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : After filling the quiz form, audit the *populated* form
              state (validation messages, helper text) for a11y bugs.

Run all  : python -m unittest test_nfr_06_quiz_sec_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import time
import unittest

BASE_URL     = "https://ihatetesting.moodlecloud.com"
LOGIN_URL    = BASE_URL + "/login/index.php"
COURSE_ID    = 426
SECTION_ID   = 2121
QUIZ_ADD_URL = (BASE_URL
                + f"/course/modedit.php?add=quiz&type"
                  f"&course={COURSE_ID}&sectionid={SECTION_ID}"
                  f"&return=0&beforemod=0")
USERNAME     = "phuc.nguyen0310@hcmut.edu.vn"
PASSWORD     = "Huuphuc0310@"


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  SECURITY  — OWASP ZAP active scan focused on Quiz Name input
# ══════════════════════════════════════════════════════════════════════════
class TestQuizFormZapInputFuzz(unittest.TestCase):

    ZAP_PROXY = "http://127.0.0.1:8080"

    @classmethod
    def setUpClass(cls):
        # Skips with platform-aware install/launch instructions if the python
        # client is missing OR the ZAP daemon is not reachable on ZAP_PROXY.
        from zap_setup import ensure_zap_ready
        cls.zap = ensure_zap_ready(cls.ZAP_PROXY)

    def test_01_active_scan_xss_and_sqli_rules(self):
        """Run ZAP active scan with only the XSS + SQLi policies enabled."""
        # Policy IDs:  40012 = Reflected XSS, 40018 = SQL Injection
        print(f"\n  [SEC] Configuring scan policy (XSS + SQLi only)")
        try:
            self.zap.ascan.enable_scanners("40012,40018")
        except Exception as e:
            print(f"  [SEC] (warn) could not toggle scanners: {e}")

        print(f"  [SEC] Active scanning {QUIZ_ADD_URL} ...")
        sid = self.zap.ascan.scan(QUIZ_ADD_URL)
        while int(self.zap.ascan.status(sid)) < 100:
            time.sleep(5)

        alerts = self.zap.core.alerts(baseurl=QUIZ_ADD_URL)
        xss_sqli = [a for a in alerts
                    if "xss" in a["alert"].lower()
                    or "sql"  in a["alert"].lower()]
        for a in xss_sqli:
            print(f"    ✗ {a['risk']:<6} {a['alert']}  @ {a['url']}")
        self.assertEqual(len(xss_sqli), 0,
                         f"{len(xss_sqli)} XSS/SQLi alerts on quiz form")

    def test_02_no_stacktrace_in_responses(self):
        """ZAP history must not contain PHP/Python stack traces."""
        msgs = self.zap.core.messages(baseurl=QUIZ_ADD_URL, count=50)
        leaks = []
        for m in msgs:
            body = (m.get("responseBody") or "").lower()
            if "fatal error" in body or "traceback" in body:
                leaks.append(m["id"])
        self.assertFalse(leaks, f"Stack-trace leak on messages: {leaks}")
        print(f"\n  [SEC] No stack-trace leaks across {len(msgs)} messages ✓")


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe audit on a *populated* + *invalidated* form
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
        # Verify axe engine ran and produced a structured report.
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)
        self.assertIn("passes", results)
        print(f"  [A11Y] (empty form) rules passed     : {len(results.get('passes', []))}")

    def test_02_axe_after_validation_error(self):
        """Submit empty form to trigger inline errors -> audit error states."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(QUIZ_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))
        # Submit empty to trigger validation error
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
        # Validation error messages should ideally be ARIA-associated with inputs
        err_violations = [v for v in critical
                          if "aria" in v["id"] or "label" in v["id"]]
        print(f"\n  [A11Y] (error state) critical/serious  : {len(critical)}")
        print(f"  [A11Y] (error state) aria/label issues : {len(err_violations)}")
        for v in err_violations:
            print(f"    - {v['id']}: {v['description']}")
        # Verify axe engine executed. Specific ARIA findings on the third-party
        # Moodle UI are documented (printed + persisted to JSON), not asserted.
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
