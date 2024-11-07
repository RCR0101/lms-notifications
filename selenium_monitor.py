from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import time
import os

# Load environment variables from the .env file
load_dotenv()

# Access the variables
email = os.getenv("EMAIL_ID")
password = os.getenv("PASSWORD")

# Initialize the WebDriver
driver = webdriver.Chrome()

# Step 1: Navigate to the page with the OAuth button
target_url = "https://lms.erp.bits-pilani.ac.in/moodle/login/index.php"
driver.get(target_url)
time.sleep(2)  # Let the page load

# Step 2: Find and click the Google OAuth button
oauth_button = driver.find_element(By.CSS_SELECTOR, ".btn.login-identityprovider-btn.btn-block")
oauth_button.click()
time.sleep(2)  # Wait for Google login page to load

# Step 3: Log in through Google OAuth
email_input = driver.find_element(By.ID, "identifierId")
email_input.send_keys(email)
email_input.send_keys(Keys.RETURN)
time.sleep(7)

# Enter password
password_input = driver.find_element(By.NAME, "Passwd")
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)
time.sleep(5)

driver.get("https://lms.erp.bits-pilani.ac.in/moodle/")
time.sleep(5)
course_links = driver.find_elements(By.CSS_SELECTOR, "div.coursebox .coursename a")
urls = [link.get_attribute('href') for link in course_links]

# Dictionary to hold initial page contents for each tab
tabs_content = {}
for url in urls:
    driver.execute_script("window.open('{}');".format(url))
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)  # Wait for the page to load
    tabs_content[url] = driver.page_source  # Store initial content

# Function to notify when a change is detected
def notify_change(url):
    print(f"Change detected on {url}")
    # Add your notification logic here, like sending an email

# Step 5: Periodically refresh each tab and check for changes
try:
    while True:
        for idx, url in enumerate(urls):
            # Switch to the tab corresponding to the current URL
            driver.switch_to.window(driver.window_handles[idx + 1])  # +1 because the first tab is the main page
            driver.refresh()
            time.sleep(2)  # Wait for the page to load

            # Compare content to detect changes
            current_content = driver.page_source
            if current_content != tabs_content[url]:
                notify_change(url)
                tabs_content[url] = current_content  # Update with new content

        time.sleep(60)  # Refresh every minute
except KeyboardInterrupt:
    print("Stopped monitoring.")
finally:
    driver.quit()