#!/usr/bin/env python3
"""
Quick inline script to update Agent Engine environment variables.

Copy and paste this entire script to update your agent's environment variables.
"""

python3 << 'EOF'
from vertexai import agent_engines
import vertexai
import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

# Load .env file
load_dotenv()

# ============================================================================
# CONFIGURATION - Update these values
# ============================================================================
PROJECT_ID = os.getenv("PROJECT_ID", "logical-hallway-485016-r7")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ID = os.getenv("AGENT_ID", "180545306838958080")  # ⚠️ UPDATE THIS with your agent ID

AGENT_RESOURCE = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}"

# Initialize Vertex AI
print(f"🔧 Initializing Vertex AI...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Load environment variables from .env
dotenv_path = Path('.env')
env_vars = {}

if dotenv_path.exists():
    env_dict = dotenv_values(dotenv_path)
    
    # All variables to include
    keys_to_include = [
        # OpenAI (REQUIRED)
        "OPENAI_API_KEY",
        
        # LangSmith (RECOMMENDED)
        "LANGSMITH_API_KEY",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
        
        # Resend Email (REQUIRED for emails)
        "RESEND_API_KEY",
        "RESEND_FROM_EMAIL",
        
        # Email Recipients (REQUIRED)
        "SALES_AGENT_EMAIL",
        "PRODUCT_EXPERT_EMAIL",
        "SERVICES_AGENT_EMAIL",
        "NOTIFICATION_EMAIL",
        "IT_SUPPORT_URL",
        
        # Salesforce (Optional)
        "SALESFORCE_MODE",
        "SALESFORCE_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET",
        "SALESFORCE_USERNAME",
        "SALESFORCE_PASSWORD",
        "SALESFORCE_SECURITY_TOKEN",
        "SALESFORCE_LOGIN_URL",
        "SALESFORCE_API_VERSION",
        
        # SAP (Optional)
        "SAP_MODE",
        "SAP_BASE_URL",
        "SAP_API_KEY",
        "SAP_USERNAME",
        "SAP_PASSWORD",
        "SAP_CLIENT",
        
        # Routing (Optional)
        "ROUTING_AE_OWNER_ID",
        "ROUTING_SDR_OWNER_ID",
        "ROUTING_NURTURE_OWNER_ID",
        "ROUTING_ESCALATION_OWNER_ID",
    ]
    
    for key in keys_to_include:
        value = env_dict.get(key) or os.getenv(key)
        if value:
            env_vars[key] = value
    
    print(f"✅ Loaded {len(env_vars)} variables from .env")
else:
    print("⚠️  .env not found. Using system environment variables.")
    for key in ["OPENAI_API_KEY", "RESEND_API_KEY"]:
        if os.getenv(key):
            env_vars[key] = os.getenv(key)

if not env_vars:
    print("❌ No environment variables found!")
    exit(1)

# Get agent
print(f"\n📋 Getting agent: {AGENT_RESOURCE}")
agent = agent_engines.get(AGENT_RESOURCE)
print(f"✅ Found: {agent.display_name}")

# Update
print(f"\n🔄 Updating {len(env_vars)} environment variables...")
updated_agent = agent_engines.update(
    resource_name=AGENT_RESOURCE,
    env_vars=env_vars
)

print("\n" + "=" * 60)
print("✅ SUCCESS! Environment variables updated!")
print("=" * 60)
print(f"Agent: {updated_agent.display_name}")
print(f"Variables updated: {len(env_vars)}")
print("\n📋 Updated variables:")
for key in sorted(env_vars.keys()):
    value = env_vars[key]
    if any(x in key for x in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
        print(f"   {key} = {value[:8]}...{value[-4:]}")
    else:
        print(f"   {key} = {value}")
print("=" * 60)
print("\n💡 Changes will take effect after agent restart (usually 1-2 minutes)")
EOF
