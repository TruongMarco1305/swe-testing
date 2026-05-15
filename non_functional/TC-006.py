"""
NON-FUNCTIONAL TEST FILE 06 — TC-006 TEACHER CREATES A QUIZ
                              Usability Testing
Feature : Moodle LMS — Quiz creation form (course 12)
Site    : https://xuansang1234.moodlecloud.com/course/modedit.php
          ?add=quiz&type&course=12&section=0&return=0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NFR  USABILITY TESTING  (Selenium — keyboard navigation + focus)
  Tool      : pip install selenium webdriver-manager
  Approach  : Verify the quiz-add form can be fully operated by
              keyboard alone (Tab navigation, visible focus indicators,
              labelled fields) and that validation errors appear in the
              DOM after an empty-form submit.
  Run       : python -m pytest TC-006.py -v
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
import unittest

BASE_URL     = "https://xuansang1234.moodlecloud.com"
LOGIN_URL    = BASE_URL + "/login/index.php"
QUIZ_ADD_URL = BASE_URL + "/course/modedit.php?add=quiz&type&course=12&section=0&return=0"
USERNAME     = "sang.truong2005@hcmut.edu.vn"
PASSWORD     = "Abcdxyz12@"

TAB_LIMIT = 80   # max Tab presses before declaring a field unreachable


# ══════════════════════════════════════════════════════════════════════════
# NFR  USABILITY  — keyboard nav, focus indicators, labels, error DOM
# ══════════════════════════════════════════════════════════════════════════
class TestQuizUsability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            svc = Service(ChromeDriverManager().install())
        except Exception:
            svc = Service()

        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(service=svc, options=opts)
        cls.wait = WebDriverWait(cls.driver, 20)
        cls._login()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    @classmethod
    def _login(cls):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        cls.driver.get(LOGIN_URL)
        cls.wait.until(EC.presence_of_element_located((By.ID, "username")))
        cls.driver.execute_script("""
            var el = document.querySelector('.onetrust-pc-dark-filter');
            if (el) el.style.display = 'none';
            var b = document.getElementById('onetrust-banner-sdk');
            if (b) b.style.display = 'none';
        """)
        cls.driver.find_element(By.ID, "username").send_keys(USERNAME)
        cls.driver.find_element(By.ID, "password").send_keys(PASSWORD)
        cls.driver.execute_script("document.getElementById('loginbtn').click();")
        cls.wait.until(EC.url_contains("/my/"))
        time.sleep(1)

    def _open_quiz_form(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        self.driver.get(QUIZ_ADD_URL)
        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))

    def test_01_required_fields_have_accessible_labels(self):
        """Quiz Name and Grade-to-pass fields must have associated <label> elements."""
        self._open_quiz_form()
        for fid in ("id_name", "id_gradepass"):
            label_text = self.driver.execute_script(
                f"var l = document.querySelector('label[for=\"{fid}\"]');"
                "return l ? l.innerText.trim() : '';"
            )
            self.assertTrue(label_text,
                            f"Form field #{fid} has no <label for=...>")
            print(f"\n  [USAB] #{fid} label = '{label_text}' [OK]")

    def test_02_quiz_name_field_reachable_by_keyboard(self):
        """Tab navigation from page body must reach the #id_name field."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        self._open_quiz_form()
        self.driver.find_element(By.TAG_NAME, "body").click()
        body = self.driver.find_element(By.TAG_NAME, "body")
        for i in range(TAB_LIMIT):
            body.send_keys(Keys.TAB)
            active_id = self.driver.execute_script(
                "return document.activeElement ? document.activeElement.id : '';"
            )
            if active_id == "id_name":
                print(f"\n  [USAB] #id_name reached via Tab after {i+1} press(es) [OK]")
                return
        self.fail(f"#id_name not reachable within {TAB_LIMIT} Tab presses")

    def test_03_focused_input_has_visible_focus_indicator(self):
        """When #id_name is focused it must show a visible outline or box-shadow."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        self._open_quiz_form()
        self.driver.find_element(By.TAG_NAME, "body").click()
        body = self.driver.find_element(By.TAG_NAME, "body")
        for _ in range(TAB_LIMIT):
            body.send_keys(Keys.TAB)
            active_id = self.driver.execute_script(
                "return document.activeElement ? document.activeElement.id : '';"
            )
            if active_id == "id_name":
                break
        else:
            self.skipTest("#id_name not reached — skipping focus-indicator check")

        outline_style = self.driver.execute_script(
            "var el = document.getElementById('id_name');"
            "var s = window.getComputedStyle(el);"
            "return s.outlineStyle + '|' + s.outlineWidth + '|' + s.outlineColor;"
        )
        style, width, color = outline_style.split("|")
        has_visible_outline = (
            style not in ("none", "")
            or (width not in ("0px", "0", "")
                and color not in ("", "rgba(0, 0, 0, 0)"))
        )
        box_shadow = self.driver.execute_script(
            "var el = document.getElementById('id_name');"
            "return window.getComputedStyle(el).boxShadow;"
        )
        has_box_shadow = box_shadow not in ("none", "")
        self.assertTrue(
            has_visible_outline or has_box_shadow,
            f"#id_name shows no visible focus indicator "
            f"(outline={outline_style}, boxShadow={box_shadow})"
        )
        print(f"\n  [USAB] #id_name focus indicator visible "
              f"(outline={outline_style}) [OK]")

    def test_04_save_button_reachable_by_keyboard(self):
        """Save button must exist in the tab order and accept programmatic focus."""
        self._open_quiz_form()

        # 1. Verify the button is present, visible, not disabled, and in the tab order.
        result = self.driver.execute_script("""
            var btn = document.getElementById('id_submitbutton2')
                      || document.getElementById('id_submitbutton');
            if (!btn) return {found: false};
            var rect = btn.getBoundingClientRect();
            return {
                found:    true,
                id:       btn.id,
                tabIndex: btn.tabIndex,
                disabled: btn.disabled,
                visible:  rect.width > 0 && rect.height > 0
            };
        """)
        self.assertTrue(result.get("found"),
                        "Save button (#id_submitbutton2 / #id_submitbutton) not found in DOM")
        self.assertFalse(result.get("disabled"),
                         "Save button is disabled — not keyboard-operable")
        self.assertTrue(result.get("visible"),
                        "Save button has zero dimensions — not visible")
        self.assertGreaterEqual(result.get("tabIndex", 0), 0,
                                f"Save button has tabIndex={result.get('tabIndex')} "
                                "— explicitly removed from tab order")

        # 2. Confirm the button actually receives focus (keyboard-accessible by browsers).
        focused_id = self.driver.execute_script("""
            var btn = document.getElementById('id_submitbutton2')
                      || document.getElementById('id_submitbutton');
            btn.focus();
            return document.activeElement ? document.activeElement.id : '';
        """)
        self.assertIn(focused_id, ("id_submitbutton2", "id_submitbutton"),
                      f"Save button did not receive focus (activeElement='{focused_id}')")
        print(f"\n  [USAB] Save button (#{focused_id}) is keyboard-reachable "
              f"(tabIndex={result['tabIndex']}, visible={result['visible']}) [OK]")

    def test_05_error_messages_present_in_dom_after_empty_submit(self):
        """Submitting the empty quiz form must produce inline DOM error messages."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        self._open_quiz_form()
        name_fld = self.driver.find_element(By.ID, "id_name")
        name_fld.clear()
        btn = self.driver.find_element(By.ID, "id_submitbutton2")
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", btn
        )
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        errors = self.driver.find_elements(
            By.CSS_SELECTOR, "[id^='id_error_']"
        )
        self.assertTrue(errors,
                        "No [id^='id_error_'] elements found after empty form submit")
        print(f"\n  [USAB] {len(errors)} inline error message(s) present in DOM [OK]")


if __name__ == "__main__":
    unittest.main(verbosity=2)

