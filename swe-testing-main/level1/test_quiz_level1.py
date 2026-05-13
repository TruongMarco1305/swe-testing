"""
TC-006: Teacher Creates a Quiz
Level-1 Selenium test – data-driven from test_data_tc006.csv
"""

import csv
import os
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL   = "https://ihatetesting.moodlecloud.com"
ADMIN_USER = "phuc.nguyen0310@hcmut.edu.vn"
ADMIN_PASS = "Huuphuc0310@"
COURSE_ID  = 426
SECTION_ID = 2121
QUIZ_URL   = (
    f"{BASE_URL}/course/modedit.php"
    f"?add=quiz&type&course={COURSE_ID}&sectionid={SECTION_ID}&return=0&beforemod=0"
)
CSV_PATH   = os.path.join(os.path.dirname(__file__), "test_data_tc006.csv")


def _load_csv():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _make_test(row):
    tc_id              = row["test_case_id"]
    name               = row["name"]
    timeclose_enabled  = row["timeclose_enabled"].strip().lower() == "yes"
    close_days         = int(row["close_offset_days"]) if row["close_offset_days"].strip() else 7
    close_years        = int(row["close_offset_years"]) if row["close_offset_years"].strip() else 0
    timelimit_enabled  = row["timelimit_enabled"].strip().lower() == "yes"
    timelimit_number   = row["timelimit_number"].strip() if row["timelimit_number"].strip() else "30"
    gradepass          = row["gradepass"].strip()
    expected           = row["expected_result"].strip().lower()

    def test_method(self):
        driver = self.__class__.driver
        wait   = WebDriverWait(driver, 20)

        driver.get(QUIZ_URL)
        time.sleep(3)

        # type name
        name_field = wait.until(EC.presence_of_element_located((By.ID, "id_name")))
        name_field.clear()
        if name:
            name_field.send_keys(name)

        # JS helpers
        js_helpers = """
function sS(id,v){
  var e=document.getElementById(id);
  if(e){e.value=String(v);e.dispatchEvent(new Event('change',{bubbles:true}));}
}
function nS(id,v){
  var e=document.getElementById(id);
  if(e){
    var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    s.call(e,String(v));
    e.dispatchEvent(new Event('input',{bubbles:true}));
    e.dispatchEvent(new Event('change',{bubbles:true}));
  }
}
function ens(id){var c=document.getElementById(id);if(c&&!c.checked){c.click();}}
function dis(id){var c=document.getElementById(id);if(c&&c.checked){c.click();}}
"""
        js = js_helpers + """
ens('id_timeopen_enabled');
var tod=new Date();
sS('id_timeopen_day',tod.getDate());
sS('id_timeopen_month',tod.getMonth()+1);
sS('id_timeopen_year',tod.getFullYear());
sS('id_timeopen_hour',tod.getHours());
sS('id_timeopen_minute',0);
"""
        if timeclose_enabled:
            js += f"""
ens('id_timeclose_enabled');
var cl=new Date(tod);
cl.setFullYear(cl.getFullYear()+({close_years}));
cl.setDate(cl.getDate()+({close_days}));
sS('id_timeclose_day',cl.getDate());
sS('id_timeclose_month',cl.getMonth()+1);
sS('id_timeclose_year',cl.getFullYear());
sS('id_timeclose_hour',cl.getHours());
sS('id_timeclose_minute',0);
"""
        else:
            js += "dis('id_timeclose_enabled');\n"

        if timelimit_enabled:
            js += f"""
ens('id_timelimit_enabled');
nS('id_timelimit_number',{repr(timelimit_number)});
sS('id_timelimit_timeunit','60');
"""
        else:
            js += "dis('id_timelimit_enabled');\n"

        js += f"nS('id_gradepass',{repr(gradepass)});\n"

        driver.execute_script(js)
        time.sleep(2)

        # submit
        try:
            btn = driver.find_element(By.ID, "id_submitbutton2")
        except Exception:
            btn = driver.find_element(By.ID, "id_submitbutton")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(4)

        outcome = self._get_outcome(driver)
        self.assertEqual(
            outcome, expected,
            f"{tc_id}: expected={expected}, got={outcome} | "
            f"name={repr(name)} gradepass={gradepass} "
            f"timelimit_enabled={timelimit_enabled} timelimit_number={timelimit_number} "
            f"timeclose_enabled={timeclose_enabled} close_days={close_days} close_years={close_years}"
        )

    test_method.__name__ = f"test_{tc_id.replace('-', '_')}"
    return test_method


class TestQuizLevel1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        opts = webdriver.ChromeOptions()
        # opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
        cls.driver.set_window_size(1400, 900)
        cls._login_and_switch_role()

    @classmethod
    def _login_and_switch_role(cls):
        driver = cls.driver
        wait   = WebDriverWait(driver, 20)

        driver.get(f"{BASE_URL}/login/index.php")
        wait.until(EC.presence_of_element_located((By.ID, "username")))

        # dismiss OneTrust / cookie-consent overlay if present
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_btn.click()
            time.sleep(1)
        except Exception:
            pass
        driver.execute_script("""
            var el = document.querySelector('.onetrust-pc-dark-filter');
            if (el) el.style.display = 'none';
            var banner = document.getElementById('onetrust-banner-sdk');
            if (banner) banner.style.display = 'none';
        """)

        driver.find_element(By.ID, "username").send_keys(ADMIN_USER)
        driver.find_element(By.ID, "password").send_keys(ADMIN_PASS)
        driver.execute_script("document.getElementById('loginbtn').click();")
        wait.until(EC.url_contains("/my/"))
        time.sleep(2)

        # switch to Teacher role on course 152
        driver.get(
            f"{BASE_URL}/course/switchrole.php"
            f"?id={COURSE_ID}&switchrole=-1"
            f"&returnurl=%2Fcourse%2Fview.php%3Fid%3D{COURSE_ID}"
        )
        time.sleep(2)
        try:
            teacher_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space(.)='Teacher']")))
            driver.execute_script("arguments[0].click();", teacher_btn)
            time.sleep(2)
        except Exception:
            pass

        # enable editing
        driver.get(f"{BASE_URL}/course/view.php?id={COURSE_ID}")
        time.sleep(2)
        try:
            edit_switch = driver.find_element(By.NAME, "setmode")
            if not edit_switch.is_selected():
                driver.execute_script("arguments[0].click();", edit_switch)
            time.sleep(2)
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _get_outcome(self, driver):
        errors = driver.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
        if errors:
            return "fail"
        if "Announcements" in driver.page_source:
            return "success"
        return "success"


# ── attach test methods dynamically ──────────────────────────────────────────
for _row in _load_csv():
    _m = _make_test(_row)
    setattr(TestQuizLevel1, _m.__name__, _m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
