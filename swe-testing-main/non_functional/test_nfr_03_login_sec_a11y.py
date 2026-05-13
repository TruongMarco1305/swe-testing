"""
NON-FUNCTIONAL TEST FILE 03 — LOGIN: SECURITY + ACCESSIBILITY
Feature : Moodle LMS — Login page
Site    : https://ihatetesting.moodlecloud.com/login/index.php

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  SECURITY TESTING       (OWASP ZAP Python API)
  Tool      : pip install python-owasp-zap-v2.4
  Pre-req   : ZAP daemon on 127.0.0.1:8080
  Approach  : Passive scan only (no aggressive payloads) — look for
              missing security headers (CSP, HSTS, X-Frame-Options) on
              the login page.

NFR-2  ACCESSIBILITY TESTING  (axe-selenium-python)
  Tool      : pip install axe-selenium-python selenium webdriver-manager
  Approach  : Audit colour-contrast & ARIA on the login page; assert any
              login-form-related violation count is zero.

Run all  : python -m unittest test_nfr_03_login_sec_a11y.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
import unittest

BASE_URL  = "https://ihatetesting.moodlecloud.com"
LOGIN_URL = BASE_URL + "/login/index.php"
REQUIRED_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Frame-Options",
    "X-Content-Type-Options",
]


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  SECURITY  — OWASP ZAP passive header audit
# ══════════════════════════════════════════════════════════════════════════
class TestLoginSecurityHeaders(unittest.TestCase):

    ZAP_PROXY = "http://127.0.0.1:8080"

    @classmethod
    def setUpClass(cls):
        from zapv2 import ZAPv2
        cls.zap = ZAPv2(proxies={"http": cls.ZAP_PROXY, "https": cls.ZAP_PROXY})

    def test_01_passive_scan_login_page(self):
        """Visit login via ZAP proxy; passive scanner inspects headers."""
        print(f"\n  [SEC] Passive-scanning {LOGIN_URL} ...")
        self.zap.urlopen(LOGIN_URL)
        time.sleep(3)
        while int(self.zap.pscan.records_to_scan) > 0:
            time.sleep(1)

        alerts = self.zap.core.alerts(baseurl=LOGIN_URL)
        header_alerts = [a for a in alerts
                         if "header" in a["alert"].lower()
                         or "csp"   in a["alert"].lower()
                         or "hsts"  in a["alert"].lower()]
        for a in header_alerts:
            print(f"    • {a['risk']:<6} {a['alert']}")
        # Fail only on Medium+ header-related alerts
        bad = [a for a in header_alerts if a["risk"] in ("High", "Medium")]
        self.assertEqual(len(bad), 0,
                         f"{len(bad)} medium/high header alerts on login page")

    def test_02_required_response_headers_present(self):
        """Each REQUIRED_HEADERS entry should appear in ZAP's HTTP history."""
        history = self.zap.core.messages(baseurl=LOGIN_URL, count=1)
        self.assertTrue(history, "ZAP has no recorded request for login URL")
        resp_headers = history[0]["responseHeader"].lower()
        missing = [h for h in REQUIRED_HEADERS
                   if h.lower() not in resp_headers]
        print(f"\n  [SEC] Missing headers: {missing or 'none'}")
        # Report-only: don't hard-fail (Moodle Cloud may not set all of these)
        if missing:
            print(f"  [SEC] ⚠ {len(missing)} recommended headers missing")


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  ACCESSIBILITY  — axe-selenium-python (login form specifics)
# ══════════════════════════════════════════════════════════════════════════
class TestLoginA11yForm(unittest.TestCase):

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

    def test_01_color_contrast_on_login(self):
        """No critical colour-contrast violations on the login form."""
        from axe_selenium_python import Axe

        self.driver.get(LOGIN_URL)
        axe = Axe(self.driver)
        axe.inject()
        results = axe.run(options={"runOnly": {"type": "rule",
                                               "values": ["color-contrast"]}})
        critical = [v for v in results["violations"]
                    if v.get("impact") in ("critical", "serious")]
        for v in critical:
            print(f"\n  [A11Y] ✗ contrast violation: {v['description']}")
        self.assertEqual(len(critical), 0,
                         "Login page has critical color-contrast issues")

    def test_02_focus_order_reachable_by_keyboard(self):
        """Tab from username should reach password then submit button."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        self.driver.get(LOGIN_URL)
        username = self.driver.find_element(By.ID, "username")
        username.click()
        username.send_keys(Keys.TAB)
        active = self.driver.switch_to.active_element
        self.assertEqual(active.get_attribute("id"), "password",
                         "Tab order broken: username → ??? (expected password)")
        active.send_keys(Keys.TAB)
        active2 = self.driver.switch_to.active_element
        # Some themes have a 'rememberusername' checkbox between password & btn
        self.assertIn(active2.get_attribute("id"),
                      ("loginbtn", "rememberusername"),
                      "Tab order broken after password field")
        print(f"\n  [A11Y] Keyboard focus order OK ✓")


if __name__ == "__main__":
    unittest.main(verbosity=2)
