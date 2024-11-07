from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import re

# Define the request model
class MonitorRequest(BaseModel):
    email: str
    password: str

# Initialize the FastAPI app
app = FastAPI()

# Function to sanitize uid
def sanitize_uid(uid):
    # Remove any non-alphanumeric characters
    sanitized = re.sub(r'\W+', '_', uid)
    return sanitized

def get_data_file(uid):
    sanitized_uid = sanitize_uid(uid)
    return f"data_{sanitized_uid}.json"

def read_previous_data(data_file):
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        return {}

def write_current_data(data_file, data):
    with open(data_file, 'w') as f:
        json.dump(data, f)

def compare_course_data(old_data, new_data):
    changes = {}
    for url in new_data:
        if url not in old_data:
            changes[url] = 'New course added.'
        else:
            old_course = old_data[url]
            new_course = new_data[url]
            if old_course.get('announcement_body') != new_course.get('announcement_body'):
                changes[url] = 'Announcements updated.'
    for url in old_data:
        if url not in new_data:
            changes[url] = 'Course removed.'
    return changes

@app.post("/monitor")
def monitor_courses(request: MonitorRequest):
    email = request.email
    password = request.password

    # Extract uid from email
    uid = email.split('@')[0]
    uid = sanitize_uid(uid)

    # Get the data file path for the user
    data_file = get_data_file(uid)

    # Set up headless Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize the WebDriver with headless options
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebDriver Error: {e}")

    wait = WebDriverWait(driver, 20)

    courses_data = {}

    try:
        # Step 1: Navigate to the login page
        target_url = "https://lms.erp.bits-pilani.ac.in/moodle/login/index.php"
        driver.get(target_url)

        # Step 2: Google OAuth login process
        oauth_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".btn.login-identityprovider-btn.btn-block")
        ))
        oauth_button.click()

        email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
        email_input.send_keys(email)
        email_input.send_keys(Keys.RETURN)
        time.sleep(3)

        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        time.sleep(5)
        driver.get("https://lms.erp.bits-pilani.ac.in/moodle/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.coursebox")))

        course_links = driver.find_elements(By.CSS_SELECTOR, "div.coursebox .coursename a")
        urls = [link.get_attribute('href') for link in course_links]

        def extract_course_data():
            data = {}
            try:
                announcement_element = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class, 'activitytitle') and contains(@class, 'modtype_forum')]"
                    "//div[contains(@class, 'activityname')]//a"
                )
                announcement_link = announcement_element.get_attribute('href')
                data['announcement_link'] = announcement_link
            except Exception:
                data['announcement_link'] = None

            return data

        for url in urls:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-content")))
            data = extract_course_data()

            if data['announcement_link']:
                driver.get(data['announcement_link'])
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                announcement_body = driver.find_element(By.TAG_NAME, "body").text
                data['announcement_body'] = announcement_body

            courses_data[url] = data

        # Read previous data
        old_courses_data = read_previous_data(data_file)

        # Compare data
        changes = compare_course_data(old_courses_data, courses_data)

        # Write current data to file
        write_current_data(data_file, courses_data)

        if changes:
            return {"message": "Changes detected.", "changes": changes}
        else:
            return {"message": "No changes detected."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    finally:
        driver.quit()