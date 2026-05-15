"""
NON-FUNCTIONAL TEST FILE 04 — TC-004 TEACHER GRADES A STUDENT
                              Reliability Testing
Feature : Moodle LMS — Assignment grader (assignment cmid=41, userid=2)
Site    : https://xuansang1234.moodlecloud.com/mod/assign/view.php
          ?id=41&action=grader&userid=2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR  RELIABILITY TESTING  (unittest + requests)
  Tool      : pip install requests
  Approach  : Repeat the grader-page load N times under the same
              authenticated session and assert consistent HTTP status
              codes, identical page structure, no response-time
              degradation across runs, and session persistence.
  Run       : python -m pytest TC-004.py -v
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import time
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

REPEAT_COUNT       = 5    # number of consecutive identical requests
DEGRADATION_FACTOR = 3.0  # no single run may be >3× slower than the fastest


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
# NFR  RELIABILITY  — repeated identical grader page loads
# ══════════════════════════════════════════════════════════════════════════
class TestGraderReliability(unittest.TestCase):
    """Reliability tests for TC-004 (Teacher Grades a Student) feature."""

    @classmethod
    def setUpClass(cls):
        cls.session = _login_session()

    def test_01_grader_page_consistently_returns_200(self):
        """All consecutive loads of the grader page must return HTTP 200."""
        for i in range(1, REPEAT_COUNT + 1):
            r = self.session.get(GRADER_URL, timeout=20)
            self.assertEqual(r.status_code, 200,
                             f"Run #{i}: grader returned {r.status_code}")
            print(f"\n  [REL] Run #{i}: HTTP {r.status_code} [OK]")

    def test_02_grader_page_content_consistent_across_runs(self):
        """Key DOM marker must be present in every repeated load."""
        marker = "mod/assign"
        for i in range(1, REPEAT_COUNT + 1):
            r = self.session.get(GRADER_URL, timeout=20)
            self.assertIn(marker, r.text,
                          f"Run #{i}: grader page missing '{marker}' — "
                          "session may have degraded")
            print(f"\n  [REL] Run #{i}: content marker '{marker}' present [OK]")

    def test_03_response_time_does_not_degrade_across_runs(self):
        """No single run must be >{factor}× slower than the fastest run."""
        times = []
        for i in range(1, REPEAT_COUNT + 1):
            start = time.time()
            self.session.get(GRADER_URL, timeout=20)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"\n  [REL] Run #{i}: {elapsed:.3f}s")

        fastest = min(times)
        for i, t in enumerate(times, start=1):
            self.assertLessEqual(
                t, fastest * DEGRADATION_FACTOR,
                f"Run #{i} ({t:.2f}s) is >{DEGRADATION_FACTOR}× fastest run "
                f"({fastest:.2f}s) — potential performance degradation"
            )
        print(f"\n  [REL] All {REPEAT_COUNT} runs within {DEGRADATION_FACTOR}× "
              f"fastest ({fastest:.3f}s) [OK]")

    def test_04_session_remains_authenticated_after_repeated_requests(self):
        """After {N} requests the session must still be authenticated."""
        for _ in range(REPEAT_COUNT):
            self.session.get(GRADER_URL, timeout=20)
        r = self.session.get(DASHBOARD_URL, timeout=20)
        self.assertNotIn('name="logintoken"', r.text,
                         f"Session expired after {REPEAT_COUNT} grader requests")
        self.assertEqual(r.status_code, 200,
                         f"Dashboard returned {r.status_code} after session stress")
        print(f"\n  [REL] Session still authenticated after "
              f"{REPEAT_COUNT} requests [OK]")

    def test_05_grader_never_returns_server_error(self):
        """No grader request in {N} runs must produce a 5xx server error."""
        for i in range(1, REPEAT_COUNT + 1):
            r = self.session.get(GRADER_URL, timeout=20)
            self.assertLess(r.status_code, 500,
                            f"Run #{i}: server error {r.status_code}")
            print(f"\n  [REL] Run #{i}: no 5xx (status {r.status_code}) [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)

