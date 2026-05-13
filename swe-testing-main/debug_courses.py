"""Debug: where do test courses actually live in Moodle?"""
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

    urls_to_try = [
        "/course/search.php?q=sn0",
        "/course/search.php?q=sn001_ssssssss",
        "/course/index.php",
        "/course/index.php?categoryid=1",
        "/course/management.php",
    ]

    for path in urls_to_try:
        print(f"\n========== {path} ==========")
        driver.get(BASE_URL + path)
        time.sleep(4)
        print(f"Current URL: {driver.current_url}")
        print(f"Page title : {driver.title}")
        html = driver.page_source
        # Find all course IDs referenced in the page
        course_ids = sorted(set(int(x) for x in re.findall(r'/course/view\.php\?id=(\d+)', html)))
        print(f"  /course/view.php?id=N refs: {len(course_ids)} unique ids")
        if course_ids:
            print(f"  Sample IDs: {course_ids[:15]}{'...' if len(course_ids) > 15 else ''}")
        # Find shortname/fullname mentions of test patterns
        sn_hits = re.findall(r'sn\d+_\w+', html)
        fn_hits = re.findall(r'fn\d+_\w+', html)
        print(f"  Mentions sn*_*: {len(sn_hits)}  fn*_*: {len(fn_hits)}")
        if sn_hits[:5]:
            print(f"  Sample sn: {sn_hits[:5]}")

finally:
    driver.quit()
