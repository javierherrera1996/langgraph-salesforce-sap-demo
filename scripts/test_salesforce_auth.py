#!/usr/bin/env python3
"""
Test Salesforce authentication (both password and client_credentials flows).
"""

import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.tools import salesforce
from src.config import get_salesforce_config

def test_authentication():
    """Test Salesforce authentication."""
    print("=" * 60)
    print("🔐 TESTING SALESFORCE AUTHENTICATION")
    print("=" * 60)

    config = get_salesforce_config()

    print(f"\n📋 Configuration:")
    print(f"   Mode: {config.mode}")
    print(f"   Auth Type: {config.auth_type}")
    print(f"   Instance URL: {config.instance_url}")
    print(f"   API Version: {config.api_version}")
    print(f"   Client ID: {config.client_id[:20]}..." if config.client_id else "   Client ID: NOT SET")

    if config.is_mock:
        print("\n⚠️  Running in MOCK mode")
        print("   Change SALESFORCE_MODE=real in .env to test real connection")
        return

    print(f"\n🔄 Attempting authentication...")
    print(f"   Flow: {config.auth_type}")

    try:
        access_token, instance_url = salesforce.authenticate()

        print(f"\n✅ Authentication successful!")
        print(f"   Access Token: {access_token[:30]}...")
        print(f"   Instance URL: {instance_url}")

        # Test a simple API call
        print(f"\n🧪 Testing API call (get new leads)...")
        leads = salesforce.get_new_leads(limit=1)

        if leads:
            print(f"✅ API call successful!")
            print(f"   Found {len(leads)} lead(s)")
            if leads:
                lead = leads[0]
                print(f"   Lead: {lead.get('Name', 'N/A')} - {lead.get('Company', 'N/A')}")
        else:
            print("⚠️  No leads found (this is OK if your Salesforce org has no New leads)")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_authentication()
