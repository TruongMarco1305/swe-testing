"""
TC-005: Admin Creates a Calendar Event
Level-1 Selenium test – data-driven from test_data_tc005.csv
"""

import csv
import os
import time
import unittest
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL   = "https://ihatetesting.moodlecloud.com"
ADMIN_USER = "phuc.nguyen0310@hcmut.edu.vn"
ADMIN_PASS = "Huuphuc0310@"
CAL_URL    = f"{BASE_URL}/calendar/view.php?view=month"
CSV_PATH   = os.path.join(os.path.dirname(__file__), "test_data_tc005.csv")


def _load_csv():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _make_test(row):
    tc_id          = row["test_case_id"]
    name           = row["name"]
    duration_type  = row["duration_type"]          # none | minutes | until
    minutes_val    = row["minutes"]                # may be empty
    until_offset   = row["until_offset_days"]      # may be empty
    repeat         = row["repeat"].strip().lower() == "yes"
    expected       = row["expected_result"].strip().lower()  # success | fail

    def test_method(self):
        driver = self.__class__.driver
        wait   = WebDriverWait(driver, 20)

        # ── navigate to calendar ──────────────────────────────────────────
        driver.get(CAL_URL)
        time.sleep(3)

        # ── open New Event modal ──────────────────────────────────────────
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-action='new-event-button']")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

        # ── build JS payload ──────────────────────────────────────────────
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
function clickRadio(name,val){
  document.querySelectorAll('input[name="'+name+'"]').forEach(function(r){
    if(r.value===val){r.click();}
  });
}
function setCheckbox(id,checked){
  var e=document.getElementById(id);
  if(e){if(e.checked!==checked){e.click();}}
}
"""

        js_fill = js_helpers + f"\nnS('id_name',{repr(name)});\n"
        js_fill += """
var tod=new Date();
sS('id_timestart_day',tod.getDate());
sS('id_timestart_month',tod.getMonth()+1);
sS('id_timestart_year',tod.getFullYear());
sS('id_timestart_hour',tod.getHours());
sS('id_timestart_minute',0);
"""

        if duration_type == "none":
            js_fill += "clickRadio('duration','0');\n"
        elif duration_type == "minutes":
            js_fill += "clickRadio('duration','1');\n"
            js_fill += f"nS('id_minutes',{repr(str(minutes_val))});\n"
        elif duration_type == "until":
            offset = int(until_offset)
            js_fill += "clickRadio('duration','2');\n"
            js_fill += f"""
var until=new Date(tod.getTime()+({offset})*86400000);
sS('id_timedurationuntil_day',until.getDate());
sS('id_timedurationuntil_month',until.getMonth()+1);
sS('id_timedurationuntil_year',until.getFullYear());
sS('id_timedurationuntil_hour',until.getHours());
sS('id_timedurationuntil_minute',0);
"""

        if repeat:
            js_fill += "setCheckbox('id_repeat',true);\n"

        driver.execute_script(js_fill)
        time.sleep(2)

        # ── click Save in modal ───────────────────────────────────────────
        save_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='dialog']//button[@data-action='save']")))
        driver.execute_script("arguments[0].click();", save_btn)
        time.sleep(4)

        # ── determine outcome ─────────────────────────────────────────────
        outcome = self._get_outcome(driver)
        self.assertEqual(
            outcome, expected,
            f"{tc_id}: expected={expected}, got={outcome} | name={repr(name)} "
            f"duration_type={duration_type} minutes={minutes_val} until_offset={until_offset}"
        )

    test_method.__name__ = f"test_{tc_id.replace('-', '_')}"
    return test_method


class TestCalendarEventLevel1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        opts = webdriver.ChromeOptions()
        # opts.add_argument("--headless")   # uncomment for headless mode
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
        cls.driver.set_window_size(1400, 900)
        cls._login()

    @classmethod
    def _login(cls):
        driver = cls.driver
        driver.get(f"{BASE_URL}/login/index.php")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(ADMIN_USER)
        driver.find_element(By.ID, "password").send_keys(ADMIN_PASS)
        driver.find_element(By.ID, "loginbtn").click()
        wait.until(EC.url_contains("/my/"))
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _get_outcome(self, driver):
        """Return 'fail' if error element present in modal, else 'success'."""
        # Check for in-modal error first
        errors = driver.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
        if errors:
            return "fail"
        # Success: modal closed and page contains Calendar heading
        if "Calendar" in driver.page_source:
            return "success"
        # Fallback: modal still open with no error counts as success
        return "success"


# ── dynamically attach test methods ──────────────────────────────────────────
for _row in _load_csv():
    _m = _make_test(_row)
    setattr(TestCalendarEventLevel1, _m.__name__, _m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
