from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
wait = WebDriverWait(driver, 20)

# Step 1: Navigate to the page with the OAuth button
target_url = "https://lms.erp.bits-pilani.ac.in/moodle/login/index.php"
driver.get(target_url)

# Step 2: Find and click the Google OAuth button
oauth_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.login-identityprovider-btn.btn-block")))
oauth_button.click()

# Step 3: Log in through Google OAuth
email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
email_input.send_keys(email)
email_input.send_keys(Keys.RETURN)
time.sleep(3) 
# Wait for password input to appear
password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)

time.sleep(5)  # Wait for the login to complete
# Navigate to the main courses page
driver.get("https://lms.erp.bits-pilani.ac.in/moodle/")
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.coursebox")))

# Extract course URLs dynamically
course_links = driver.find_elements(By.CSS_SELECTOR, "div.coursebox .coursename a")
urls = [link.get_attribute('href') for link in course_links]

# Dictionary to hold initial data for each course
courses_data = {}

# Function to extract specific data from a course page
def extract_course_data():
    data = {}
    # Extract the announcements link
    try:
        announcement_element = driver.find_element(
            By.XPATH, "//div[contains(@class, 'activitytitle') and contains(@class, 'modtype_forum')]//div[contains(@class, 'activityname')]//a"
        )
        announcement_link = announcement_element.get_attribute('href')
        data['announcement_link'] = announcement_link
    except:
        data['announcement_link'] = None

    return data

# Open each course URL in a new tab and store the initial content
for url in urls:
    driver.execute_script(f"window.open('{url}');")
    driver.switch_to.window(driver.window_handles[-1])

    # Wait for the course page to load
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-content")))

    # Extract specific data from the course page
    data = extract_course_data()
    
    if data['announcement_link']:
        # Open the announcements page in a new tab
        driver.execute_script(f"window.open('{data['announcement_link']}');")
        driver.switch_to.window(driver.window_handles[-1])
        
        # Wait for the announcements page to load and get its body content
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        announcement_body = driver.find_element(By.TAG_NAME, "body").text
        data['announcement_body'] = announcement_body
        
        # Close announcements tab and return to course tab
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        
    courses_data[url] = data  # Store initial data

# Function to notify when a change is detected
def notify_change(url, changes):
    course_name = driver.title
    print(f"Change detected in course: {course_name}")
    print("Changes:")
    for change in changes:
        print(f"- {change}")
    print("-" * 40)
    # Add your notification logic here, like sending an email

# Step 5: Periodically refresh each tab and check for changes
try:
    while True:
        for idx, url in enumerate(urls):
            # Switch to the tab corresponding to the current URL
            driver.switch_to.window(driver.window_handles[idx + 1])  # +1 because the first tab is the main page
            driver.refresh()

            # Wait for the course page to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-content")))

            # Extract specific data after refresh
            new_data = extract_course_data()
            old_data = courses_data[url]
            changes = []

            # Check if the announcement link exists
            if new_data['announcement_link']:
                # Open the announcements page in a new tab
                driver.execute_script(f"window.open('{new_data['announcement_link']}');")
                driver.switch_to.window(driver.window_handles[-1])

                # Wait for the announcements page to load and get its body content
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                new_announcement_body = driver.find_element(By.TAG_NAME, "body").text
                
                # Check for changes in announcement content
                if old_data.get('announcement_body') != new_announcement_body:
                    changes.append("Announcements content has changed.")

                # Close announcements tab and return to course tab
                driver.close()
                driver.switch_to.window(driver.window_handles[idx + 1])

                # Update announcement body in stored data
                old_data['announcement_body'] = new_announcement_body

            # Notify if there are changes
            if changes:
                notify_change(url, changes)

        time.sleep(600)  # Refresh every 10 minutes
except KeyboardInterrupt:
    print("Stopped monitoring.")
finally:
    driver.quit()