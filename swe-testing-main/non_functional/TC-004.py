"""
NON-FUNCTIONAL TEST FILE 04 — TC-004 TEACHER GRADES A STUDENT
                              Performance + Security
Feature : Moodle LMS — Assignment grader (assignment cmid=41, userid=2)
Site    : https://xuansang1234.moodlecloud.com/mod/assign/view.php
          ?id=41&action=grader&userid=2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING   (Locust)
  Tool      : pip install locust
  Approach  : Authenticated teacher repeatedly loads the grader page
              and measures latency under concurrency.
  Run       : locust -f test_nfr_04_quiz_perf_sec.py

NFR-2  SECURITY TESTING      (requests — passive probes)
  Tool      : pip install requests
  Approach  : Verify the grader page enforces authentication, the
              authenticated session exposes a sesskey, and malformed
              grader queries do not leak PHP errors.
  Run       : python -m unittest test_nfr_04_quiz_perf_sec.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import sys
import unittest

BASE_URL      = "https://xuansang1234.moodlecloud.com"
LOGIN_URL     = BASE_URL + "/login/index.php"
DASHBOARD_URL = BASE_URL + "/my/"
ASSIGN_CMID   = 41
GRADER_USERID = 2
GRADER_URL    = (BASE_URL
                 + f"/mod/assign/view.php?id={ASSIGN_CMID}"
                   f"&action=grader&userid={GRADER_USERID}")
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
# NFR-1  PERFORMANCE  — Locust (authenticated grader page load)
# ══════════════════════════════════════════════════════════════════════════
# Skip Locust import under pytest — gevent monkey-patching of `ssl` after
# selenium has loaded it causes RecursionError during pytest collection.
def _define_locust_users():
    from locust import HttpUser, task, between

    class GraderPerfUser(HttpUser):
        host = BASE_URL
        wait_time = between(2, 6)

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
        def open_grader(self):
            with self.client.get(
                f"/mod/assign/view.php?id={ASSIGN_CMID}"
                f"&action=grader&userid={GRADER_USERID}",
                name="GET /mod/assign/view (grader)",
                catch_response=True) as r:
                if r.status_code != 200:
                    r.failure(f"Grader returned {r.status_code}")

    globals()["GraderPerfUser"] = GraderPerfUser


if "pytest" not in sys.modules:
    try:
        _define_locust_users()
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  SECURITY  — Authenticated requests probes
# ══════════════════════════════════════════════════════════════════════════
class TestGraderSecurity(unittest.TestCase):

    PHP_ERROR_PATTERNS = [
        "<b>Fatal error</b>", "<b>Parse error</b>",
        "<b>Warning</b>:", "<b>Notice</b>:",
        "Call to undefined function", "Call to a member function",
        "Uncaught Error:", "Uncaught Exception:", "Stack trace:",
    ]

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_grader_requires_authentication(self):
        """Anonymous access to the grader URL must be blocked."""
        import requests
        anon = requests.Session()
        anon.headers.update({"User-Agent": UA})
        r = anon.get(GRADER_URL, timeout=20, allow_redirects=True)
        is_blocked = (
            "/login/" in r.url or
            'name="logintoken"' in r.text or
            r.status_code in (302, 401, 403)
        )
        self.assertTrue(is_blocked,
                        f"Grader URL exposed anonymously; url={r.url}, status={r.status_code}")
        print(f"\n  [SEC] Anonymous access to grader blocked (status {r.status_code}) [OK]")

    def test_02_authenticated_session_has_csrf_sesskey(self):
        """Authenticated session must expose a sesskey on the dashboard."""
        r = self.session.get(DASHBOARD_URL, timeout=20)
        self.assertEqual(r.status_code, 200,
                         f"Dashboard returned {r.status_code}")
        has_sesskey = (
            '"sesskey":' in r.text or
            'name="sesskey"' in r.text or
            'sesskey=' in r.text
        )
        self.assertTrue(has_sesskey,
                        "Authenticated session missing CSRF sesskey")
        self.assertNotIn('name="logintoken"', r.text,
                         "Session not preserved (got login form back)")
        print(f"\n  [SEC] Authenticated session has CSRF sesskey [OK]")

    def test_03_no_php_error_on_malformed_grader_query(self):
        """Malformed grader query string must not leak PHP errors."""
        bad_url = GRADER_URL + "&userid=' OR 1=1--&id=<script>"
        r = self.session.get(bad_url, timeout=20)
        for pat in self.PHP_ERROR_PATTERNS:
            self.assertNotIn(pat, r.text,
                             f"Grader leaked PHP error signature '{pat}'")
        print(f"\n  [SEC] No PHP error on malformed grader query "
              f"(HTTP {r.status_code}) [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
