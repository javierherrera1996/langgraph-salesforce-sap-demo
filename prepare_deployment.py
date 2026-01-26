#!/usr/bin/env python3
"""
Preparation script for deploying to Vertex AI Agent Engine.

This script verifies and configures everything needed before deployment.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv, set_key, dotenv_values

def check_gcloud():
    """Checks if gcloud is installed."""
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ gcloud CLI is installed")
            print(f"   Version: {result.stdout.split()[0]}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("❌ gcloud CLI is not installed or not in PATH")
    print("\n📥 To install gcloud:")
    print("   1. macOS: brew install --cask google-cloud-sdk")
    print("   2. Or download from: https://cloud.google.com/sdk/docs/install")
    return False

def check_authentication():
    """Checks if authenticated with GCP."""
    # Check if service account credentials are configured
    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if service_account_path and os.path.exists(service_account_path):
        print(f"✅ Service Account credentials found: {service_account_path}")
        return True

    # Check Application Default Credentials with gcloud
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Authenticated with GCP (Application Default Credentials)")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try to verify with Python SDK directly
    try:
        from google.auth import default
        credentials, project = default()
        if credentials:
            print("✅ Credentials found (Python SDK)")
            return True
    except Exception:
        pass

    print("❌ Not authenticated with GCP")
    print("\n🔐 Authentication options:")
    print("   1. With gcloud CLI:")
    print("      gcloud auth application-default login")
    print("\n   2. With Service Account:")
    print("      export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json")
    print("      Or add GOOGLE_APPLICATION_CREDENTIALS to your .env file")
    return False

def get_current_project():
    """Gets the current gcloud project."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            project = result.stdout.strip()
            if project:
                return project
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None

def list_projects():
    """Lists available projects."""
    try:
        result = subprocess.run(
            ["gcloud", "projects", "list", "--format=value(projectId)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            projects = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            return projects
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []

def check_env_vars():
    """Checks required environment variables."""
    load_dotenv()

    required_vars = {
        "PROJECT_ID": "GCP project ID",
        "LOCATION": "GCP region (e.g.: us-central1)",
        "STAGING_BUCKET": "Staging bucket (e.g.: gs://your-project-agent-staging)",
        "OPENAI_API_KEY": "OpenAI API key"
    }

    missing = []
    configured = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.startswith("your-") or value.startswith("tu-") or value.startswith("TU_"):
            missing.append((var, description))
        else:
            configured.append(var)

    print("\n📋 Environment variables:")
    for var in configured:
        print(f"   ✅ {var}: Configured")

    for var, description in missing:
        print(f"   ❌ {var}: Missing - {description}")

    return len(missing) == 0, missing

def setup_env_file():
    """Configures the .env file with interactive values."""
    env_path = Path(".env")

    if not env_path.exists():
        print("\n⚠️  .env file doesn't exist. Creating from env.gcp.example...")
        example_path = Path("env.gcp.example")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print(f"✅ .env file created from {example_path}")
        else:
            print("❌ env.gcp.example not found")
            return False

    load_dotenv()
    env_vars = dotenv_values(".env")

    # Get current project if available
    current_project = get_current_project()
    if current_project and not env_vars.get("PROJECT_ID") or env_vars.get("PROJECT_ID", "").startswith("your-"):
        print(f"\n💡 Current gcloud project: {current_project}")
        response = input(f"Use '{current_project}' as PROJECT_ID? (y/n): ").strip().lower()
        if response == 'y':
            set_key(".env", "PROJECT_ID", current_project)
            print(f"✅ PROJECT_ID configured: {current_project}")

    # Configure LOCATION
    if not env_vars.get("LOCATION") or env_vars.get("LOCATION", "").startswith("your-"):
        location = input("Enter GCP region (default: us-central1): ").strip() or "us-central1"
        set_key(".env", "LOCATION", location)
        print(f"✅ LOCATION configured: {location}")

    # Configure STAGING_BUCKET
    project_id = os.getenv("PROJECT_ID") or current_project
    if project_id and (not env_vars.get("STAGING_BUCKET") or env_vars.get("STAGING_BUCKET", "").startswith("your-")):
        default_bucket = f"gs://{project_id}-agent-staging"
        bucket = input(f"Enter STAGING_BUCKET (default: {default_bucket}): ").strip() or default_bucket
        set_key(".env", "STAGING_BUCKET", bucket)
        print(f"✅ STAGING_BUCKET configured: {bucket}")

    return True

def check_apis():
    """Checks if required APIs are enabled."""
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("⚠️  PROJECT_ID not configured, cannot verify APIs")
        return False

    # Try to verify with gcloud CLI
    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", "--project", project_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            enabled_services = result.stdout.lower()
            if "aiplatform.googleapis.com" in enabled_services:
                print("✅ Vertex AI API is enabled")
                return True
            else:
                print("❌ Vertex AI API is not enabled")
                print(f"\n🔧 To enable it:")
                print(f"   gcloud services enable aiplatform.googleapis.com --project {project_id}")
                print(f"   Or from Console: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={project_id}")
                return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Could not verify APIs (gcloud not available)")
        print(f"\n💡 Verify manually at:")
        print(f"   https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={project_id}")
        print(f"   https://console.cloud.google.com/apis/library/storage-component.googleapis.com?project={project_id}")
        # Don't fail if gcloud is not available, just warn
        return True  # Allow to continue, assuming user will verify manually

    return False

def check_staging_bucket():
    """Checks if the staging bucket exists."""
    staging_bucket = os.getenv("STAGING_BUCKET")
    if not staging_bucket:
        print("⚠️  STAGING_BUCKET not configured")
        return False

    # Remove gs:// prefix if exists
    bucket_name = staging_bucket.replace("gs://", "")

    try:
        result = subprocess.run(
            ["gsutil", "ls", "-b", staging_bucket],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Staging bucket exists: {staging_bucket}")
            return True
        else:
            print(f"❌ Staging bucket doesn't exist: {staging_bucket}")
            project_id = os.getenv("PROJECT_ID")
            location = os.getenv("LOCATION", "us-central1")
            print(f"\n🔧 To create it:")
            print(f"   gsutil mb -l {location} {staging_bucket}")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Could not verify bucket (gsutil not available)")
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("🚀 PREPARATION FOR DEPLOYMENT TO VERTEX AI AGENT ENGINE")
    print("=" * 60)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    all_ready = True

    # 1. Check gcloud
    print("\n1️⃣ Checking gcloud CLI...")
    if not check_gcloud():
        all_ready = False
        print("\n⚠️  You need to install gcloud before continuing")
        return 1

    # 2. Check authentication
    print("\n2️⃣ Checking authentication...")
    if not check_authentication():
        all_ready = False
        print("\n⚠️  You need to authenticate before continuing")
        return 1

    # 3. Check environment variables
    print("\n3️⃣ Checking environment variables...")
    env_ready, missing = check_env_vars()

    if not env_ready:
        print("\n🔧 Configuring environment variables...")
        if not setup_env_file():
            all_ready = False
            return 1
        # Reload after configuring
        load_dotenv()
        env_ready, missing = check_env_vars()
        if not env_ready:
            print("\n❌ Still missing environment variables. Please configure the .env file manually.")
            all_ready = False

    # 4. Check APIs
    if env_ready:
        print("\n4️⃣ Checking GCP APIs...")
        if not check_apis():
            all_ready = False

    # 5. Check bucket
    if env_ready:
        print("\n5️⃣ Checking staging bucket...")
        if not check_staging_bucket():
            all_ready = False

    # Summary
    print("\n" + "=" * 60)
    if all_ready:
        print("✅ EVERYTHING READY TO DEPLOY!")
        print("=" * 60)
        print("\n🚀 To deploy, run:")
        print("   python deploy_agent.py")
        print("\nOr to deploy only a specific mode:")
        print("   python deploy_agent.py --mode lead    # Only Lead Qualification")
        print("   python deploy_agent.py --mode ticket # Only Ticket Triage")
        print("   python deploy_agent.py --mode combined # Both (default)")
        return 0
    else:
        print("❌ THERE ARE ISSUES TO RESOLVE BEFORE DEPLOYING")
        print("=" * 60)
        print("\nPlease resolve the issues indicated above and run again:")
        print("   python prepare_deployment.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
