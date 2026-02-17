import requests
import sys
import time
import signal

def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Base URL
BASE_URL = "http://localhost:5000"

# NOTE: Renamed test_endpoint -> helper_endpoint to avoid pytest collecting
# this diagnostic script's function as a real test (it lacks fixtures).
def helper_endpoint(endpoint, desc=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting {desc or endpoint}...")
    
    try:
        response = requests.get(url, timeout=5)
        status = response.status_code
        print(f"Status code: {status}")
        
        if status == 200:
            try:
                # Try to parse as JSON
                data = response.json()
                print("Response (JSON):")
                print(data)
            except:
                # If not JSON, print first 100 chars of text
                text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                print(f"Response (text): {text}")
        else:
            print(f"Error response: {response.text[:200]}")
        
        return status
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Main testing function
def main():
    print("========================================")
    print("     Flask Endpoint Testing Script      ")
    print("========================================")
    print(f"Testing server at {BASE_URL}")

    # Test main endpoints
    helper_endpoint("/", "Main page")
    helper_endpoint("/diagnostic/auth-status", "Diagnostic auth status")
    helper_endpoint("/test/access-control", "Test access control")
    helper_endpoint("/profile/", "Profile page")
    helper_endpoint("/portfolio/", "Portfolio page")

    print("\nTesting complete.")

if __name__ == "__main__":
    main()
