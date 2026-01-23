#!/usr/bin/env python3
"""
Debug script to test Resend API and verify POST method is used.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / ".env")

API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
TO_EMAIL = os.getenv("NOTIFICATION_EMAIL", "andreshebe96@gmail.com")

print("🔍 Debug Resend API - Verify POST Method")
print("=" * 60)

if not API_KEY:
    print("❌ ERROR: RESEND_API_KEY not found")
    sys.exit(1)

api_url = "https://api.resend.com/emails"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "from": FROM_EMAIL,
    "to": [TO_EMAIL],
    "subject": "🔍 Debug Test - POST Method Verification",
    "html": "<p>This is a test to verify POST method is used.</p>"
}

print(f"URL: {api_url}")
print(f"Method: POST (explicit)")
print(f"Headers: {headers}")
print(f"Payload: {payload}")
print()

# Create a session to track the request
session = requests.Session()

# Add a hook to log the actual request
def log_request(response, *args, **kwargs):
    print("📊 REQUEST DETAILS:")
    print(f"   Actual Method: {response.request.method}")
    print(f"   Actual URL: {response.request.url}")
    print(f"   Headers Sent: {dict(response.request.headers)}")
    print(f"   Body: {response.request.body[:200] if response.request.body else 'None'}")
    return response

# Register the hook
session.hooks['response'] = [log_request]

print("📧 Sending request...")
print()

try:
    response = session.post(
        api_url,
        json=payload,
        headers=headers,
        timeout=30,
        allow_redirects=False
    )
    
    print()
    print("📊 RESPONSE DETAILS:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"   Message ID: {result.get('id', 'N/A')}")
    else:
        print("❌ ERROR:")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw Response: {response.text}")
            
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()
