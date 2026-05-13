Here is how you can implement those exact non-functional requirements using Python:

1. Performance Testing in Python: Use Locust (Instead of JMeter)
While JMeter is Java-based, the Python industry standard for load testing is Locust. It allows you to define user behavior using pure Python code, making it incredibly easy to integrate with your existing project.

How it works: You write a simple Python class defining what a "user" does, and Locust spawns hundreds of them.

Installation: pip install locust

Implementation Example:

Python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5) # Users wait 1-5 seconds between actions

    @task
    def load_login_page(self):
        # Simulates a user loading the login page from Project #2
        self.client.get("/login") 
Running it: You run locust -f your_file.py in your terminal, and it opens a beautiful web UI where you can tell it to simulate 50 users and watch the graphs update in real-time.

2. Security Testing in Python: Use the OWASP ZAP Python API
OWASP ZAP is a standalone application, but it is built to be automated. It has an official Python API that allows your Python script to start a scan, wait for it to finish, and print the results.

How it works: You run the ZAP application in the background (as a daemon), and your Python script sends commands to it.

Installation: pip install python-owasp-zap-v2.4

Implementation Example:

Python
from zapv2 import ZAPv2
import time

target_url = 'http://your-project-url.com'
zap = ZAPv2(proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})

print('Spidering target...')
zap.spider.scan(target_url)
time.sleep(5) # Wait for spider to finish

print('Active Scanning target...')
zap.ascan.scan(target_url)

# After waiting for completion, fetch results:
print('Hosts: {}'.format(zap.core.hosts))
print('Alerts: {}'.format(zap.core.alerts()))
3. Accessibility Testing in Python: Use axe-selenium-python (Instead of Lighthouse)
Since you are already writing Selenium WebDriver scripts for your data-driven testing, the most elegant Python solution is to inject axe-core (the industry standard accessibility engine) directly into your Selenium tests.

How it works: While your Selenium script has a webpage open, it runs an accessibility audit on that specific page state and returns the violations.

Installation: pip install axe-selenium-python

Implementation Example:

Python
from selenium import webdriver
from axe_selenium_python import Axe

driver = webdriver.Chrome()
driver.get("http://your-project-url.com/login")

# Inject and run the accessibility tool
axe = Axe(driver)
axe.inject()
results = axe.run()

# Print out any accessibility violations (e.g., missing alt text, poor color contrast)
if len(results['violations']) == 0:
    print("Accessibility Check Passed!")
else:
    for violation in results['violations']:
        print(f"Violation: {violation['description']}")

driver.quit()
Summary Recommendation for Python
If you want to stick entirely to Python, I highly recommend choosing Locust (for Performance) and axe-selenium-python (for Accessibility). Both are native to Python, relatively easy to set up, and will look extremely impressive in your final Project #3 report!