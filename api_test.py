import requests
import os
import sys
import time

# Print with flush to ensure output is visible
def print_flush(msg):
    print(msg, flush=True)

# Base URL for the local Flask server
BASE_URL = "http://localhost:5000"

print_flush("========================================")
print_flush("API Endpoint Testing")
print_flush("========================================")

# Test the root endpoint
print_flush("\nTesting root endpoint (/)...")
try:
    response = requests.get(f"{BASE_URL}/")
    print_flush(f"Root endpoint status: {response.status_code}")
    if response.status_code == 200:
        print_flush(f"Root response snippet: {response.text[:100]}...")
    else:
        print_flush(f"Root response error: {response.text[:100]}...")
except Exception as e:
    print_flush(f"Root endpoint error: {str(e)}")

# Test the diagnostic endpoint
print_flush("\nTesting diagnostic endpoint (/diagnostic/auth-status)...")
try:
    response = requests.get(f"{BASE_URL}/diagnostic/auth-status")
    print_flush(f"Diagnostic endpoint status: {response.status_code}")
    if response.status_code == 200:
        print_flush(f"Diagnostic response snippet: {response.text[:100]}...")
    else:
        print_flush(f"Diagnostic response error: {response.text[:100]}...")
except Exception as e:
    print_flush(f"Diagnostic endpoint error: {str(e)}")

# Test the test access control endpoint
print_flush("\nTesting access control endpoint (/test/access-control)...")
try:
    response = requests.get(f"{BASE_URL}/test/access-control")
    print_flush(f"Access control endpoint status: {response.status_code}")
    if response.status_code == 200:
        print_flush(f"Access control response snippet: {response.text[:100]}...")
    else:
        print_flush(f"Access control response error: {response.text[:100]}...")
except Exception as e:
    print_flush(f"Access control endpoint error: {str(e)}")

# Test the profile endpoint
print_flush("\nTesting profile endpoint (/profile/)...")
try:
    response = requests.get(f"{BASE_URL}/profile/")
    print_flush(f"Profile endpoint status: {response.status_code}")
    if response.status_code == 200:
        print_flush(f"Profile response snippet: {response.text[:100]}...")
    else:
        print_flush(f"Profile response error: {response.text[:100]}...")
except Exception as e:
    print_flush(f"Profile endpoint error: {str(e)}")

# Test the portfolio endpoint
print_flush("\nTesting portfolio endpoint (/portfolio/)...")
try:
    response = requests.get(f"{BASE_URL}/portfolio/")
    print_flush(f"Portfolio endpoint status: {response.status_code}")
    if response.status_code == 200:
        print_flush(f"Portfolio response snippet: {response.text[:100]}...")
    else:
        print_flush(f"Portfolio response error: {response.text[:100]}...")
except Exception as e:
    print_flush(f"Portfolio endpoint error: {str(e)}")

print_flush("\nTesting complete")
