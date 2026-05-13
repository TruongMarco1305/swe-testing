"""Discover the first sectionid in courses 425 and 426."""
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
    driver.get(BASE_URL + "/login/index.php")
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    driver.execute_script("""
        var el = document.querySelector('.onetrust-pc-dark-filter');
        if (el) el.style.display = 'none';
    """)
    time.sleep(1)
    driver.execute_script("""
        document.getElementById('username').value = arguments[0];
        document.getElementById('password').value = arguments[1];
        document.getElementById('loginbtn').click();
    """, USERNAME, PASSWORD)
    wait.until(EC.url_contains("/my/"))
    print("[OK] Logged in")

    for cid in (425, 426):
        print(f"\n========== Course {cid} ==========")
        driver.get(BASE_URL + f"/course/view.php?id={cid}")
        time.sleep(4)
        html = driver.page_source
        print(f"  Title: {driver.title}")
        # Find section IDs from li.section[data-id]
        section_ids = sorted(set(int(x) for x in re.findall(r'data-sectionid="(\d+)"|class="section[^"]*" data-id="(\d+)"', html) for x in x if x))
        # Better: just find any sectionid= or sectionreturn= in href links
        section_link_ids = sorted(set(int(x) for x in re.findall(r'sectionid=(\d+)|sectionreturn=(\d+)', html) for x in x if x))
        # Also find data-id on section elements specifically
        bs_section_ids = sorted(set(int(x) for x in re.findall(r'<li[^>]+class="[^"]*section[^"]*"[^>]+data-id="(\d+)"', html)))
        print(f"  data-sectionid attrs:    {section_ids}")
        print(f"  sectionid= URL params:   {section_link_ids[:20]}")
        print(f"  <li.section data-id=*>:  {bs_section_ids[:20]}")
        # Try the modedit URL with discovered sectionid
        if section_link_ids:
            test_sid = section_link_ids[0]
            print(f"\n  --> Try sectionid={test_sid}")
            test_url = BASE_URL + f"/course/modedit.php?add=assign&type&course={cid}&sectionid={test_sid}&return=0&beforemod=0"
            driver.get(test_url)
            time.sleep(4)
            print(f"     Current URL: {driver.current_url}")
            has_id_name = "id=\"id_name\"" in driver.page_source
            print(f"     Has #id_name input: {has_id_name}")

finally:
    driver.quit()
