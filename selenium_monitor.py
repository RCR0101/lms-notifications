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

# Helper functions for data handling
def sanitize_uid(uid):
    return re.sub(r'\W+', '_', uid)

def get_data_file(uid):
    return f"data_{sanitize_uid(uid)}.json"

def read_previous_data(data_file):
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

def write_current_data(data_file, data):
    with open(data_file, 'w') as f:
        json.dump(data, f)

def tokenize_text(text):
    """Tokenize the text by sentences for fine-grained comparison."""
    return [sentence.strip() for sentence in text.split('\n') if sentence.strip()]

def compare_announcement_body(old_body, new_body):
    """Compare tokenized sentences to detect fine-grained changes."""
    old_tokens = set(tokenize_text(old_body))
    new_tokens = set(tokenize_text(new_body))
    
    added = new_tokens - old_tokens
    removed = old_tokens - new_tokens

    changes = {}
    if added:
        changes["added"] = list(added)
    if removed:
        changes["removed"] = list(removed)

    return changes if changes else None

def compare_course_data(old_data, new_data):
    """Compare new data to old data for fine-grained changes detection."""
    changes = {}
    for url, new_course in new_data.items():
        if url not in old_data:
            changes[url] = "New course added."
        else:
            old_course = old_data[url]
            new_body = new_course.get('announcement_body', '')
            old_body = old_course.get('announcement_body', '')

            if new_body != old_body:
                body_changes = compare_announcement_body(old_body, new_body)
                if body_changes:
                    changes[url] = {"Announcements updated": body_changes}
    
    # Detect removed courses
    for url in old_data:
        if url not in new_data:
            changes[url] = "Course removed."

    return changes

# Main API function
@app.post("/monitor")
def monitor_courses(request: MonitorRequest):
    email = request.email
    password = request.password
    uid = sanitize_uid(email.split('@')[0])
    data_file = get_data_file(uid)

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebDriver Error: {e}")

    wait = WebDriverWait(driver, 20)
    courses_data = {}

    try:
        # Login process
        target_url = "https://lms.erp.bits-pilani.ac.in/moodle/login/index.php"
        driver.get(target_url)
        oauth_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.login-identityprovider-btn.btn-block")))
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

        # Extract and store data for each course
        for url in urls:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-content")))
            data = {}
            
            # Try to find announcement details
            try:
                announcement_element = driver.find_element(By.XPATH, "//div[contains(@class, 'activitytitle') and contains(@class, 'modtype_forum')]//div[contains(@class, 'activityname')]//a")
                data['announcement_link'] = announcement_element.get_attribute('href')
                driver.get(data['announcement_link'])
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                data['announcement_body'] = driver.find_element(By.TAG_NAME, "body").text
            except Exception:
                data['announcement_link'] = None
                data['announcement_body'] = "No announcement found."

            courses_data[url] = data

        # Compare with previous data
        old_courses_data = read_previous_data(data_file)
        changes = compare_course_data(old_courses_data, courses_data)

        # Write current data to file
        write_current_data(data_file, courses_data)

        # Return only detected changes, if any
        if changes:
            return {
                "message": "Changes detected.",
                "changes": changes
            }
        else:
            return {
                "message": "No changes detected."
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    finally:
        driver.quit()