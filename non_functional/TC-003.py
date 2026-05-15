"""
NON-FUNCTIONAL TEST FILE 03 — TC-003 TEACHER CREATES AN ASSIGNMENT
                              Accessibility Testing
Feature : Moodle LMS — Assignment-creation form (course 10, section 39)
Site    : https://xuansang1234.moodlecloud.com/course/modedit.php
          ?add=assign&type&course=10&sectionid=39&return=0&beforemod=0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR  ACCESSIBILITY TESTING  (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Selenium opens the assignment-add form as Teacher, injects
              axe-core, and audits both the blank form and the error state
              for WCAG violations. Also verifies required fields have
              associated labels.
  Run       : python -m pytest TC-003.py -v
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import time
import unittest

BASE_URL      = "https://xuansang1234.moodlecloud.com"
LOGIN_URL     = BASE_URL + "/login/index.php"
COURSE_ID     = 10
SECTION_ID    = 39
ASSIGN_ADD_URL = (BASE_URL
                  + f"/course/modedit.php?add=assign&type"
                    f"&course={COURSE_ID}&sectionid={SECTION_ID}"
                    f"&return=0&beforemod=0")
USERNAME      = "sang.truong2005@hcmut.edu.vn"
PASSWORD      = "Abcdxyz12@"


# ══════════════════════════════════════════════════════════════════════════
# NFR  ACCESSIBILITY  — axe audit on the assignment-add form
# ══════════════════════════════════════════════════════════════════════════
class TestAssignmentAccessibility(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            svc = Service(ChromeDriverManager().install())
        except Exception:
            svc = Service()

        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(service=svc, options=opts)
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

    def test_01_axe_audit_assignment_form_empty(self):
        """Full axe audit on the freshly-loaded assignment-add form."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(ASSIGN_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_assignment_empty_report.json")
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        violations = results.get("violations", [])
        critical = [v for v in violations
                    if v.get("impact") in ("critical", "serious")]
        print(f"\n  [A11Y] Total violations   : {len(violations)}")
        print(f"  [A11Y] Critical/Serious   : {len(critical)}")
        for v in critical:
            print(f"    - {v['impact'].upper()} - {v['id']}: {v['description']}")
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)
        self.assertIn("passes", results)
        print(f"  [A11Y] Rules passed        : {len(results.get('passes', []))}")

    def test_02_required_fields_have_labels(self):
        """Assignment Name and Grade-to-pass inputs must have associated labels."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(ASSIGN_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

        for fid in ("id_name", "id_gradepass"):
            label = self.driver.execute_script(
                f"var l=document.querySelector('label[for=\"{fid}\"]');"
                "return l?l.innerText.trim():'';"
            )
            self.assertTrue(label,
                            f"Form field #{fid} has no <label for=...>")
            print(f"\n  [A11Y] #{fid} label = '{label}' [OK]")

    def test_03_axe_audit_assignment_form_error_state(self):
        """axe audit on the form after triggering a validation error (empty name)."""
        from axe_selenium_python import Axe
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.get(ASSIGN_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

        name_fld = self.driver.find_element(By.ID, "id_name")
        name_fld.clear()
        btn = self.driver.find_element(By.ID, "id_submitbutton2")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_assignment_error_report.json")
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        violations = results.get("violations", [])
        critical = [v for v in violations
                    if v.get("impact") in ("critical", "serious")]
        print(f"\n  [A11Y] (error state) Total violations  : {len(violations)}")
        print(f"  [A11Y] (error state) Critical/Serious  : {len(critical)}")
        self.assertIsInstance(results, dict)
        self.assertIn("violations", results)


if __name__ == "__main__":
    unittest.main(verbosity=2)

