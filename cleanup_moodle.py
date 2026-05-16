"""
cleanup_moodle.py - Delete test data created by Project #3 test suites
                    Group 11 - Software Testing 2025S2

WHAT THIS SCRIPT DELETES
  - Users with names matching the TC-001 patterns       (usr*, test_*, ...)
  - Courses with names matching the TC-002 patterns     (fn*, sn*, ...)
    ONLY from Category 1 (Miscellaneous). "DO NOT DELETE" and all other
    categories are never touched.
  - Assignments inside course 10 (TC-003)               (an*, a, as, ...)
  - Calendar events with TC-005 patterns                (t*, ti, ...)
  - Quizzes inside course 12 (TC-006 + NFR files)       (qn*, perf_*, xss_*)

USAGE
  python cleanup_moodle.py --all                # Clean up everything
  python cleanup_moodle.py --users              # Only users
  python cleanup_moodle.py --quizzes            # Only quizzes in course 12
  python cleanup_moodle.py --courses            # Only courses
  python cleanup_moodle.py --assignments        # Only assignments in course 10
  python cleanup_moodle.py --events             # Only calendar events
  python cleanup_moodle.py --dry-run --all      # List matches without deleting
  python cleanup_moodle.py --headless --all     # Run without showing browser

NOTES
  - Builds on the same Selenium/webdriver-manager stack as the test suite
  - Logs every deletion to the console with [DEL] / [SKIP] / [DRY] prefixes
  - Safe to re-run: idempotent (skips items already deleted)
  - DOES NOT delete the admin/test account itself, courses 10 or 12, or
    the Moodle built-in 'admin' user
"""

import argparse
import re
import sys
import time
from urllib.parse import urlencode

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                         TimeoutException,
                                         WebDriverException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
try:
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    ChromeDriverManager = None

# ── Configuration ──────────────────────────────────────────────────────────
BASE_URL  = "https://xuansang1234.moodlecloud.com"
LOGIN_URL = BASE_URL + "/login/index.php"
USERNAME  = "sang.truong2005@hcmut.edu.vn"
PASSWORD  = "Abcdxyz12@"

COURSE_TC003_ASSIGN = 10    # Assignment test course (TC_003_MAIN)
COURSE_TC006_QUIZ   = 12    # Quiz test course (TC_004_MAIN reused for TC-006)

# Protected items - NEVER delete these no matter what
PROTECTED_USERNAMES = {"admin", USERNAME.lower(), "guest", "sang.truong2005@hcmut.edu.vn"}
PROTECTED_COURSE_IDS = {1, COURSE_TC003_ASSIGN, COURSE_TC006_QUIZ}

# Match patterns - any item whose name matches ANY of these gets deleted
USER_PATTERNS = [
    re.compile(r"^usr\d+_", re.IGNORECASE),
    re.compile(r"^test_", re.IGNORECASE),
    re.compile(r"^username\d+", re.IGNORECASE),
]
COURSE_FULLNAME_PATTERNS = [
    re.compile(r"^f$", re.IGNORECASE),              # exact 'f' (TC-002-003)
    re.compile(r"^fn$", re.IGNORECASE),             # exact 'fn' (TC-002-004)
    re.compile(r"^fn\d", re.IGNORECASE),            # fn001..., fn005..., fn006..., fn034...
    re.compile(r"^fn_", re.IGNORECASE),             # legacy variants
    re.compile(r"^test_course", re.IGNORECASE),
]
COURSE_SHORTNAME_PATTERNS = [
    re.compile(r"^s$", re.IGNORECASE),              # exact 's' (TC-002-008)
    re.compile(r"^sn$", re.IGNORECASE),             # exact 'sn' (TC-002-009)
    re.compile(r"^sn\d", re.IGNORECASE),            # sn001..., sn005..., sn011..., sn012...
    re.compile(r"^sn_", re.IGNORECASE),
]
ASSIGN_PATTERNS = [
    re.compile(r"^an\d+_", re.IGNORECASE),
    re.compile(r"^test_assign", re.IGNORECASE),
]
QUIZ_PATTERNS = [
    re.compile(r"^qn\d+_", re.IGNORECASE),
    re.compile(r"^perf_", re.IGNORECASE),
    re.compile(r"^test_quiz", re.IGNORECASE),
    # XSS/SQLi payloads used in NFR test_06 - match any quote style
    re.compile(r"xss", re.IGNORECASE),
    re.compile(r"alert\s*\(", re.IGNORECASE),
    re.compile(r"onerror\s*=", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"<img", re.IGNORECASE),
    re.compile(r"OR\s+[\"']?1[\"']?\s*=\s*[\"']?1", re.IGNORECASE),
    re.compile(r"mdl_quiz", re.IGNORECASE),
]
EVENT_PATTERNS = [
    re.compile(r"^t\d+_", re.IGNORECASE),
    re.compile(r"^test_event", re.IGNORECASE),
]

# ── Pretty printers (ASCII only for cross-platform safety) ────────────────
def log_section(msg):  print(f"\n{'=' * 70}\n  {msg}\n{'=' * 70}")
def log_step(msg):     print(f">> {msg}")
def log_del(msg):      print(f"  [DEL]  {msg}")
def log_dry(msg):      print(f"  [DRY]  {msg}")
def log_skip(msg):     print(f"  [SKIP] {msg}")
def log_warn(msg):     print(f"  [WARN] {msg}")
def log_ok(msg):       print(f"  [OK]   {msg}")


# ══════════════════════════════════════════════════════════════════════════
# Browser setup + Moodle login
# ══════════════════════════════════════════════════════════════════════════
def make_driver(headless=False):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
    else:
        opts.add_argument("--start-maximized")
    if ChromeDriverManager is not None:
        try:
            return webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=opts,
            )
        except Exception:
            pass
    opts.browser_version = "stable"
    return webdriver.Chrome(service=Service(), options=opts)


def login(driver, wait):
    log_step("Logging in as admin")
    driver.get(LOGIN_URL)
    # If we are already logged-in, Moodle redirects directly to /my/
    try:
        WebDriverWait(driver, 3).until(EC.url_contains("/my/"))
        log_ok("Already logged in (session persisted)")
        return
    except TimeoutException:
        pass
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    # Dismiss OneTrust cookie banner if present
    driver.execute_script("""
        var el = document.querySelector('.onetrust-pc-dark-filter');
        if (el) el.style.display = 'none';
        var b = document.getElementById('onetrust-banner-sdk');
        if (b) b.style.display = 'none';
    """)
    time.sleep(1)   # let any banner-removal redraw finish before grabbing inputs
    # Use JS to set credentials and submit - avoids StaleElementReferenceException
    # when the banner overlay re-renders the inputs.
    driver.execute_script("""
        var u = document.getElementById('username');
        var p = document.getElementById('password');
        if (u) { u.value = arguments[0]; u.dispatchEvent(new Event('input',{bubbles:true})); }
        if (p) { p.value = arguments[1]; p.dispatchEvent(new Event('input',{bubbles:true})); }
        var btn = document.getElementById('loginbtn');
        if (btn) btn.click();
    """, USERNAME, PASSWORD)
    wait.until(EC.url_contains("/my/"))
    log_ok("Login successful")


def get_sesskey(driver):
    """Extract Moodle's session key (required for all destructive actions)."""
    sesskey = driver.execute_script("return (window.M && M.cfg) ? M.cfg.sesskey : null")
    if not sesskey:
        # Fallback: look for sesskey in any form
        try:
            el = driver.find_element(By.CSS_SELECTOR, "input[name='sesskey']")
            sesskey = el.get_attribute("value")
        except Exception:
            pass
    return sesskey


def matches_any(name, patterns):
    if not name:
        return False
    return any(p.search(name) for p in patterns)


# ══════════════════════════════════════════════════════════════════════════
# 1a. USERS (BULK)  -  /admin/user/user_bulk.php
#     Mirrors the TC-001-Cleanup approach from the original Katalon recorder.
#     Filters by 'usr' prefix, then adds all matches and deletes in one shot.
# ══════════════════════════════════════════════════════════════════════════
def cleanup_users_bulk(driver, wait, dry_run=False):
    log_section("USERS (bulk) - /admin/user/user_bulk.php")
    driver.get(f"{BASE_URL}/admin/user/user_bulk.php")
    # Wait for the listbox (always present) - showall is a button we click later
    try:
        wait.until(EC.presence_of_element_located((By.ID, "removeselect")))
    except TimeoutException:
        log_warn("Could not load bulk user actions page - falling back to per-user delete")
        return cleanup_users(driver, wait, dry_run=dry_run)

    # Click "Show all" so every user is visible in the Available listbox.
    # Try multiple selectors — the button varies across Moodle versions.
    for sel in [(By.ID, "showall"),
                (By.CSS_SELECTOR, "input[value*='Show all']"),
                (By.CSS_SELECTOR, "button[name='showall']"),
                (By.XPATH, "//input[@type='submit' and contains(@value,'Show all')]"),
                (By.XPATH, "//button[contains(.,'Show all')]")]:
        try:
            btn = driver.find_element(*sel)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            break
        except NoSuchElementException:
            continue
    else:
        log_skip("'Show all' button not found — proceeding with visible users")
        time.sleep(1)

    # Read all user options from the "Available users" listbox (#removeselect)
    options = driver.find_elements(By.CSS_SELECTOR, "select#removeselect option")
    candidates = []
    for opt in options:
        try:
            uid_raw = (opt.get_attribute("value") or "").strip()
            if not uid_raw.isdigit():
                continue
            uid = int(uid_raw)
            label = (opt.text or "").strip()
            # Skip protected accounts
            label_lc = label.lower()
            if any(p in label_lc for p in PROTECTED_USERNAMES):
                continue
            # Match by pattern - tests create users with emails like usr001_nom@test.com
            # Bulk listbox usually shows "Lastname Firstname (email)" or "First Last, email"
            if any(matches_any(part.strip("()<>,"), USER_PATTERNS)
                   for part in re.split(r"\s+", label)):
                candidates.append((uid, label))
        except ValueError:
            continue

    log_step(f"Found {len(candidates)} test users to delete in bulk")
    if not candidates:
        return 0

    if dry_run:
        for uid, label in candidates:
            display = (label[:70] + "...") if len(label) > 70 else label
            log_dry(f"user {uid:>6}  '{display}'")
        return len(candidates)

    # Multi-select matching users with ActionChains (Ctrl+click) so that
    # Moodle's listbox JS receives real mouse events and recognises the selection.
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys as _Keys

    uid_values = {str(uid) for uid, _ in candidates}
    matching_opts = [
        opt for opt in driver.find_elements(By.CSS_SELECTOR, "select#removeselect option")
        if (opt.get_attribute("value") or "").strip() in uid_values
    ]
    if not matching_opts:
        log_warn("No matching options found in Available listbox — falling back to per-user delete")
        return cleanup_users(driver, wait, dry_run=dry_run)

    actions = ActionChains(driver)
    actions.click(matching_opts[0])
    for opt in matching_opts[1:]:
        actions.key_down(_Keys.CONTROL).click(opt).key_up(_Keys.CONTROL)
    actions.perform()
    time.sleep(1)

    # Click "Add to selection"
    try:
        add_btn = driver.find_element(By.ID, "add")
    except NoSuchElementException:
        add_btn = driver.find_element(By.CSS_SELECTOR, "input[name='add']")
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(2)

    # Select action "Delete" from the dropdown
    try:
        from selenium.webdriver.support.ui import Select as SeleniumSelect
        SeleniumSelect(driver.find_element(By.ID, "id_action")).select_by_visible_text("Delete")
    except Exception as e:
        log_warn(f"Could not select Delete action: {e}")
        return 0
    time.sleep(1)

    # Click "Go"
    try:
        go_btn = driver.find_element(By.ID, "id_doaction")
        driver.execute_script("arguments[0].click();", go_btn)
    except NoSuchElementException:
        log_warn("Go button not found")
        return 0

    # Confirmation page - click "Yes"
    try:
        confirm_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Yes')] | //input[@type='submit' and @value='Yes']")))
        driver.execute_script("arguments[0].click();", confirm_btn)
        time.sleep(3)
        log_ok(f"Bulk delete submitted for {len(candidates)} users")
        return len(candidates)
    except TimeoutException:
        log_warn("Confirmation button not found - users may not be deleted")
        return 0


# ══════════════════════════════════════════════════════════════════════════
# 1b. USERS (per-user fallback)  -  /admin/user.php
# ══════════════════════════════════════════════════════════════════════════
def cleanup_users(driver, wait, dry_run=False):
    log_section("USERS - scanning /admin/user.php")
    driver.get(f"{BASE_URL}/admin/user.php?sort=username&dir=ASC&perpage=5000")
    # Moodle 4.x: try several selectors as the table id/class varies by theme
    user_table_selectors = [
        (By.ID, "users"),
        (By.CSS_SELECTOR, "table.flexible"),
        (By.CSS_SELECTOR, "table.userinfobox"),
        (By.CSS_SELECTOR, ".userlist table"),
        (By.CSS_SELECTOR, "table.generaltable"),
    ]
    table_found = False
    for sel in user_table_selectors:
        try:
            WebDriverWait(driver, 6).until(EC.presence_of_element_located(sel))
            table_found = True
            break
        except TimeoutException:
            continue
    if not table_found:
        log_warn("Could not load user admin page - skipping")
        log_warn(f"  current URL: {driver.current_url}")
        return 0

    sesskey = get_sesskey(driver)
    if not sesskey:
        log_warn("Could not extract sesskey - aborting user cleanup")
        return 0

    # Collect all candidates from any user table on the page
    rows = driver.find_elements(By.CSS_SELECTOR,
                                "table.generaltable tbody tr, table#users tbody tr, table.flexible tbody tr")
    candidates = []
    for tr in rows:
        try:
            # First column is usually first/last name link, which contains ?id=<uid>
            links = tr.find_elements(By.CSS_SELECTOR, "a[href*='user/profile.php'], a[href*='user/view.php']")
            uid = None
            for link in links:
                m = re.search(r"[?&]id=(\d+)", link.get_attribute("href") or "")
                if m:
                    uid = int(m.group(1))
                    break
            if uid is None:
                continue

            # Username column might be 2nd, 3rd, or 4th depending on theme
            cells = tr.find_elements(By.TAG_NAME, "td")
            row_text = " ".join((c.text or "").strip() for c in cells)
            # Pull out a representative username: first 'usr*' token if any
            username = ""
            for token in row_text.split():
                token = token.strip()
                if matches_any(token, USER_PATTERNS):
                    username = token
                    break
            if not username:
                # Otherwise use the first cell text as display
                username = cells[0].text.strip() if cells else f"id={uid}"

            if username.lower() in PROTECTED_USERNAMES:
                continue
            if matches_any(username, USER_PATTERNS) or \
               any(matches_any(part, USER_PATTERNS) for part in row_text.split()):
                candidates.append((uid, username))
        except (NoSuchElementException, ValueError):
            continue

    log_step(f"Found {len(candidates)} test users to delete")
    if not candidates:
        return 0

    if dry_run:
        for uid, username in candidates:
            log_dry(f"user {uid:>6}  '{username}'")
        return len(candidates)

    deleted = 0
    # Use JS form-POST to actually commit (analogous to the quiz fast-path).
    # Moodle's user delete confirm page has TWO buttons (Delete / Cancel),
    # and a generic XPath could click the wrong one - JS POST avoids this
    # entirely by submitting the form's `confirm=1` field directly.
    driver.set_script_timeout(60)
    js_user_delete = """
        const done = arguments[arguments.length - 1];
        const uid = arguments[0];
        const sk  = arguments[1];
        fetch('/admin/user.php?delete=' + uid + '&sesskey=' + sk,
              {credentials: 'include'})
          .then(r => r.text())
          .then(html => {
              const parser = new DOMParser();
              const doc = parser.parseFromString(html, 'text/html');
              let form = null;
              doc.querySelectorAll('form').forEach(f => {
                  if (f.action && f.action.indexOf('/admin/user.php') !== -1) form = f;
              });
              if (!form) form = doc.querySelector('form');
              if (!form) return done({status: 'no-form'});
              const fd = new FormData(form);
              if (!fd.has('confirm')) fd.set('confirm', '1');
              if (!fd.has('delete'))  fd.set('delete', uid);
              const params = new URLSearchParams();
              fd.forEach((v, k) => params.append(k, v));
              return fetch(form.action, {
                  method: 'POST',
                  credentials: 'include',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: params.toString()
              }).then(r => done({status: r.status, url: r.url}));
          })
          .catch(e => done({status: 'err', error: e.message}));
    """
    for uid, username in candidates:
        try:
            result = driver.execute_async_script(js_user_delete, uid, sesskey)
            status = result.get("status") if isinstance(result, dict) else result
            if isinstance(status, int) and status in (200, 302, 303):
                log_del(f"user {uid:>6}  HTTP {status}  '{username}'")
                deleted += 1
            else:
                log_skip(f"user {uid}  '{username}' - result={result}")
        except WebDriverException as e:
            log_warn(f"user {uid}  '{username}' - {e.__class__.__name__}")
    return deleted


# ══════════════════════════════════════════════════════════════════════════
# 2. COURSES  -  /course/management.php?categoryid=4  (Category 1 only)
#    Uses the admin "Manage courses and categories" bulk-delete UI.
#    Never touches "DO NOT DELETE" or any other category.
# ══════════════════════════════════════════════════════════════════════════
def cleanup_courses(driver, wait, dry_run=False, purge_all=False):
    log_section("COURSES - /course/management.php?categoryid=4 (Category 1 only)")
    # Use a large perpage so pagination is rarely needed.
    MGMT_URL = f"{BASE_URL}/course/management.php?categoryid=4&perpage=200"

    # ─── Phase 1: enumerate matching courses in Category 1 ────────────────
    candidates = []
    seen_cids  = set()
    page_num   = 0

    while True:
        url = MGMT_URL + (f"&page={page_num}" if page_num else "")
        driver.get(url)
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "li.listitem-course, #course-listing, .management-course-listing")))
        except TimeoutException:
            if page_num == 0:
                log_warn("Could not load /course/management.php — skipping course cleanup")
                return 0
            break

        items = driver.find_elements(By.CSS_SELECTOR, "li.listitem-course")
        if not items:
            break

        found_new = False
        for li in items:
            cid_raw = (li.get_attribute("data-id") or "").strip()
            if not cid_raw.isdigit():
                continue
            cid = int(cid_raw)
            if cid in seen_cids or cid in PROTECTED_COURSE_IDS:
                continue
            seen_cids.add(cid)
            found_new = True

            # Full name
            name = ""
            try:
                name_el = li.find_element(By.CSS_SELECTOR,
                    ".coursename a, a.coursename, .course-title a")
                name = (name_el.text or "").strip()
            except NoSuchElementException:
                pass
            if not name:
                name = f"id={cid}"

            # Short name (shown as "Short name: SN001" in the detail line)
            short = ""
            try:
                short_el = li.find_element(By.CSS_SELECTOR,
                    ".shortname, .course-shortname, [data-type='shortname']")
                short = re.sub(r"^short\s*name\s*:?\s*", "",
                               (short_el.text or "").strip(),
                               flags=re.IGNORECASE).strip()
            except NoSuchElementException:
                pass

            if purge_all:
                candidates.append((cid, name))
            elif (matches_any(name,  COURSE_FULLNAME_PATTERNS) or
                  matches_any(short, COURSE_SHORTNAME_PATTERNS) or
                  matches_any(name,  COURSE_SHORTNAME_PATTERNS)):
                candidates.append((cid, name))

        if not found_new:
            break

        # Advance to next page if a Next link exists
        try:
            driver.find_element(By.CSS_SELECTOR,
                ".pagination .page-item:not(.disabled) a[aria-label='Next'], "
                "a.next[href*='page='], a[rel='next']")
            page_num += 1
        except NoSuchElementException:
            break

    log_step(f"Found {len(candidates)} course(s) in Category 1 to {'list' if dry_run else 'delete'}")
    if not candidates:
        return 0

    if dry_run:
        for cid, name in candidates:
            display = (name[:60] + "...") if len(name) > 60 else name
            log_dry(f"course {cid:>6}  '{display}'")
        return len(candidates)

    # ─── Phase 2: per-course delete via /course/delete.php?id=N ──────────
    # Moodle Cloud's management page does not reliably expose the bulk-action
    # <select> in its DOM (it is JS-gated and varies by version).  Deleting
    # one course at a time via the dedicated delete endpoint is simpler and
    # works with every Moodle version / hosting arrangement.
    deleted = 0
    for cid, name in candidates:
        display = (name[:60] + "...") if len(name) > 60 else name
        try:
            driver.get(f"{BASE_URL}/course/delete.php?id={cid}")
            # Wait for the confirmation page form to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "form, .confirmation-dialogue, .mform")))
            # Click the "Delete" / "Yes" confirm button
            confirm_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
                By.XPATH,
                "//button[normalize-space(.)='Delete'] | "
                "//input[@type='submit' and @value='Delete'] | "
                "//button[normalize-space(.)='Yes'] | "
                "//input[@type='submit' and @value='Yes'] | "
                "//button[contains(@class,'btn-danger') and contains(.,'Delete')]"
            )))
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", confirm_btn)
            driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)   # give Moodle time to process; no redirect check needed
            log_del(f"course {cid:>6}  '{display}'")
            deleted += 1
        except (TimeoutException, NoSuchElementException) as exc:
            log_warn(f"course {cid}  '{display}' - {exc.__class__.__name__}")
        except WebDriverException as exc:
            log_warn(f"course {cid}  '{display}' - {exc.__class__.__name__}")

    return deleted


# ══════════════════════════════════════════════════════════════════════════
# 3. ACTIVITIES IN COURSE  (quizzes / assignments)
# ══════════════════════════════════════════════════════════════════════════
def cleanup_activities_in_course(driver, wait, course_id, patterns, label,
                                  dry_run=False):
    log_section(f"{label.upper()} - scanning course {course_id}")
    driver.get(f"{BASE_URL}/course/view.php?id={course_id}")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-content")))
    except TimeoutException:
        log_warn(f"Could not load course {course_id} - skipping")
        return 0

    sesskey = get_sesskey(driver)
    if not sesskey:
        log_warn("Could not extract sesskey - aborting activity cleanup")
        return 0

    # ── Use Moodle's per-type listing page (e.g. /mod/quiz/index.php?id=<courseid>)
    # which lists every activity of that type in a flat table regardless of
    # section / page format. This is much more reliable than scanning the
    # course view page DOM.
    candidates = []
    type_url_map = {
        "quizzes":     "mod/quiz/index.php",
        "assignments": "mod/assign/index.php",
    }
    listing_path = type_url_map.get(label)
    if listing_path:
        listing_url = f"{BASE_URL}/{listing_path}?id={course_id}"
        log_step(f"Listing activities via {listing_path}?id={course_id}")
        driver.get(listing_url)
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table.generaltable, .generaltable")))
        except TimeoutException:
            log_warn(f"Could not load {listing_url}")
        # Each row has a link like /mod/quiz/view.php?id=<cmid>
        rows = driver.find_elements(By.CSS_SELECTOR, "table.generaltable tbody tr")
        seen_cmids = set()
        for tr in rows:
            try:
                links = tr.find_elements(By.CSS_SELECTOR, "a[href*='view.php']")
                cmid = None
                for a in links:
                    m = re.search(r"[?&]id=(\d+)", a.get_attribute("href") or "")
                    if m:
                        cmid = int(m.group(1))
                        break
                if cmid is None or cmid in seen_cmids:
                    continue
                seen_cmids.add(cmid)
                # Activity name is typically in the 2nd column ("Name")
                # but can also be in 3rd column depending on theme. Try links first.
                name = ""
                for a in links:
                    text = (a.text or "").strip()
                    if text:
                        name = text
                        break
                if not name:
                    cells = tr.find_elements(By.TAG_NAME, "td")
                    name = " ".join((c.text or "").strip() for c in cells[:3])
                if matches_any(name, patterns):
                    candidates.append((cmid, name))
            except (NoSuchElementException, ValueError):
                continue
        log_step(f"Listing page returned {len(rows)} rows, {len(candidates)} match patterns")

    # Fallback: if listing didn't work, scan the course view DOM
    if not candidates:
        log_step("Falling back to course-view DOM scan")
        driver.get(f"{BASE_URL}/course/view.php?id={course_id}")
        time.sleep(3)
        # Restrict to the course-content area so we don't pick up activities
        # from nav drawers belonging to other courses.
        activities = driver.find_elements(
            By.CSS_SELECTOR,
            ".course-content li.activity[data-id], "
            ".course-content li.activity[id^='module-'], "
            "main li.activity[data-id], "
            "main li.activity[id^='module-']")
        if not activities:
            # Last resort: whole page (will catch nav drawer too)
            activities = driver.find_elements(
                By.CSS_SELECTOR, "li.activity[data-id], li.activity[id^='module-']")
        seen_cmids = set()
        for a in activities:
            try:
                cmid_attr = a.get_attribute("data-id") or ""
                if not cmid_attr.isdigit():
                    node_id = a.get_attribute("id") or ""
                    m = re.match(r"module-(\d+)", node_id)
                    if m:
                        cmid_attr = m.group(1)
                if not cmid_attr.isdigit():
                    continue
                cmid = int(cmid_attr)
                if cmid in seen_cmids:
                    continue
                seen_cmids.add(cmid)
                # Prefer raw data-activityname attribute - preserves special chars
                name = ""
                try:
                    inner = a.find_element(By.CSS_SELECTOR, "[data-activityname]")
                    name = (inner.get_attribute("data-activityname") or "").strip()
                except NoSuchElementException:
                    pass
                if not name:
                    try:
                        name_el = a.find_element(By.CSS_SELECTOR,
                            ".activityname, .activity-instance .stretched-link, .instancename")
                        name = name_el.text.strip()
                    except NoSuchElementException:
                        name = (a.text or "").splitlines()[0].strip()
                # Clean trailing type-label noise
                name_lines = [ln.strip() for ln in name.splitlines() if ln.strip()]
                name_lines = [ln for ln in name_lines if ln.lower() not in
                              ("quiz","assignment","forum","resource","page","label")]
                name = " ".join(name_lines) if name_lines else name.replace("\n"," ").strip()
                if matches_any(name, patterns):
                    candidates.append((cmid, name))
            except (NoSuchElementException, ValueError):
                continue

    log_step(f"Found {len(candidates)} test {label} to delete in course {course_id}")
    if not candidates:
        return 0

    if dry_run:
        for cmid, name in candidates:
            display = (name[:60] + "...") if len(name) > 60 else name
            log_dry(f"{label[:-1]} cmid={cmid:>6}  '{display}'")
        return len(candidates)

    # ── FAST PATH: fetch the delete confirmation page once per activity,
    # parse the form with DOMParser to capture EVERY hidden field, then POST
    # it back. We follow redirects so the final HTTP status reflects whether
    # the deletion actually committed (Moodle redirects to course view with
    # 200 OK on success; returns 400/403 on missing CSRF / sesskey mismatch).
    driver.set_script_timeout(60)
    js_post = """
        const done = arguments[arguments.length - 1];
        const cmid = arguments[0];
        const sesskey = arguments[1];
        fetch('/course/mod.php?delete=' + cmid + '&sesskey=' + sesskey,
              {credentials: 'include'})
          .then(r => r.text())
          .then(html => {
              const parser = new DOMParser();
              const doc = parser.parseFromString(html, 'text/html');
              // Pick the form whose action targets /course/mod.php (the delete form)
              let form = null;
              doc.querySelectorAll('form').forEach(f => {
                  if (f.action && f.action.indexOf('/course/mod.php') !== -1) form = f;
              });
              if (!form) form = doc.querySelector('form');
              if (!form) return done('no-form');
              const fd = new FormData(form);
              // Ensure confirm flag is set (Moodle requires it)
              if (!fd.has('confirm')) fd.set('confirm', '1');
              const params = new URLSearchParams();
              fd.forEach((v, k) => params.append(k, v));
              return fetch(form.action, {
                  method: 'POST',
                  credentials: 'include',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: params.toString()
              }).then(r => done({status: r.status, url: r.url}));
          })
          .catch(e => done({status: 'err', error: e.message}));
    """
    deleted = 0
    for cmid, name in candidates:
        display = (name[:60] + "...") if len(name) > 60 else name
        try:
            result = driver.execute_async_script(js_post, cmid, sesskey)
            status = result.get("status") if isinstance(result, dict) else result
            final_url = result.get("url", "") if isinstance(result, dict) else ""
            if isinstance(status, int) and status in (200, 302, 303):
                # Server redirected to course view = delete committed
                committed = "/course/view.php" in final_url or status in (302, 303)
                tag = "DEL" if committed else "DEL?"
                if committed:
                    log_del(f"{label[:-1]} cmid={cmid:>6}  HTTP {status}  '{display}'")
                    deleted += 1
                else:
                    log_skip(f"{label[:-1]} cmid={cmid:>6}  HTTP {status} final={final_url}")
            else:
                log_skip(f"{label[:-1]} cmid={cmid:>6}  result={result}")
        except WebDriverException as e:
            log_warn(f"{label[:-1]} cmid={cmid}  '{display}' - {e.__class__.__name__}")
    return deleted


# ══════════════════════════════════════════════════════════════════════════
# 4. CALENDAR EVENTS  -  /calendar/view.php?view=upcoming
# ══════════════════════════════════════════════════════════════════════════
def cleanup_calendar_events(driver, wait, dry_run=False):
    log_section("CALENDAR EVENTS - scanning /calendar/view.php?view=upcoming")
    driver.get(f"{BASE_URL}/calendar/view.php?view=upcoming")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".eventlist, .maincalendar")))
    except TimeoutException:
        log_warn("Could not load calendar - skipping")
        return 0

    sesskey = get_sesskey(driver)
    if not sesskey:
        log_warn("Could not extract sesskey - aborting calendar cleanup")
        return 0

    # Collect event IDs and names from upcoming list
    candidates = []
    events = driver.find_elements(By.CSS_SELECTOR,
        ".eventlist .event, .event-name a, a[href*='view.php?view=day']")
    seen_ids = set()
    for ev in events:
        try:
            href = ev.get_attribute("href") or ""
            m = re.search(r"event_id=(\d+)|[&?]id=(\d+)", href)
            if not m:
                continue
            eid = int(m.group(1) or m.group(2))
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            name = (ev.text or "").strip()
            if matches_any(name, EVENT_PATTERNS):
                candidates.append((eid, name))
        except (NoSuchElementException, ValueError):
            continue

    log_step(f"Found {len(candidates)} test calendar events to delete")
    if not candidates:
        return 0

    if dry_run:
        for eid, name in candidates:
            display = (name[:60] + "...") if len(name) > 60 else name
            log_dry(f"event {eid:>6}  '{display}'")
        return len(candidates)

    deleted = 0
    for eid, name in candidates:
        display = (name[:60] + "...") if len(name) > 60 else name
        try:
            # /calendar/delete.php?id=<id>&sesskey=<key>
            driver.get(f"{BASE_URL}/calendar/delete.php?id={eid}")
            try:
                btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='submit' and contains(., 'Delete')] | "
                               "//input[@type='submit' and @value='Delete']")))
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                log_del(f"event {eid:>6}  '{display}'")
                deleted += 1
            except TimeoutException:
                log_skip(f"event {eid} - confirm button not found")
        except WebDriverException as e:
            log_warn(f"event {eid}  '{display}' - {e.__class__.__name__}")
    return deleted


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════
def parse_args():
    p = argparse.ArgumentParser(
        description="Clean up Moodle test data created by Project #3 test suites")
    p.add_argument("--all", action="store_true", help="Clean every category")
    p.add_argument("--users", action="store_true", help="Delete test users (TC-001)")
    p.add_argument("--courses", action="store_true", help="Delete test courses (TC-002)")
    p.add_argument("--assignments", action="store_true",
                   help="Delete test assignments in course 10 (TC-003)")
    p.add_argument("--quizzes", action="store_true",
                   help="Delete test quizzes in course 12 (TC-006, NFR)")
    p.add_argument("--events", action="store_true",
                   help="Delete test calendar events (TC-005)")
    p.add_argument("--purge-courses", action="store_true",
                   help="Delete EVERY non-protected course (ignores name patterns). "
                        "Implies --courses. Use with care - wipes Category 1 etc.")
    p.add_argument("--dry-run", action="store_true",
                   help="List matching items without deleting them")
    p.add_argument("--headless", action="store_true",
                   help="Run browser headless (no UI)")
    return p.parse_args()


def main():
    args = parse_args()
    flags = (args.all, args.users, args.courses, args.assignments,
             args.quizzes, args.events, args.purge_courses)
    if not any(flags):
        print("ERROR: no cleanup target specified. Use --all or one of:")
        print("       --users --courses --assignments --quizzes --events")
        print("       --purge-courses (wipe every non-protected course)")
        print("       Add --dry-run to preview without deleting.")
        sys.exit(1)

    run_users  = args.all or args.users
    run_course = args.all or args.courses or args.purge_courses
    run_assign = args.all or args.assignments
    run_quiz   = args.all or args.quizzes
    run_event  = args.all or args.events

    log_section("MOODLE CLEANUP - Project #3 Group 11")
    print(f"  Target site : {BASE_URL}")
    print(f"  Admin user  : {USERNAME}")
    print(f"  Mode        : {'DRY-RUN (no deletion)' if args.dry_run else 'DELETE'}")
    print(f"  Headless    : {args.headless}")

    driver = make_driver(headless=args.headless)
    wait = WebDriverWait(driver, 20)
    totals = {}
    try:
        login(driver, wait)

        if run_quiz:
            totals["quizzes"] = cleanup_activities_in_course(
                driver, wait, COURSE_TC006_QUIZ, QUIZ_PATTERNS, "quizzes",
                dry_run=args.dry_run)
        if run_assign:
            totals["assignments"] = cleanup_activities_in_course(
                driver, wait, COURSE_TC003_ASSIGN, ASSIGN_PATTERNS, "assignments",
                dry_run=args.dry_run)
        if run_event:
            totals["events"] = cleanup_calendar_events(driver, wait,
                                                       dry_run=args.dry_run)
        if run_users:
            # Use bulk delete (mirrors TC-001-Cleanup in the Katalon recorder)
            totals["users"] = cleanup_users_bulk(driver, wait, dry_run=args.dry_run)
        if run_course:
            totals["courses"] = cleanup_courses(driver, wait,
                                                 dry_run=args.dry_run,
                                                 purge_all=args.purge_courses)

        log_section("SUMMARY")
        verb = "Would delete" if args.dry_run else "Deleted"
        for k, v in totals.items():
            print(f"  {verb:<14} {v:>4}  {k}")
        print(f"  {'TOTAL':<14} {sum(totals.values()):>4}")
    except KeyboardInterrupt:
        print("\n[interrupted]")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()