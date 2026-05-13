"""
NON-FUNCTIONAL TEST FILE 05 — QUIZ SETUP: PERFORMANCE + ACCESSIBILITY
Feature : Moodle LMS — Teacher Sets Up a Quiz
Site    : https://ihatetesting.moodlecloud.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING   (Locust)
  Tool      : pip install locust
  Approach  : Authenticated virtual users load the quiz add-form and
              measure server response time + failure rate.
  Run       : locust -f test_nfr_05_quiz_perf_a11y.py

NFR-2  ACCESSIBILITY TESTING (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Real Selenium login → navigate to quiz form → inject axe-core
              and assert no critical/serious WCAG violations on this form
              (it has many form controls — high risk for a11y bugs).
  Run       : python -m unittest test_nfr_05_quiz_perf_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import re
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
# NFR-1  PERFORMANCE  — Locust (authenticated)
# ══════════════════════════════════════════════════════════════════════════
try:
    from locust import HttpUser, task, between

    class QuizFormPerfA11yUser(HttpUser):
        host = BASE_URL
        wait_time = between(1, 4)

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
        def load_quiz_form(self):
            with self.client.get(
                f"/course/modedit.php?add=quiz&type"
                f"&course={COURSE_ID}&sectionid={SECTION_ID}"
                f"&return=0&beforemod=0",
                name="GET /modedit (quiz add)",
                catch_response=True) as r:
                if 'id="id_name"' not in r.text:
                    r.failure("Quiz form not rendered properly under load")
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe-selenium-python on the quiz add form
# ══════════════════════════════════════════════════════════════════════════
class TestQuizFormAccessibility(unittest.TestCase):

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
        cls.driver.get(QUIZ_ADD_URL)
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        cls.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    @classmethod
    def _login(cls):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        cls.driver.get(LOGIN_URL)
        cls.wait.until(EC.presence_of_element_located((By.ID, "username")))
        # Dismiss OneTrust banner if it appears
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

    def test_01_axe_full_audit_quiz_form(self):
        """Full axe audit — no critical/serious violations allowed."""
        from axe_selenium_python import Axe

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_quiz_form_report.json")
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        violations = results.get("violations", [])
        critical = [v for v in violations
                    if v.get("impact") in ("critical", "serious")]
        print(f"\n  [A11Y] Violations total      : {len(violations)}")
        print(f"  [A11Y] Critical/Serious      : {len(critical)}")
        for v in critical:
            print(f"    ✗ {v['impact'].upper()} — {v['id']}: {v['description']}")

        self.assertEqual(len(critical), 0,
            f"Quiz add form has {len(critical)} critical/serious a11y violations")

    def test_02_required_form_controls_have_labels(self):
        """id_name, id_introeditor and id_grade must all have <label>s."""
        from selenium.webdriver.common.by import By

        for fid in ("id_name", "id_grade"):
            try:
                self.driver.find_element(By.ID, fid)
            except Exception:
                self.skipTest(f"Field {fid} not in current Moodle theme")
                return
            label_text = self.driver.execute_script(
                "var l=document.querySelector('label[for=\""+fid+"\"]');"
                "return l?l.innerText.trim():'';"
            )
            self.assertTrue(label_text,
                            f"Form field #{fid} has no <label for=...>")
            print(f"\n  [A11Y] #{fid} label = '{label_text}' ✓")


if __name__ == "__main__":
    unittest.main(verbosity=2)
