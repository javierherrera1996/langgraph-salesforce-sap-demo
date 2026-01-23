#!/usr/bin/env python3
"""
Test email configuration loading from the application.
This uses the same config loading mechanism as the app.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables FIRST (same as main.py)
from dotenv import load_dotenv
load_dotenv(override=True)

print("🧪 Test Email Configuration Loading")
print("=" * 60)

# Test 1: Direct environment variable
print("\n1️⃣ Direct Environment Variable:")
resend_key = os.getenv("RESEND_API_KEY", "")
print(f"   RESEND_API_KEY from env: {resend_key[:20] if resend_key else 'NOT SET'}...")
print(f"   Length: {len(resend_key) if resend_key else 0}")

# Test 2: Using config module
print("\n2️⃣ Using Config Module:")
try:
    from src.config import get_resend_config
    config = get_resend_config()
    
    print(f"   API Key from config: {config.api_key[:20] if config.api_key else 'NOT SET'}...")
    print(f"   API Key length: {len(config.api_key) if config.api_key else 0}")
    print(f"   is_configured: {config.is_configured}")
    print(f"   From email: {config.from_email}")
    print(f"   Product Expert email: {config.product_expert_email}")
    print(f"   Services Agent email: {config.services_agent_email}")
    
    # Test 3: Try to send email
    print("\n3️⃣ Test Sending Email:")
    if config.is_configured:
        from src.tools.email import send_email
        
        test_result = send_email(
            to=config.product_expert_email or "andreshebe96@gmail.com",
            subject="🧪 Test Email Configuration",
            html_content="<p>This is a test email to verify configuration loading.</p>"
        )
        
        print(f"   Result: {test_result}")
        print(f"   Success: {test_result.get('success', False)}")
        print(f"   Message ID: {test_result.get('message_id', 'N/A')}")
        print(f"   Error: {test_result.get('error', 'N/A')}")
    else:
        print("   ⚠️ Resend not configured - cannot send test email")
        print(f"   API Key value: {config.api_key}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ Test completed")
