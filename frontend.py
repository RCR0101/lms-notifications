import streamlit as st
import requests
from datetime import datetime, timedelta

# Function to perform the API call
def call_api(email, password):
    url = "http://127.0.0.1:8000/monitor"  # Adjust the URL if your API is hosted elsewhere
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Title and input fields for email and password
st.title("Course Monitor")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

# Function to display the response in a formatted, clean style
def display_response(data):
    if "error" in data:
        st.error(data["error"])
    else:
        st.subheader("API Response")
        for key, value in data.items():
            st.markdown(f"**{key.capitalize()}:** {value}")

# Button to start monitoring
if st.button("Start Monitoring"):
    if email and password:
        # Call the API and display the response
        with st.spinner('Calling API...'):
            api_response = call_api(email, password)
            display_response(api_response)
    else:
        st.error("Please enter both email and password.")