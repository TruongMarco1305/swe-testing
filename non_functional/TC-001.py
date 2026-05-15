"""
NON-FUNCTIONAL TEST FILE 01 — TC-001 ADMIN ADDS A NEW USER
                              Performance + Security
Feature : Moodle LMS — Admin user-creation form
Site    : https://xuansang1234.moodlecloud.com/user/editadvanced.php?id=-1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING  (Locust)
  Tool          : pip install locust
  Approach      : Authenticated admin opens the "Add new user" form
                  repeatedly under concurrency; measures form-render
                  latency, RPS, and failure rate.
  Run           : locust -f test_nfr_01_login_perf_sec.py --class-picker

NFR-2  SECURITY TESTING     (requests — passive probes)
  Tool          : pip install requests
  Approach      : Verify the add-user endpoint enforces authentication,
                  the login form embeds a CSRF token, the XSS payload
                  submitted as username is HTML-escaped, and malformed
                  POSTs do not surface PHP errors.
  Run           : python -m unittest test_nfr_01_login_perf_sec.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import sys
import unittest

# ── Shared configuration ──────────────────────────────────────────────────
BASE_URL     = "https://xuansang1234.moodlecloud.com"
LOGIN_URL    = BASE_URL + "/login/index.php"
DASHBOARD_URL = BASE_URL + "/my/"
ADD_USER_URL = BASE_URL + "/user/editadvanced.php?id=-1"
USERNAME     = "sang.truong2005@hcmut.edu.vn"
PASSWORD     = "Abcdxyz12@"
UA           = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36")


def _login_session():
    """Return a requests.Session authenticated as admin against Moodle."""
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
# NFR-1  PERFORMANCE  — Locust (authenticated admin loads add-user form)
# ══════════════════════════════════════════════════════════════════════════
# Locust's gevent monkey-patches `ssl` at import time. Under pytest the
# selenium imports done by level1 tests have already loaded ssl, so the
# late monkey-patch produces RecursionError. Skip the Locust import path
# entirely when running under pytest — locust users are only needed when
# the file is invoked via the `locust` CLI.
def _define_locust_users():
    from locust import HttpUser, task, between

    class AddUserPerfUser(HttpUser):
        """Simulates an admin repeatedly opening the Add-User form."""
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
        def open_add_user_form(self):
            with self.client.get("/user/editadvanced.php?id=-1",
                                 name="GET /user/editadvanced (add)",
                                 catch_response=True) as r:
                if r.status_code != 200:
                    r.failure(f"Add-User form returned {r.status_code}")
                elif 'id="id_username"' not in r.text:
                    r.failure("Add-User form did not render id_username")

    globals()["AddUserPerfUser"] = AddUserPerfUser


if "pytest" not in sys.modules:
    try:
        _define_locust_users()
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  SECURITY  — passive probes for the Add-User feature
# ══════════════════════════════════════════════════════════════════════════
class TestAddUserSecurity(unittest.TestCase):
    """Security probes for TC-001 (Admin Adds a New User) feature."""

    PHP_ERROR_PATTERNS = [
        "<b>Fatal error</b>", "<b>Parse error</b>",
        "<b>Warning</b>:", "<b>Notice</b>:",
        "Call to undefined function", "Call to a member function",
        "Uncaught Error:", "Uncaught Exception:", "Stack trace:",
    ]

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_add_user_form_requires_authentication(self):
        """Anonymous GET to /user/editadvanced.php must redirect to login."""
        import requests
        anon = requests.Session()
        anon.headers.update({"User-Agent": UA})
        r = anon.get(ADD_USER_URL, timeout=20, allow_redirects=True)
        is_login = (
            "/login/" in r.url or
            'name="logintoken"' in r.text or
            ('name="username"' in r.text and 'name="password"' in r.text)
        )
        self.assertTrue(is_login,
                        f"Add-User form accessible without auth; url={r.url}")
        print(f"\n  [SEC] Anonymous access to Add-User redirected to login [OK]")

    def test_02_login_form_has_csrf_token(self):
        """Moodle login form must embed a CSRF logintoken."""
        import requests
        r = requests.get(LOGIN_URL, headers={"User-Agent": UA}, timeout=15)
        m = re.search(r'name="logintoken"\s+value="([^"]+)"', r.text)
        self.assertIsNotNone(m, "Login form missing logintoken CSRF field")
        print(f"\n  [SEC] Login CSRF logintoken present (len={len(m.group(1))}) [OK]")

    def test_03_xss_payload_in_username_not_reflected(self):
        """XSS payload as username must not be echoed unescaped on the login form."""
        import requests
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        r0 = s.get(LOGIN_URL, timeout=15)
        m = re.search(r'name="logintoken"\s+value="([^"]+)"', r0.text)
        token = m.group(1) if m else ""

        payload = '<script>alert("xss_u_' + 'a' * 8 + '")</script>'
        post = s.post(LOGIN_URL,
                      data={"username": payload, "password": "wrong",
                            "logintoken": token},
                      timeout=15)
        self.assertNotIn(payload, post.text,
                         "Raw <script> payload reflected on login — XSS risk")
        print(f"\n  [SEC] XSS payload not reflected unescaped [OK]")

    def test_04_no_php_error_on_malformed_login(self):
        """A malformed POST must not leak unhandled PHP errors."""
        import requests
        bad = requests.post(LOGIN_URL,
                            headers={"User-Agent": UA},
                            data={"username": "x" * 5000,
                                  "password": "y" * 5000},
                            timeout=15)
        body = bad.text
        for pat in self.PHP_ERROR_PATTERNS:
            self.assertNotIn(pat, body,
                             f"Server leaked PHP error signature '{pat}'")
        print(f"\n  [SEC] No PHP error/stack-trace leaks on malformed login [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
