import requests

# Base URL for the local Flask server
BASE_URL = "http://localhost:5000"

# Test the root endpoint
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"Root endpoint status: {response.status_code}")
    print(f"Response: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to server: {str(e)}")

# Test the diagnostic endpoint
try:
    response = requests.get(f"{BASE_URL}/diagnostic/auth-status")
    print(f"Diagnostic endpoint status: {response.status_code}")
    print(f"Response: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to diagnostic endpoint: {str(e)}")

# Test the profile endpoint
try:
    response = requests.get(f"{BASE_URL}/profile/")
    print(f"Profile endpoint status: {response.status_code}")
    print(f"Response: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to profile endpoint: {str(e)}")
