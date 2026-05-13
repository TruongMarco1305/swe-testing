"""
NON-FUNCTIONAL TEST FILE 01 — LOGIN: PERFORMANCE + SECURITY
Feature : Moodle LMS — Login page (entry point to Teacher's Quiz Setup)
Site    : https://ihatetesting.moodlecloud.com/login/index.php

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING  (Locust)
  Tool          : pip install locust
  Approach      : Spawn N virtual users hitting /login/index.php to measure
                  RPS, p95 response time, and failure rate under load.
  Run           : locust -f test_nfr_01_login_perf_sec.py --class-picker
                  (then open http://localhost:8089)

NFR-2  SECURITY TESTING     (OWASP ZAP Python API)
  Tool          : pip install python-owasp-zap-v2.4
  Prerequisite  : ZAP running as daemon on 127.0.0.1:8080
                  (zap.sh -daemon -port 8080 -config api.disablekey=true)
  Approach      : Spider + Active Scan the login URL; assert no High-risk
                  alerts (XSS, SQLi, missing TLS, etc.).
  Run           : python -m unittest test_nfr_01_login_perf_sec.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
import unittest

# ── Shared configuration ──────────────────────────────────────────────────
BASE_URL  = "https://ihatetesting.moodlecloud.com"
LOGIN_URL = BASE_URL + "/login/index.php"
USERNAME  = "phuc.nguyen0310@hcmut.edu.vn"
PASSWORD  = "Huuphuc0310@"


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  PERFORMANCE  — Locust HttpUser
# ══════════════════════════════════════════════════════════════════════════
try:
    from locust import HttpUser, task, between

    class LoginPerfUser(HttpUser):
        """Simulates a teacher repeatedly opening the Moodle login page."""
        host = BASE_URL
        wait_time = between(1, 5)

        @task(3)
        def load_login_page(self):
            with self.client.get("/login/index.php",
                                 name="GET /login",
                                 catch_response=True) as resp:
                if resp.status_code != 200:
                    resp.failure(f"Login page returned {resp.status_code}")
                elif "loginbtn" not in resp.text:
                    resp.failure("Login button missing from page")

        @task(1)
        def submit_invalid_login(self):
            """Pretend-submit (no valid token) — measures POST latency only."""
            self.client.post("/login/index.php",
                             data={"username": "dummy", "password": "dummy"},
                             name="POST /login (invalid)")
except ImportError:
    pass   # Locust not installed in this environment — unittest still runs


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  SECURITY  — OWASP ZAP active scan
# ══════════════════════════════════════════════════════════════════════════
class TestLoginZapScan(unittest.TestCase):
    """Drives a running OWASP ZAP daemon to scan the Moodle login page."""

    ZAP_PROXY = "http://127.0.0.1:8080"

    @classmethod
    def setUpClass(cls):
        # Skips with platform-aware install/launch instructions if the python
        # client is missing OR the ZAP daemon is not reachable on ZAP_PROXY.
        from zap_setup import ensure_zap_ready
        cls.zap = ensure_zap_ready(cls.ZAP_PROXY)

    def test_01_spider_login_url(self):
        """ZAP spider must enumerate the login URL without errors."""
        print(f"\n  [SEC] Spidering {LOGIN_URL} ...")
        scan_id = self.zap.spider.scan(LOGIN_URL)
        while int(self.zap.spider.status(scan_id)) < 100:
            time.sleep(2)
        urls = self.zap.core.urls()
        self.assertIn(LOGIN_URL, urls, "Spider failed to register login URL")
        print(f"  [SEC] Spider OK — {len(urls)} URLs discovered")

    def test_02_active_scan_no_high_alerts(self):
        """Active scan must produce zero High-risk alerts on the login page."""
        print(f"\n  [SEC] Active scanning {LOGIN_URL} ...")
        scan_id = self.zap.ascan.scan(LOGIN_URL)
        while int(self.zap.ascan.status(scan_id)) < 100:
            time.sleep(5)
        alerts = self.zap.core.alerts(baseurl=LOGIN_URL)
        high = [a for a in alerts if a["risk"] == "High"]
        for a in high:
            print(f"    ✗ HIGH: {a['alert']} @ {a['url']}")
        self.assertEqual(len(high), 0,
                         f"{len(high)} High-risk alerts on login page")
        print(f"  [SEC] No High-risk alerts ✓ (total alerts: {len(alerts)})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
