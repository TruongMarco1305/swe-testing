"""
NON-FUNCTIONAL TEST FILE 02 — LOGIN: PERFORMANCE + ACCESSIBILITY
Feature : Moodle LMS — Login page
Site    : https://ihatetesting.moodlecloud.com/login/index.php

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING   (Locust)
  Tool      : pip install locust
  Approach  : N virtual users repeatedly load the login page; we track
              response-time distribution and failure rate.
  Run       : locust -f test_nfr_02_login_perf_a11y.py

NFR-2  ACCESSIBILITY TESTING (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Open the login page in Selenium, inject axe-core, and assert
              there are no WCAG violations of "serious" or "critical" impact.
  Run       : python -m unittest test_nfr_02_login_perf_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import unittest

BASE_URL  = "https://ihatetesting.moodlecloud.com"
LOGIN_URL = BASE_URL + "/login/index.php"


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  PERFORMANCE  — Locust HttpUser
# ══════════════════════════════════════════════════════════════════════════
try:
    from locust import HttpUser, task, between

    class LoginA11yPerfUser(HttpUser):
        host = BASE_URL
        wait_time = between(1, 5)

        @task
        def open_login(self):
            with self.client.get("/login/index.php",
                                 name="GET /login",
                                 catch_response=True) as r:
                if r.status_code != 200 or "loginbtn" not in r.text:
                    r.failure("Login page degraded under load")
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe-selenium-python
# ══════════════════════════════════════════════════════════════════════════
class TestLoginAccessibility(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_axe_no_critical_violations_on_login(self):
        """axe-core must report no critical/serious WCAG violations."""
        from axe_selenium_python import Axe

        self.driver.get(LOGIN_URL)
        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        violations = results.get("violations", [])
        critical = [v for v in violations
                    if v.get("impact") in ("critical", "serious")]

        # Persist full report for the QA evidence pack
        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_login_report.json")
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        print(f"\n  [A11Y] Total violations  : {len(violations)}")
        print(f"  [A11Y] Critical/Serious  : {len(critical)}")
        for v in critical:
            print(f"    ✗ {v['impact'].upper()} — {v['id']}: {v['description']}")

        self.assertEqual(len(critical), 0,
                         f"{len(critical)} critical/serious a11y violations on login")

    def test_02_login_inputs_have_labels(self):
        """Both username and password inputs must have an accessible name."""
        from selenium.webdriver.common.by import By

        self.driver.get(LOGIN_URL)
        for field_id in ("username", "password"):
            el = self.driver.find_element(By.ID, field_id)
            label = (el.get_attribute("aria-label")
                     or self.driver.execute_script(
                        "var l=document.querySelector('label[for=\""+field_id+"\"]');"
                        "return l?l.innerText.trim():'';"))
            self.assertTrue(label,
                            f"Input #{field_id} has no accessible label")
            print(f"\n  [A11Y] #{field_id} label = '{label}' ✓")


if __name__ == "__main__":
    unittest.main(verbosity=2)
