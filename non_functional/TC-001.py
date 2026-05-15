"""
NON-FUNCTIONAL TEST FILE 01 — TC-001 ADMIN ADDS A NEW USER
                              Performance Testing
Feature : Moodle LMS — Admin user-creation form
Site    : https://xuansang1234.moodlecloud.com/user/editadvanced.php?id=-1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR  PERFORMANCE TESTING  (Locust + time.time() SLA assertions)
  Tool      : pip install locust requests
  Approach  : Authenticated admin opens the "Add new user" form
              repeatedly under concurrency; measures form-render
              latency, RPS, and failure rate.
              A unittest class validates SLA thresholds against the
              live server using direct HTTP requests.
  SLAs      : login page  ≤ 5 s · add-user form  ≤ 8 s
  Locust    : locust -f TC-001.py --class-picker
  Unittest  : python -m pytest TC-001.py -v
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import sys
import time
import unittest

# ── Shared configuration ──────────────────────────────────────────────────
BASE_URL      = "https://xuansang1234.moodlecloud.com"
LOGIN_URL     = BASE_URL + "/login/index.php"
DASHBOARD_URL = BASE_URL + "/my/"
ADD_USER_URL  = BASE_URL + "/user/editadvanced.php?id=-1"
USERNAME      = "sang.truong2005@hcmut.edu.vn"
PASSWORD      = "Abcdxyz12@"
UA            = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/120.0.0.0 Safari/537.36")

SLA_LOGIN_S        = 5.0   # login GET/POST must complete within this many seconds
SLA_ADD_USER_FORM_S = 8.0  # authenticated add-user form load SLA


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
# NFR  PERFORMANCE  — Locust (authenticated admin loads add-user form)
# ══════════════════════════════════════════════════════════════════════════
# Locust's gevent monkey-patches `ssl` at import time. Under pytest the
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
# NFR  PERFORMANCE  — SLA assertions (unittest via pytest)
# ══════════════════════════════════════════════════════════════════════════
class TestAddUserPerformance(unittest.TestCase):
    """SLA-based performance tests for TC-001 (Admin Adds a New User)."""

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_login_page_loads_within_sla(self):
        """GET /login/index.php must respond within the SLA."""
        import requests
        start = time.time()
        r = requests.get(LOGIN_URL, headers={"User-Agent": UA}, timeout=15)
        elapsed = time.time() - start
        self.assertEqual(r.status_code, 200,
                         f"Login page returned {r.status_code}")
        self.assertLessEqual(elapsed, SLA_LOGIN_S,
                             f"Login page load {elapsed:.2f}s exceeds SLA {SLA_LOGIN_S}s")
        print(f"\n  [PERF] Login page loaded in {elapsed:.3f}s "
              f"(SLA ≤{SLA_LOGIN_S}s) [OK]")

    def test_02_add_user_form_loads_within_sla(self):
        """Authenticated GET to the Add-User form must respond within the SLA."""
        start = time.time()
        r = self.session.get(ADD_USER_URL, timeout=15)
        elapsed = time.time() - start
        self.assertEqual(r.status_code, 200,
                         f"Add-User form returned {r.status_code}")
        self.assertLessEqual(elapsed, SLA_ADD_USER_FORM_S,
                             f"Add-User form {elapsed:.2f}s exceeds SLA {SLA_ADD_USER_FORM_S}s")
        print(f"\n  [PERF] Add-User form loaded in {elapsed:.3f}s "
              f"(SLA ≤{SLA_ADD_USER_FORM_S}s) [OK]")

    def test_03_login_post_completes_within_sla(self):
        """A fresh login POST must complete within the SLA."""
        import requests
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        r0 = s.get(LOGIN_URL, timeout=15)
        m = re.search(r'name="logintoken"\s+value="([^"]+)"', r0.text)
        token = m.group(1) if m else ""
        start = time.time()
        s.post(LOGIN_URL,
               data={"username": USERNAME, "password": PASSWORD,
                     "logintoken": token},
               timeout=20, allow_redirects=True)
        elapsed = time.time() - start
        self.assertLessEqual(elapsed, SLA_LOGIN_S,
                             f"Login POST {elapsed:.2f}s exceeds SLA {SLA_LOGIN_S}s")
        print(f"\n  [PERF] Login POST completed in {elapsed:.3f}s "
              f"(SLA ≤{SLA_LOGIN_S}s) [OK]")

    def test_04_five_consecutive_form_loads_all_within_sla(self):
        """Five back-to-back Add-User form loads must all stay within the SLA."""
        for i in range(1, 6):
            start = time.time()
            r = self.session.get(ADD_USER_URL, timeout=15)
            elapsed = time.time() - start
            self.assertEqual(r.status_code, 200,
                             f"Run #{i}: Add-User form returned {r.status_code}")
            self.assertLessEqual(elapsed, SLA_ADD_USER_FORM_S,
                                 f"Run #{i}: {elapsed:.2f}s exceeds SLA {SLA_ADD_USER_FORM_S}s")
            print(f"\n  [PERF] Run #{i}: {elapsed:.3f}s ≤ {SLA_ADD_USER_FORM_S}s [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
