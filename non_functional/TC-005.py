"""
NON-FUNCTIONAL TEST FILE 05 — TC-005 ADMIN CREATES A CALENDAR EVENT
                              Compatibility Testing
Feature : Moodle LMS — Calendar month view (event creation entry point)
Site    : https://xuansang1234.moodlecloud.com/calendar/view.php?view=month

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR  COMPATIBILITY TESTING  (Selenium — viewport resizing)
  Tool      : pip install selenium webdriver-manager
  Approach  : Resize the Chrome window to Desktop, Tablet and Mobile
              breakpoints and verify the calendar renders key elements
              without layout overflow at each viewport.
  Run       : python -m pytest TC-005.py -v
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import re
import sys
import time
import time
import unittest

BASE_URL      = "https://xuansang1234.moodlecloud.com"
LOGIN_URL     = BASE_URL + "/login/index.php"
CALENDAR_URL  = BASE_URL + "/calendar/view.php?view=month"
USERNAME      = "sang.truong2005@hcmut.edu.vn"
PASSWORD      = "Abcdxyz12@"

VIEWPORTS = [
    {"name": "Desktop", "width": 1920, "height": 1080},
    {"name": "Tablet",  "width": 768,  "height": 1024},
    {"name": "Mobile",  "width": 375,  "height": 812},
]

CALENDAR_GRID_SELECTOR = (
    ".calendarwrapper, table.calendartable, .calendar-monthly-cell"
)


# ══════════════════════════════════════════════════════════════════════════
# NFR  COMPATIBILITY  — calendar renders correctly at multiple viewports
# ══════════════════════════════════════════════════════════════════════════
class TestCalendarCompatibility(unittest.TestCase):

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
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(service=svc, options=opts)
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

    def _set_viewport(self, width, height):
        """Resize the browser window to achieve the desired inner viewport."""
        chrome_w = self.driver.execute_script(
            "return window.outerWidth - window.innerWidth;"
        )
        chrome_h = self.driver.execute_script(
            "return window.outerHeight - window.innerHeight;"
        )
        self.driver.set_window_size(width + chrome_w, height + chrome_h)

    def test_01_desktop_calendar_renders_key_elements(self):
        """Calendar grid must be visible at 1920×1080 (Desktop)."""
        from selenium.webdriver.common.by import By
        vp = VIEWPORTS[0]
        self._set_viewport(vp["width"], vp["height"])
        self.driver.get(CALENDAR_URL)
        time.sleep(2)
        grid = self.driver.find_elements(By.CSS_SELECTOR, CALENDAR_GRID_SELECTOR)
        self.assertTrue(grid,
                        f"[{vp['name']}] Calendar grid not found "
                        f"({CALENDAR_GRID_SELECTOR})")
        print(f"\n  [COMPAT] {vp['name']} ({vp['width']}×{vp['height']}): "
              f"grid present [OK]")

    def test_02_tablet_calendar_renders_key_elements(self):
        """Calendar grid must be visible at 768×1024 (Tablet)."""
        from selenium.webdriver.common.by import By
        vp = VIEWPORTS[1]
        self._set_viewport(vp["width"], vp["height"])
        self.driver.get(CALENDAR_URL)
        time.sleep(2)
        grid = self.driver.find_elements(By.CSS_SELECTOR, CALENDAR_GRID_SELECTOR)
        self.assertTrue(grid,
                        f"[{vp['name']}] Calendar grid not found "
                        f"({CALENDAR_GRID_SELECTOR})")
        print(f"\n  [COMPAT] {vp['name']} ({vp['width']}×{vp['height']}): "
              f"grid present [OK]")

    def test_03_mobile_calendar_renders_without_crash(self):
        """Calendar page must load at 375×812 (Mobile) without login redirect."""
        from selenium.webdriver.common.by import By
        vp = VIEWPORTS[2]
        self._set_viewport(vp["width"], vp["height"])
        self.driver.get(CALENDAR_URL)
        time.sleep(2)
        body = self.driver.find_elements(By.TAG_NAME, "body")
        self.assertTrue(body, f"[{vp['name']}] Page body missing")
        self.assertNotIn("/login/", self.driver.current_url,
                         f"[{vp['name']}] Redirected to login at mobile viewport")
        print(f"\n  [COMPAT] {vp['name']} ({vp['width']}×{vp['height']}): "
              f"page loaded without crash [OK]")

    def test_04_no_horizontal_overflow_at_tablet_viewport(self):
        """Page must not overflow horizontally at 768×1024 (Tablet)."""
        vp = VIEWPORTS[1]
        self._set_viewport(vp["width"], vp["height"])
        self.driver.get(CALENDAR_URL)
        time.sleep(2)
        scroll_w = self.driver.execute_script(
            "return document.documentElement.scrollWidth;"
        )
        client_w = self.driver.execute_script(
            "return document.documentElement.clientWidth;"
        )
        self.assertLessEqual(scroll_w, client_w + 20,
                             f"[{vp['name']}] Horizontal overflow: "
                             f"scrollWidth={scroll_w} > clientWidth={client_w}")
        print(f"\n  [COMPAT] {vp['name']}: no horizontal overflow "
              f"(scroll={scroll_w}, client={client_w}) [OK]")

    def test_05_no_horizontal_overflow_at_mobile_viewport(self):
        """Page must not overflow horizontally at 375×812 (Mobile)."""
        vp = VIEWPORTS[2]
        self._set_viewport(vp["width"], vp["height"])
        self.driver.get(CALENDAR_URL)
        time.sleep(2)
        scroll_w = self.driver.execute_script(
            "return document.documentElement.scrollWidth;"
        )
        client_w = self.driver.execute_script(
            "return document.documentElement.clientWidth;"
        )
        self.assertLessEqual(scroll_w, client_w + 20,
                             f"[{vp['name']}] Horizontal overflow: "
                             f"scrollWidth={scroll_w} > clientWidth={client_w}")
        print(f"\n  [COMPAT] {vp['name']}: no horizontal overflow "
              f"(scroll={scroll_w}, client={client_w}) [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)

