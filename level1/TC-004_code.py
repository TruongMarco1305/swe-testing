"""
LEVEL 1 — Data-Driven Automation Testing
TC-004 : Teacher Grades a Student Assignment (Moodle LMS)
Converted from: TC-004.krecorder (Katalon Recorder)

Data-driven approach
--------------------
Varying values (grade, feedback, expected_result) are read from
TC-004_data.csv.  Locators and the grading page URL are hardcoded here.

Run all:
    cd level1
    python -m pytest TC-004_code.py -v

Run single:
    python -m pytest TC-004_code.py -v -k "TC_004_002"
"""

import csv
import os
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL   = "https://xuansang1234.moodlecloud.com"
LOGIN_URL  = f"{BASE_URL}/login/index.php"
GRADER_URL = f"{BASE_URL}/mod/assign/view.php?id=41&action=grader&userid=2"
ADMIN_USER = "sang.truong2005@hcmut.edu.vn"
ADMIN_PASS = "Abcdxyz12@"

# JS: set grade using React-compatible native input setter + dispatch events
_JS_SET_GRADE = """
    function nS(id, v) {
        var e = document.getElementById(id);
        if (e) {
            var s = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            s.call(e, String(v));
            e.dispatchEvent(new Event('input',  {bubbles:true}));
            e.dispatchEvent(new Event('change', {bubbles:true}));
            e.dispatchEvent(new Event('blur',   {bubbles:true}));
        }
    }
    // Remove old marker
    var old = document.getElementById('__test_marker');
    if (old) old.remove();
    // Set grade
    nS('id_grade', arguments[0]);
    // Set feedback text
    var fb = 'Good work';
    if (window.tinymce && window.tinymce.activeEditor) {
        try { window.tinymce.activeEditor.setContent(fb); } catch(e) {}
    }
    var ifr = document.getElementById('id_assignfeedbackcomments_editor_ifr');
    if (ifr && ifr.contentDocument && ifr.contentDocument.body) {
        ifr.contentDocument.body.innerText = fb;
    }
    var ta = document.getElementById('id_assignfeedbackcomments_editor');
    if (ta) {
        ta.value = fb;
        ta.dispatchEvent(new Event('change', {bubbles:true}));
    }
    // Notify student
    var nf = document.getElementById('id_sendstudentnotifications');
    if (nf) {
        if (nf.tagName === 'SELECT') {
            nf.value = '1';
            nf.dispatchEvent(new Event('change', {bubbles:true}));
        } else if (nf.type === 'checkbox' && !nf.checked) {
            nf.click();
        }
    }
"""

# JS: inject marker with error detection AND error-message capture
_JS_CHECK_ERRORS = """
    var hasErr = false;
    var errMsg = '';
    var sels = '[id^="id_error_"], .invalid-feedback, .form-control-feedback, '
             + '.error.felement, .help-block.text-danger';
    document.querySelectorAll(sels).forEach(function(el) {
        var st = window.getComputedStyle(el);
        var visible = (st.display !== 'none')
                   && (st.visibility !== 'hidden')
                   && (el.offsetParent !== null);
        var txt = (el.innerText || el.textContent || '').trim();
        if (visible && txt) {
            hasErr = true;
            if (!errMsg) errMsg = txt;
            else errMsg += ' | ' + txt;
        }
    });
    var gi = document.getElementById('id_grade');
    if (gi && gi.classList.contains('is-invalid')) hasErr = true;
    var marker = document.getElementById('__test_marker');
    if (!marker) {
        marker = document.createElement('div');
        marker.id = '__test_marker';
        document.body.appendChild(marker);
    }
    marker.setAttribute('data-has-error', hasErr ? 'yes' : 'no');
    marker.setAttribute('data-error-msg', errMsg);
"""

CSV_PATH = os.path.join(os.path.dirname(__file__), "TC-004_data.csv")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------
class TestGradeLevel1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        cls.driver.implicitly_wait(10)
        cls._login()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    @classmethod
    def _login(cls):
        driver = cls.driver
        driver.get(LOGIN_URL)
        driver.execute_script(
            "document.getElementById('username').value = arguments[0];"
            "document.getElementById('password').value = arguments[1];"
            "document.getElementById('login').submit();",
            ADMIN_USER,
            ADMIN_PASS,
        )
        time.sleep(3)
        driver.get(f"{BASE_URL}/course/view.php?id=10")
        time.sleep(2)

    # ------------------------------------------------------------------
    # Per-test helpers
    # ------------------------------------------------------------------
    def _fill_and_submit(self, grade_value):
        driver = self.driver
        driver.get(GRADER_URL)

        # Wait for grade field
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "id_grade"))
        )
        time.sleep(5)  # let TinyMCE / React fully initialise

        # Fill grade + feedback + notification
        driver.execute_script(_JS_SET_GRADE, grade_value)
        time.sleep(5)

        # Click Save changes
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@name='savechanges']"))
        )
        btn = driver.find_element(By.XPATH, "//button[@name='savechanges']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(5)

        # Inject error-detection marker
        driver.execute_script(_JS_CHECK_ERRORS)
        time.sleep(5)

    def _get_outcome(self):
        driver = self.driver
        markers_ok  = driver.find_elements(
            By.CSS_SELECTOR, '#__test_marker[data-has-error="no"]'
        )
        markers_err = driver.find_elements(
            By.CSS_SELECTOR, '#__test_marker[data-has-error="yes"]'
        )
        if markers_ok:
            return "success"
        if markers_err:
            msg = (markers_err[0].get_attribute("data-error-msg") or "").strip()
            return msg if msg else "fail"
        # Fallback: any visible inline error text
        errors = driver.find_elements(By.CSS_SELECTOR, "[id^='id_error_']")
        msgs = [(e.text or "").strip() for e in errors if (e.text or "").strip()]
        if msgs:
            return " | ".join(msgs)
        return "success"

    @staticmethod
    def _verify_text(driver, expected_text: str) -> bool:
        """Katalon Recorder verifyText: returns True iff expected_text appears
        (case-insensitive substring) anywhere in driver.page_source.
        Equivalent to: `verifyText | <text>` → `assertIn(text, page_source)`."""
        needle = (expected_text or "").lower().strip()
        if not needle:
            return False
        return needle in driver.page_source.lower()

    # ------------------------------------------------------------------
    # Dynamic test generation
    # ------------------------------------------------------------------
    @classmethod
    def _make_test(cls, row):
        def test_method(self):
            self._fill_and_submit(row["grade"])
            actual   = self._get_outcome()
            expected = row["expected_result"].strip()
            # success → outcome marker; otherwise → Katalon verifyText
            if expected.lower() == "success":
                ok = (actual == "success")
            else:
                ok = self._verify_text(self.driver, expected)
            self.assertTrue(
                ok,
                f"{row['test_case_id']}: verifyText FAILED — '{expected}' not in page (outcome='{actual}')"
                f" (grade='{row['grade']}')",
            )
        test_method.__name__ = f"test_{row['test_case_id'].replace('-', '_')}"
        test_method.__doc__  = (
            f"{row['test_case_id']}: grade='{row['grade']}', "
            f"expected={row['expected_result']}"
        )
        return test_method


def _load_tests():
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            method_name = f"test_{row['test_case_id'].replace('-', '_')}"
            setattr(
                TestGradeLevel1,
                method_name,
                TestGradeLevel1._make_test(row),
            )


_load_tests()

if __name__ == "__main__":
    unittest.main(verbosity=2)
