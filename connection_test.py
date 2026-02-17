import requests
import sys

# Base URL for the local Flask server
BASE_URL = "http://localhost:5000"

print("Starting connection tests...")

# Test the root endpoint
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"Root endpoint status: {response.status_code}")
    if response.status_code == 200:
        print(f"Root response first 100 chars: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to server: {str(e)}")

# Test the diagnostic endpoint
try:
    print("\nTesting diagnostic endpoint...")
    response = requests.get(f"{BASE_URL}/diagnostic/auth-status")
    print(f"Diagnostic endpoint status: {response.status_code}")
    if response.status_code == 200:
        print(f"Diagnostic response first 100 chars: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to diagnostic endpoint: {str(e)}")

# Test the profile endpoint
try:
    print("\nTesting profile endpoint...")
    response = requests.get(f"{BASE_URL}/profile/")
    print(f"Profile endpoint status: {response.status_code}")
    if response.status_code == 200:
        print(f"Profile response first 100 chars: {response.text[:100]}...")
    else:
        print(f"Profile response code: {response.status_code}")
        print(f"Profile response text: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to profile endpoint: {str(e)}")

# Test the portfolio endpoint
try:
    print("\nTesting portfolio endpoint...")
    response = requests.get(f"{BASE_URL}/portfolio/")
    print(f"Portfolio endpoint status: {response.status_code}")
    if response.status_code == 200:
        print(f"Portfolio response first 100 chars: {response.text[:100]}...")
    else:
        print(f"Portfolio response code: {response.status_code}")
        print(f"Portfolio response text: {response.text[:100]}...")
except Exception as e:
    print(f"Error connecting to portfolio endpoint: {str(e)}")

print("\nConnection tests complete.")
