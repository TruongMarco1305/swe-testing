"""Final probe: visit category page with AJAX wait + dump course tree."""
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

    # Try the category-create form which lists all categories (good way to enumerate)
    print("\n========== /course/edit.php (course create form - has category dropdown) ==========")
    driver.get(BASE_URL + "/course/edit.php?category=1")
    time.sleep(4)
    # Get category dropdown options
    cats = driver.execute_script("""
        var select = document.getElementById('id_category');
        if (!select) {
            // Maybe it's an autocomplete - look for hidden categories list
            var opts = document.querySelectorAll('[data-fieldtype="autocomplete"] option');
            var result = [];
            opts.forEach(o => result.push({id: o.value, name: o.text}));
            return result;
        }
        return Array.from(select.options).map(o => ({id: o.value, name: o.text}));
    """)
    print(f"  Categories in dropdown: {len(cats) if cats else 0}")
    if cats:
        for c in cats[:30]:
            print(f"    {c.get('id'):>6}  {c.get('name')}")

    # Try recycle bin
    print("\n========== /admin/tool/recyclebin/ category list ==========")
    driver.get(BASE_URL + "/admin/tool/recyclebin/index.php")
    time.sleep(3)
    html = driver.page_source
    print(f"  URL: {driver.current_url}")
    print(f"  Title: {driver.title}")
    print(f"  Page snippet: {html[1000:1500] if len(html) > 1500 else html[:500]}")

    # Try direct category recycle bin
    print("\n========== Category recycle bin per cat 1 / 23 ==========")
    for cat in [1, 23]:
        driver.get(BASE_URL + f"/admin/tool/recyclebin/index.php?categoryid={cat}")
        time.sleep(2)
        html = driver.page_source
        course_refs = sorted(set(int(x) for x in re.findall(r'/course/view\.php\?id=(\d+)', html)))
        sn_hits = sorted(set(re.findall(r'sn\d+_\w+', html)))
        print(f"  categoryid={cat}: {len(course_refs)} course refs, {len(sn_hits)} sn shortname mentions")
        if sn_hits[:3]:
            print(f"    sn examples: {sn_hits[:3]}")

finally:
    driver.quit()
