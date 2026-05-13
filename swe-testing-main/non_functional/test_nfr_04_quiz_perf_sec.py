"""
NON-FUNCTIONAL TEST FILE 04 — QUIZ SETUP: PERFORMANCE + SECURITY
Feature : Moodle LMS — Teacher Sets Up a Quiz
Site    : https://ihatetesting.moodlecloud.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR-1  PERFORMANCE TESTING   (Locust)
  Tool      : pip install locust
  Approach  : Authenticated Locust user navigates the course view, then
              opens the quiz-add modedit form repeatedly to measure
              server-rendered form latency under concurrency.
  Run       : locust -f test_nfr_04_quiz_perf_sec.py

NFR-2  SECURITY TESTING      (OWASP ZAP Python API)
  Tool      : pip install python-owasp-zap-v2.4
  Pre-req   : ZAP daemon on 127.0.0.1:8080
  Approach  : Active scan the authenticated quiz-add URL (after seeding
              ZAP with a session cookie); assert no High alerts.
  Run       : python -m unittest test_nfr_04_quiz_perf_sec.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import time
import unittest

BASE_URL    = "https://ihatetesting.moodlecloud.com"
LOGIN_URL   = BASE_URL + "/login/index.php"
COURSE_ID   = 426
SECTION_ID  = 2121
COURSE_URL  = BASE_URL + f"/course/view.php?id={COURSE_ID}"
QUIZ_ADD_URL = (BASE_URL
                + f"/course/modedit.php?add=quiz&type"
                  f"&course={COURSE_ID}&sectionid={SECTION_ID}"
                  f"&return=0&beforemod=0")
USERNAME    = "phuc.nguyen0310@hcmut.edu.vn"
PASSWORD    = "Huuphuc0310@"


# ══════════════════════════════════════════════════════════════════════════
# NFR-1  PERFORMANCE  — Locust (authenticated quiz-form load)
# ══════════════════════════════════════════════════════════════════════════
try:
    from locust import HttpUser, task, between, events

    class QuizSetupPerfUser(HttpUser):
        host = BASE_URL
        wait_time = between(2, 6)

        def on_start(self):
            """Log in once per virtual user before hitting protected URLs."""
            r = self.client.get("/login/index.php", name="GET /login")
            m = re.search(r'name="logintoken" value="([^"]+)"', r.text)
            token = m.group(1) if m else ""
            self.client.post("/login/index.php",
                             data={"username": USERNAME,
                                   "password": PASSWORD,
                                   "logintoken": token},
                             name="POST /login")

        @task(2)
        def view_course(self):
            self.client.get(f"/course/view.php?id={COURSE_ID}",
                            name="GET /course/view")

        @task(3)
        def open_quiz_form(self):
            with self.client.get(
                f"/course/modedit.php?add=quiz&type"
                f"&course={COURSE_ID}&sectionid={SECTION_ID}"
                f"&return=0&beforemod=0",
                name="GET /modedit (quiz add)",
                catch_response=True) as r:
                if r.status_code != 200:
                    r.failure(f"Quiz form returned {r.status_code}")
                elif 'id="id_name"' not in r.text:
                    r.failure("Quiz form did not render id_name input")
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════
# NFR-2  SECURITY  — ZAP active scan of authenticated quiz add URL
# ══════════════════════════════════════════════════════════════════════════
class TestQuizFormZapScan(unittest.TestCase):

    ZAP_PROXY = "http://127.0.0.1:8080"

    @classmethod
    def setUpClass(cls):
        from zapv2 import ZAPv2
        cls.zap = ZAPv2(proxies={"http": cls.ZAP_PROXY, "https": cls.ZAP_PROXY})
        # Replay one authenticated browser session through ZAP so it has
        # cookies. The QA team should configure a ZAP context for Moodle.
        print("\n  [SEC] Ensure ZAP has a Moodle session context configured.")

    def test_01_spider_quiz_add_url(self):
        print(f"\n  [SEC] Spidering {QUIZ_ADD_URL} ...")
        sid = self.zap.spider.scan(QUIZ_ADD_URL)
        while int(self.zap.spider.status(sid)) < 100:
            time.sleep(2)
        self.assertIn(QUIZ_ADD_URL,
                      self.zap.core.urls(),
                      "Spider did not register the quiz-add URL")

    def test_02_active_scan_no_high_or_medium(self):
        """Quiz add endpoint must show no High/Medium alerts after active scan."""
        print(f"\n  [SEC] Active scanning {QUIZ_ADD_URL} ...")
        sid = self.zap.ascan.scan(QUIZ_ADD_URL)
        while int(self.zap.ascan.status(sid)) < 100:
            time.sleep(5)

        alerts = self.zap.core.alerts(baseurl=QUIZ_ADD_URL)
        bad = [a for a in alerts if a["risk"] in ("High", "Medium")]
        for a in bad:
            print(f"    ✗ {a['risk']:<6} {a['alert']} @ {a['url']}")
        self.assertEqual(len(bad), 0,
                         f"{len(bad)} High/Medium-risk alerts on quiz add page")
        print(f"  [SEC] No High/Medium alerts ✓ (total alerts: {len(alerts)})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
