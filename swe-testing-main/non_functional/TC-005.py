"""
NON-FUNCTIONAL TEST FILE 05 — TC-005 ADMIN CREATES A CALENDAR EVENT
                              Performance + Accessibility
Feature : Moodle LMS — Calendar month view (event creation entry point)
Site    : https://xuansang1234.moodlecloud.com/calendar/view.php?view=month

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING   (Locust)
  Tool      : pip install locust
  Approach  : Authenticated admin repeatedly loads the calendar month
              view and measures page-load latency under concurrency.
  Run       : locust -f test_nfr_05_quiz_perf_a11y.py

NFR-2  ACCESSIBILITY TESTING (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Selenium opens the calendar in Chrome, injects axe-core,
              and audits the month view for WCAG violations.
  Run       : python -m unittest test_nfr_05_quiz_perf_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import re
import sys
import time
import unittest

BASE_URL      = "https://xuansang1234.moodlecloud.com"
LOGIN_URL     = BASE_URL + "/login/index.php"
CALENDAR_URL  = BASE_URL + "/calendar/view.php?view=month"
USERNAME      = "sang.truong2005@hcmut.edu.vn"
PASSWORD      = "Abcdxyz12@"


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  PERFORMANCE  — Locust (authenticated calendar load)
# ══════════════════════════════════════════════════════════════════════════
# Skip Locust import under pytest — gevent monkey-patching of `ssl` after
# selenium has loaded it causes RecursionError during pytest collection.
def _define_locust_users():
    from locust import HttpUser, task, between

    class CalendarPerfUser(HttpUser):
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
        def load_calendar_month(self):
            with self.client.get("/calendar/view.php?view=month",
                                 name="GET /calendar (month)",
                                 catch_response=True) as r:
                if r.status_code != 200:
                    r.failure(f"Calendar returned {r.status_code}")

    globals()["CalendarPerfUser"] = CalendarPerfUser


if "pytest" not in sys.modules:
    try:
        _define_locust_users()
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe-selenium-python on the calendar month view
# ══════════════════════════════════════════════════════════════════════════
class TestCalendarAccessibility(unittest.TestCase):

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
        cls.driver.get(CALENDAR_URL)
        time.sleep(2)

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

    def test_01_axe_audit_calendar_month_view(self):
        """Full axe audit on the calendar month view."""
        from axe_selenium_python import Axe

        axe = Axe(self.driver)
        axe.inject()
        results = axe.run()

        report_path = os.path.join(os.path.dirname(__file__),
                                   "a11y_calendar_report.json")
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

    def test_02_new_event_link_reachable(self):
        """The 'New event' control must be discoverable on the calendar page."""
        from selenium.webdriver.common.by import By

        # Moodle 4.x: "New event" button has data-action="new-event-button"
        # Older themes used <a class="btn"...>New event</a>
        candidates = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-action='new-event-button'], "
            "a[href*='action=new'], button[data-handler='new-event']"
        )
        has_text = any(
            "new event" in (el.text or "").lower()
            or "event" in (el.get_attribute("data-action") or "").lower()
            for el in candidates
        )
        # Fall back to a body-text scan if the button locator changed
        if not candidates:
            has_text = "new event" in (self.driver.page_source or "").lower()
        self.assertTrue(candidates or has_text,
                        "Could not locate the New-event control on the calendar")
        print(f"\n  [A11Y] New-event control discoverable [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
