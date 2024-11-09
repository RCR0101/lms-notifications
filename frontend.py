import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# Initialize session state variables
if 'monitoring_active' not in st.session_state:
    st.session_state['monitoring_active'] = False
if 'refresh_interval_ms' not in st.session_state:
    st.session_state['refresh_interval_ms'] = 0
if 'api_response' not in st.session_state:
    st.session_state['api_response'] = None
if 'email' not in st.session_state:
    st.session_state['email'] = ''
if 'password' not in st.session_state:
    st.session_state['password'] = ''

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

# Function to display the response in a formatted, clean style
def display_response(data):
    if "error" in data:
        st.error(data["error"])
    else:
        st.subheader("API Response")
        for key, value in data.items():
            st.markdown(f"**{key.capitalize()}:** {value}")

# Title and input fields for email and password
st.title("LMS Monitor")
email = st.text_input("Email", value=st.session_state['email'])
password = st.text_input("Password", type="password", value=st.session_state['password'])
refresh_timer = st.number_input("Auto-Refresh Timer (in seconds)", min_value=300, max_value=3600, value=600)

if not st.session_state['monitoring_active']:
    if st.button("Start Monitoring"):
        if email and password:
            # Store monitoring state in session state
            st.session_state['monitoring_active'] = True
            st.session_state['refresh_interval_ms'] = int(refresh_timer * 1000)
            st.session_state['email'] = email
            st.session_state['password'] = password
            # Call the API and store the response
            with st.spinner('Calling API...'):
                api_response = call_api(email, password)
                st.session_state['api_response'] = api_response
                display_response(api_response)
        else:
            st.error("Please enter both email and password.")

# Stop Monitoring button
if st.session_state['monitoring_active']:
    if st.button("Stop Monitoring"):
        st.session_state['monitoring_active'] = False
        st.session_state['refresh_interval_ms'] = 0
        st.success("Monitoring stopped.")

# If monitoring is active, set up auto-refresh
if st.session_state['monitoring_active']:
    # Set up auto-refresh
    st_autorefresh(interval=st.session_state['refresh_interval_ms'], key="api_auto_refresh")
    # Call the API and update the response
    with st.spinner('Refreshing API data...'):
        api_response = call_api(st.session_state['email'], st.session_state['password'])
        st.session_state['api_response'] = api_response
    # Display the response
    display_response(st.session_state['api_response'])
else:
    # If monitoring is not active but we have an API response, display it
    if st.session_state['api_response']:
        display_response(st.session_state['api_response'])