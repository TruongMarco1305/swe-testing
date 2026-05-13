"""Debug: enumerate categories and find hidden courses in /course/management.php."""
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://ihatetesting.moodlecloud.com"
USERNAME = "phuc.nguyen0310@hcmut.edu.vn"
PASSWORD = "Huuphuc0310@"

opts = webdriver.ChromeOptions()
opts.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
wait = WebDriverWait(driver, 20)

try:
    # Login
    driver.get(BASE_URL + "/login/index.php")
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    driver.execute_script("""
        var el = document.querySelector('.onetrust-pc-dark-filter');
        if (el) el.style.display = 'none';
        var b = document.getElementById('onetrust-banner-sdk');
        if (b) b.style.display = 'none';
    """)
    time.sleep(1)
    driver.execute_script("""
        document.getElementById('username').value = arguments[0];
        document.getElementById('password').value = arguments[1];
        document.getElementById('loginbtn').click();
    """, USERNAME, PASSWORD)
    wait.until(EC.url_contains("/my/"))
    print("[OK] Logged in")

    # 1. Enumerate all categories
    print("\n========== Categories ==========")
    driver.get(BASE_URL + "/course/management.php")
    time.sleep(3)
    html = driver.page_source
    # data-id="<categoryid>" on category items
    cat_ids = sorted(set(int(x) for x in re.findall(r'data-categoryid="(\d+)"|categoryid=(\d+)', html, re.I) for x in x if x))
    # Simpler: parse the categoryid query parameter from links
    cat_ids = sorted(set(int(m.group(1)) for m in re.finditer(r'[?&]categoryid=(\d+)', html)))
    print(f"  Found categoryid params: {cat_ids}")
    # Find category names
    for c in cat_ids[:20]:
        # try to extract category name via JS
        try:
            name = driver.execute_script(
                f"var e = document.querySelector('[data-id=\"{c}\"]'); return e ? e.innerText.split('\\n')[0] : ''"
            )
            print(f"    category {c}: '{name}'")
        except Exception:
            pass

    # 2. For each category, visit and look for courses
    print("\n========== Per-category course listings ==========")
    found_total = 0
    for c in cat_ids:
        driver.get(BASE_URL + f"/course/management.php?categoryid={c}")
        time.sleep(2)
        html = driver.page_source
        course_ids = sorted(set(int(x) for x in re.findall(r'/course/view\.php\?id=(\d+)', html)))
        sn_hits = sorted(set(re.findall(r'sn\d+_\w+', html)))
        fn_hits = sorted(set(re.findall(r'fn\d+_\w+', html)))
        if course_ids or sn_hits or fn_hits:
            print(f"\n  category {c}: {len(course_ids)} courses, sn:{len(sn_hits)} fn:{len(fn_hits)}")
            if course_ids[:10]:
                print(f"    course IDs: {course_ids[:10]}{'...' if len(course_ids)>10 else ''}")
            if sn_hits[:5]:
                print(f"    sn examples: {sn_hits[:5]}")
            if fn_hits[:5]:
                print(f"    fn examples: {fn_hits[:5]}")
            found_total += len(course_ids)

    print(f"\n========== TOTAL: {found_total} courses ==========")

    # 3. Try /admin/courses.php as alternative
    print("\n========== /admin/index.php?section=coursemgmt ==========")
    driver.get(BASE_URL + "/admin/index.php?section=coursemgmt")
    time.sleep(2)
    html = driver.page_source
    course_ids = sorted(set(int(x) for x in re.findall(r'/course/view\.php\?id=(\d+)', html)))
    print(f"  courses: {len(course_ids)}")

finally:
    driver.quit()
