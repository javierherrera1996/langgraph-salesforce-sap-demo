#!/usr/bin/env python3
"""
Update environment variables for a deployed Vertex AI Agent Engine.

Usage:
    python scripts/update_agent_env_vars.py
    
Or run inline:
    python3 << 'EOF'
    # ... paste script here ...
    EOF
"""

from vertexai import agent_engines
import vertexai
import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

# Load environment variables from .env
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "logical-hallway-485016-r7")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ID = os.getenv("AGENT_ID", "180545306838958080")  # Update with your agent ID

AGENT_RESOURCE = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}"

# Initialize Vertex AI
print(f"Initializing Vertex AI for project: {PROJECT_ID}, location: {LOCATION}")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Load environment variables from .env file
dotenv_path = Path('.env')
env_vars = {}

if dotenv_path.exists():
    env_dict = dotenv_values(dotenv_path)
    
    # List of all variables to include
    required_keys = [
        # OpenAI / LLM (REQUIRED)
        "OPENAI_API_KEY",
        
        # LangSmith (RECOMMENDED)
        "LANGSMITH_API_KEY",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
        
        # Resend Email (REQUIRED for email notifications)
        "RESEND_API_KEY",
        "RESEND_FROM_EMAIL",
        
        # Email Recipients (REQUIRED)
        "SALES_AGENT_EMAIL",
        "PRODUCT_EXPERT_EMAIL",
        "SERVICES_AGENT_EMAIL",
        "NOTIFICATION_EMAIL",
        "IT_SUPPORT_URL",
        
        # Salesforce (Optional - for real integration)
        "SALESFORCE_MODE",
        "SALESFORCE_INSTANCE_URL",
        "SALESFORCE_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET",
        "SALESFORCE_USERNAME",
        "SALESFORCE_PASSWORD",
        "SALESFORCE_SECURITY_TOKEN",
        "SALESFORCE_LOGIN_URL",
        "SALESFORCE_API_VERSION",
        
        # SAP (Optional - for real integration)
        "SAP_MODE",
        "SAP_BASE_URL",
        "SAP_API_KEY",
        "SAP_USERNAME",
        "SAP_PASSWORD",
        "SAP_CLIENT",
        
        # Routing Configuration (Optional)
        "ROUTING_AE_OWNER_ID",
        "ROUTING_SDR_OWNER_ID",
        "ROUTING_NURTURE_OWNER_ID",
        "ROUTING_ESCALATION_OWNER_ID",
        
        # Product Owner Emails (Optional)
        "PRODUCT_OWNER_SWITCHES",
        "PRODUCT_OWNER_CABLES",
        "PRODUCT_OWNER_CONNECTORS",
        "PRODUCT_OWNER_SOFTWARE",
        "PRODUCT_OWNER_INFRASTRUCTURE",
        "PRODUCT_OWNER_GENERAL",
    ]
    
    # Filter only variables that exist and have values
    for key in required_keys:
        value = env_dict.get(key) or os.getenv(key)
        if value:
            env_vars[key] = value
    
    print(f"✅ Loaded {len(env_vars)} environment variables from .env")
    print(f"   Variables: {', '.join(sorted(env_vars.keys()))}")
else:
    print("⚠️  .env file not found. Using system environment variables.")
    # Fallback to critical variables
    critical_keys = ["OPENAI_API_KEY", "RESEND_API_KEY"]
    for key in critical_keys:
        value = os.getenv(key)
        if value:
            env_vars[key] = value

if not env_vars:
    print("❌ No environment variables found!")
    print("   Please create a .env file or set environment variables.")
    exit(1)

# Get the agent
print(f"\n📋 Getting agent: {AGENT_RESOURCE}")
try:
    agent = agent_engines.get(AGENT_RESOURCE)
    print(f"✅ Found agent: {agent.display_name}")
except Exception as e:
    print(f"❌ Error getting agent: {e}")
    print(f"   Make sure the agent ID is correct: {AGENT_ID}")
    exit(1)

# Update environment variables
print(f"\n🔄 Updating environment variables...")
try:
    updated_agent = agent_engines.update(
        resource_name=AGENT_RESOURCE,
        env_vars=env_vars
    )
    
    print("=" * 60)
    print("✅ SUCCESS! Environment variables updated!")
    print("=" * 60)
    print(f"Agent: {updated_agent.display_name}")
    print(f"Resource: {updated_agent.name}")
    print(f"\n📋 Updated Variables ({len(env_vars)}):")
    for key in sorted(env_vars.keys()):
        # Mask sensitive values
        value = env_vars[key]
        if "KEY" in key or "SECRET" in key or "PASSWORD" in key or "TOKEN" in key:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"   {key} = {masked}")
        else:
            print(f"   {key} = {value}")
    print("=" * 60)
    print("\n💡 Note: It may take a few minutes for changes to take effect.")
    print("   The agent will restart with the new environment variables.")
    
except Exception as e:
    print(f"❌ Error updating agent: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
