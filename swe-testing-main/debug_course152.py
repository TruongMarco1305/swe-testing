"""Quick debug: count activity references in course 152 across multiple URLs."""
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
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.execute_script("document.getElementById('loginbtn').click();")
    wait.until(EC.url_contains("/my/"))
    print("[OK] Logged in")

    urls_to_try = [
        "/course/view.php?id=152",
        "/course/view.php?id=152&section=0",
        "/mod/quiz/index.php?id=152",
    ]

    for path in urls_to_try:
        print(f"\n========== {path} ==========")
        driver.get(BASE_URL + path)
        time.sleep(4)
        print(f"Current URL: {driver.current_url}")
        print(f"Page title : {driver.title}")
        html = driver.page_source
        # Count quiz cmid references
        cmids_quiz = set(re.findall(r'/mod/quiz/view\.php\?id=(\d+)', html))
        cmids_data = set(re.findall(r'data-id="(\d+)"[^>]*activity', html))
        cmids_mod  = set(re.findall(r'id="module-(\d+)"', html))
        modedit   = set(re.findall(r'/course/modedit\.php\?update=(\d+)', html))
        print(f"  /mod/quiz/view.php?id=N         -> {len(cmids_quiz)} refs")
        print(f"  data-id=... activity            -> {len(cmids_data)} refs")
        print(f"  id=module-N                     -> {len(cmids_mod)} refs")
        print(f"  /course/modedit.php?update=N    -> {len(modedit)} refs")
        # Print first 5 quiz CMIDs
        if cmids_quiz:
            print(f"  Sample quiz cmids: {sorted(int(x) for x in cmids_quiz)[:10]}")
        # Save HTML for inspection
        out = f"debug_{path.replace('/', '_').replace('?', '_').replace('=','_').replace('&','_')}.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Saved HTML -> {out}")

finally:
    driver.quit()
