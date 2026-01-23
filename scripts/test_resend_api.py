#!/usr/bin/env python3
"""
Test Resend API directly using REST API.
This helps diagnose API key issues.
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

print("🧪 Test Resend API (Direct REST)")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...{API_KEY[-4:] if len(API_KEY) > 24 else 'N/A'}")
print(f"From: {FROM_EMAIL}")
print(f"To: {TO_EMAIL}")
print("=" * 60)

if not API_KEY:
    print("❌ ERROR: RESEND_API_KEY not found in environment")
    print("   Set it in .env file or export it:")
    print("   export RESEND_API_KEY=re_xxxxxxxxxxxxxxxx")
    sys.exit(1)

# Use Resend REST API
api_url = "https://api.resend.com/emails"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "from": FROM_EMAIL,
    "to": [TO_EMAIL],
    "subject": "✅ Test Resend API - Belden AI Agent",
    "html": """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #1E3A5F, #3B82F6); color: white; padding: 20px; border-radius: 10px 10px 0 0; }
            .content { background: #F8FAFC; padding: 20px; border-radius: 0 0 10px 10px; }
            .success { background: #D1FAE5; padding: 15px; border-radius: 8px; border: 1px solid #10B981; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0;">✅ Resend API Working!</h1>
                <p style="margin:5px 0 0 0;">Belden AI Agent - Direct API Test</p>
            </div>
            <div class="content">
                <div class="success">
                    <h2 style="margin:0; color: #065F46;">🎉 Success!</h2>
                    <p style="margin:10px 0 0 0; color: #047857;">
                        If you're seeing this email, Resend API is working correctly.
                    </p>
                </div>
                <p>The system can now send emails automatically when:</p>
                <ul>
                    <li>📊 A lead has score >= 60%</li>
                    <li>📦 A product complaint is detected</li>
                    <li>🎫 A ticket is classified (always sends AI analysis)</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
}

print("\n📧 Sending email via REST API...")
print(f"   URL: {api_url}")
print(f"   Method: POST")
print()

try:
    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    
    print(f"📊 Response Status: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        message_id = result.get("id", "N/A")
        print("✅ SUCCESS! Email sent successfully!")
        print(f"   Message ID: {message_id}")
        print(f"   Full Response: {result}")
    else:
        print("❌ ERROR: Failed to send email")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        try:
            error_data = response.json()
            print(f"   Error Name: {error_data.get('name', 'N/A')}")
            print(f"   Error Message: {error_data.get('message', 'N/A')}")
            
            if error_data.get('name') == 'restricted_api_key':
                print()
                print("🔧 SOLUTION:")
                print("   1. Go to https://resend.com/api-keys")
                print("   2. Create a NEW API key with FULL permissions")
                print("   3. Replace RESEND_API_KEY in your .env file")
                print("   4. Make sure the API key starts with 're_'")
        except:
            pass
        
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("✅ Test completed successfully!")
