"""
NON-FUNCTIONAL TEST FILE 02 — TC-002 ADMIN CREATES A NEW COURSE
                              Security Testing
Feature : Moodle LMS — Course creation form
Site    : https://xuansang1234.moodlecloud.com/course/edit.php?category=0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR  SECURITY TESTING  (requests — passive probes)
  Tool      : pip install requests
  Approach  : Verify the course-creation endpoint enforces auth,
              the login form embeds a CSRF logintoken, XSS payloads
              are not reflected unescaped, and malformed requests do
              not surface PHP errors or stack traces.
  Run       : python -m pytest TC-002.py -v
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import unittest

BASE_URL       = "https://xuansang1234.moodlecloud.com"
LOGIN_URL      = BASE_URL + "/login/index.php"
DASHBOARD_URL  = BASE_URL + "/my/"
NEW_COURSE_URL = BASE_URL + "/course/edit.php?category=0"
USERNAME       = "sang.truong2005@hcmut.edu.vn"
PASSWORD       = "Abcdxyz12@"
UA             = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
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
# NFR  SECURITY  — passive probes for TC-002 Course-creation
# ══════════════════════════════════════════════════════════════════════════
class TestNewCourseSecurity(unittest.TestCase):
    """Security probes for TC-002 (Admin Creates a New Course) feature."""

    PHP_ERROR_PATTERNS = [
        "<b>Fatal error</b>", "<b>Parse error</b>",
        "<b>Warning</b>:", "<b>Notice</b>:",
        "Call to undefined function", "Call to a member function",
        "Uncaught Error:", "Uncaught Exception:", "Stack trace:",
    ]

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_course_creation_requires_authentication(self):
        """Anonymous GET to the course-creation form must redirect to login."""
        import requests
        anon = requests.Session()
        anon.headers.update({"User-Agent": UA})
        r = anon.get(NEW_COURSE_URL, timeout=20, allow_redirects=True)
        is_login = (
            "/login/" in r.url or
            'name="logintoken"' in r.text or
            ('name="username"' in r.text and 'name="password"' in r.text)
        )
        self.assertTrue(is_login,
                        f"Course-creation form accessible without auth; url={r.url}")
        print(f"\n  [SEC] Anonymous access to course form redirected to login [OK]")

    def test_02_login_form_has_csrf_token(self):
        """Moodle login form must embed a CSRF logintoken."""
        import requests
        r = requests.get(LOGIN_URL, headers={"User-Agent": UA}, timeout=15)
        m = re.search(r'name="logintoken"\s+value="([^"]+)"', r.text)
        self.assertIsNotNone(m, "Login form missing logintoken CSRF field")
        print(f"\n  [SEC] Login CSRF logintoken present (len={len(m.group(1))}) [OK]")

    def test_03_authenticated_session_has_csrf_sesskey(self):
        """The authenticated session must expose a sesskey on the dashboard."""
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
                         "Session was not preserved (got login form back)")
        print(f"\n  [SEC] Authenticated session has CSRF sesskey [OK]")

    def test_04_xss_payload_in_username_not_reflected(self):
        """XSS payload as username must not be echoed unescaped on the login form."""
        import requests
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        r0 = s.get(LOGIN_URL, timeout=15)
        m = re.search(r'name="logintoken"\s+value="([^"]+)"', r0.text)
        token = m.group(1) if m else ""
        payload = '<script>alert("xss_c_' + 'c' * 8 + '")</script>'
        post = s.post(LOGIN_URL,
                      data={"username": payload, "password": "wrong",
                            "logintoken": token},
                      timeout=15)
        self.assertNotIn(payload, post.text,
                         "Raw <script> payload reflected on login — XSS risk")
        print(f"\n  [SEC] XSS payload not reflected unescaped [OK]")

    def test_05_no_php_error_on_malformed_course_query(self):
        """Malformed query on the course-creation endpoint must not leak PHP errors."""
        bad_url = NEW_COURSE_URL + "&category=' OR 1=1--&id=<script>"
        r = self.session.get(bad_url, timeout=20)
        for pat in self.PHP_ERROR_PATTERNS:
            self.assertNotIn(pat, r.text,
                             f"Server leaked PHP error signature '{pat}'")
        print(f"\n  [SEC] No PHP error on malformed course query "
              f"(HTTP {r.status_code}) [OK]")

    def test_06_no_php_error_on_overlong_input(self):
        """An overlong POST to the login endpoint must not surface PHP errors."""
        import requests
        bad = requests.post(LOGIN_URL,
                            headers={"User-Agent": UA},
                            data={"username": "x" * 5000,
                                  "password": "y" * 5000},
                            timeout=15)
        for pat in self.PHP_ERROR_PATTERNS:
            self.assertNotIn(pat, bad.text,
                             f"Server leaked PHP error signature '{pat}'")
        print(f"\n  [SEC] No PHP error/stack-trace on overlong input [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)

