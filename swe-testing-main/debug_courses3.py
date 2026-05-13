"""Try /course/view.php?name=<shortname> to find specific test courses."""
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

# These are the exact shortnames from test_data_tc002.csv (TC-002 rows 001..027)
TEST_SHORTNAMES = [
    "sn001_ssssssss", "sn002_ssssssss", "sn003_ssssssss", "sn004_ssssssss",
    "sn005_ssssssss", "sn006_ssssssss", "sn007_ssssssss", "sn008_ssssssss",
    "sn009_ssssssss", "sn010_ssssssss", "sn011_ssssssss", "sn012_ssssssss",
    "sn013_ssssssss", "sn014_ssssssss", "sn015_ssssssss", "sn016_ssssssss",
    "sn017_ssssssss", "sn018_ssssssss", "sn019_ssssssss", "sn020_ssssssss",
    "sn021_ssssssss", "sn022_ssssssss", "sn023_ssssssss", "sn024_ssssssss",
    "sn025_ssssssss", "sn026_ssssssss", "sn027_ssssssss",
]

opts = webdriver.ChromeOptions()
opts.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
wait = WebDriverWait(driver, 20)

try:
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

    print("\n========== Probing course shortnames via /course/view.php?name=... ==========")
    found = []
    for sn in TEST_SHORTNAMES:
        driver.get(BASE_URL + f"/course/view.php?name={sn}")
        time.sleep(1.5)
        current = driver.current_url
        # If course exists, URL becomes /course/view.php?id=<cid>
        m = re.search(r'/course/view\.php\?id=(\d+)', current)
        if m:
            cid = int(m.group(1))
            found.append((sn, cid))
            print(f"  [FOUND] {sn}  -> course id={cid}")
        else:
            # Could be error page
            if "Course not found" in driver.page_source or "errorcode" in current:
                pass  # not found - skip silently
            else:
                print(f"  [????] {sn}  -> redirected to {current[:80]}")

    print(f"\n========== TOTAL FOUND: {len(found)} courses ==========")
    for sn, cid in found:
        print(f"  {sn} = id {cid}")

finally:
    driver.quit()
