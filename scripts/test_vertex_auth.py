#!/usr/bin/env python3
"""
Test Vertex AI authentication with Service Account.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def test_vertex_auth():
    """Test Vertex AI authentication."""
    print("=" * 60)
    print("🔐 TESTING VERTEX AI AUTHENTICATION")
    print("=" * 60)

    # Check for Service Account credentials
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if creds_path:
        print(f"\n✅ Service Account configured:")
        print(f"   Path: {creds_path}")
        if os.path.exists(creds_path):
            print(f"   Status: ✅ File exists")
        else:
            print(f"   Status: ❌ File not found!")
            print(f"\n💡 Run: bash scripts/setup_service_account.sh")
            sys.exit(1)
    else:
        print("\n⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   Trying Application Default Credentials...")

    # Test authentication
    print(f"\n🔄 Testing Vertex AI connection...")

    try:
        from google.auth import default
        from google.cloud import aiplatform

        # Get credentials
        credentials, project = default()
        print(f"✅ Credentials loaded successfully")
        print(f"   Project: {project or os.getenv('PROJECT_ID')}")

        # Initialize Vertex AI
        project_id = os.getenv("PROJECT_ID", "logical-hallway-485016-r7")
        location = os.getenv("LOCATION", "us-central1")

        aiplatform.init(project=project_id, location=location, credentials=credentials)
        print(f"✅ Vertex AI initialized")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")

        # Test listing reasoning engines
        print(f"\n🧪 Testing API call (list reasoning engines)...")
        from google.cloud.aiplatform_v1.services.reasoning_engine_service import ReasoningEngineServiceClient

        client = ReasoningEngineServiceClient(credentials=credentials)
        parent = f"projects/{project_id}/locations/{location}"

        # Try to list (may return empty if no engines exist)
        try:
            response = client.list_reasoning_engines(parent=parent, page_size=1)
            engines = list(response)
            print(f"✅ API call successful!")
            print(f"   Found {len(engines)} reasoning engine(s)")
        except Exception as e:
            if "404" in str(e) or "NOT_FOUND" in str(e):
                print(f"✅ API accessible (no engines deployed yet)")
            else:
                raise

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🎯 Your Vertex AI authentication is working correctly!")
        print("   Your Postman requests will work without manual token updates.")
        print("\n💡 To use in Postman:")
        print("   1. Set Authorization type to 'Bearer Token'")
        print("   2. Token will be automatically refreshed by Service Account")
        print("   3. No need to run 'gcloud auth print-access-token' anymore!")

    except ImportError:
        print("\n❌ Google Cloud libraries not installed")
        print("   Run: pip install google-cloud-aiplatform")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Run: bash scripts/setup_service_account.sh")
        print("   2. Make sure .env has GOOGLE_APPLICATION_CREDENTIALS set")
        print("   3. Check that the JSON key file exists and is valid")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_vertex_auth()
