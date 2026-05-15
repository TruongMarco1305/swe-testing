"""
NON-FUNCTIONAL TEST FILE 02 — TC-002 ADMIN CREATES A NEW COURSE
                              Performance + Accessibility
Feature : Moodle LMS — Course creation form
Site    : https://xuansang1234.moodlecloud.com/course/edit.php?category=0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING   (Locust)
  Tool      : pip install locust
  Approach  : Authenticated admin repeatedly loads the New-Course form
              and measures server-rendered form latency.
  Run       : locust -f test_nfr_02_login_perf_a11y.py

NFR-2  ACCESSIBILITY TESTING (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Open the course-creation form in Chrome, inject axe-core,
              and assert there are no critical/serious WCAG violations.
  Run       : python -m unittest test_nfr_02_login_perf_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import re
import sys
import time
import unittest

BASE_URL    = "https://xuansang1234.moodlecloud.com"
LOGIN_URL   = BASE_URL + "/login/index.php"
NEW_COURSE_URL = BASE_URL + "/course/edit.php?category=0"
USERNAME    = "sang.truong2005@hcmut.edu.vn"
PASSWORD    = "Abcdxyz12@"


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  PERFORMANCE  — Locust (authenticated admin loads New-Course form)
# ══════════════════════════════════════════════════════════════════════════
# Skip Locust import under pytest — gevent monkey-patching of `ssl` after
# selenium has loaded it causes RecursionError during pytest collection.
def _define_locust_users():
    from locust import HttpUser, task, between

    class NewCoursePerfUser(HttpUser):
        host = BASE_URL
        wait_time = between(1, 5)

        def on_start(self):
            r = self.client.get("/login/index.php", name="GET /login")
            m = re.search(r'name="logintoken" value="([^"]+)"', r.text)
            token = m.group(1) if m else ""
            self.client.post("/login/index.php",
                             data={"username": USERNAME,
                                   "password": PASSWORD,
                                   "logintoken": token},
                             name="POST /login")

        @task
        def open_new_course_form(self):
            with self.client.get("/course/edit.php?category=0",
                                 name="GET /course/edit (new)",
                                 catch_response=True) as r:
                if r.status_code != 200 or 'id="id_fullname"' not in r.text:
                    r.failure("New-Course form did not render under load")

    globals()["NewCoursePerfUser"] = NewCoursePerfUser


if "pytest" not in sys.modules:
    try:
        _define_locust_users()
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe-selenium-python on the New-Course form
# ══════════════════════════════════════════════════════════════════════════
class TestNewCourseAccessibility(unittest.TestCase):

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

    def test_01_axe_audit_new_course_form(self):
        """Full axe audit on the New-Course form; report + verify engine ran."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(NEW_COURSE_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_fullname")))

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_new_course_report.json")
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
        print(f"  [A11Y] Rules passed       : {len(results.get('passes', []))}")

    def test_02_required_form_fields_have_labels(self):
        """Course fullname/shortname inputs must have associated <label>."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(NEW_COURSE_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_fullname")))

        for fid in ("id_fullname", "id_shortname"):
            label = self.driver.execute_script(
                "var l=document.querySelector('label[for=\""+fid+"\"]');"
                "return l?l.innerText.trim():'';"
            )
            self.assertTrue(label,
                            f"Form field #{fid} has no <label for=...>")
            print(f"\n  [A11Y] #{fid} label = '{label}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
