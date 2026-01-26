"""
Deploy Belden Sales Agent to Vertex AI Agent Engine.

This script deploys the LangGraph-based Lead Qualification and Ticket Triage
workflows to Google Cloud's Vertex AI Agent Engine.

Usage:
    python deploy_agent.py

Before running:
1. Set up Google Cloud credentials: gcloud auth application-default login
2. Configure .env with:
   - PROJECT_ID: Your GCP project
   - LOCATION: GCP region (default: us-central1)
   - STAGING_BUCKET: GCS bucket for staging (gs://your-bucket)
   - Other required variables (OpenAI, Salesforce, SAP, LangSmith)

References:
- https://docs.cloud.google.com/agent-builder/agent-engine/deploy
- https://docs.cloud.google.com/agent-builder/agent-engine/use/langgraph
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, dotenv_values
import os
os.environ["GOOGLE_AUTH_DISABLE_GCE_METADATA"] = "1"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

# Agent metadata
AGENT_DISPLAY_NAME = "Belden Sales AI Agent"
AGENT_DESCRIPTION = """
Enterprise AI Agent for Belden sales operations:
- Lead Qualification: Automatically qualify and route Salesforce leads using AI
- Ticket Triage: Categorize and route support tickets with intelligent analysis

Integrates with:
- Salesforce CRM (leads, cases, tasks)
- SAP ERP (business partner, orders)
- LangSmith (tracing and monitoring)
"""

# GCP Configuration (from environment)
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

# ============================================================================
# Environment Variables to Pass to Agent
# ============================================================================

def get_agent_env_vars() -> dict:
    """
    Get environment variables to pass to the deployed agent.
    
    These will be available to the agent at runtime.
    """
    dotenv_path = Path('.env')
    env_vars = {}
    
    if dotenv_path.exists():
        env_dict = dotenv_values(dotenv_path)
        
        # Keys to include in the deployed agent
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
            "SALESFORCE_AUTH_TYPE",  # IMPORTANT: client_credentials or password
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

            # Routing Configuration - Both naming conventions
            "ROUTING_AE_OWNER_ID",
            "ROUTING_SDR_OWNER_ID",
            "ROUTING_NURTURE_OWNER_ID",
            "ROUTING_ESCALATION_OWNER_ID",
            "DEFAULT_AE_OWNER_ID",
            "DEFAULT_SDR_OWNER_ID",
            "DEFAULT_NURTURE_OWNER_ID",
            "DEFAULT_ESCALATION_OWNER_ID",
            
            # Product Owner Emails (Optional - for specific product routing)
            "PRODUCT_OWNER_SWITCHES",
            "PRODUCT_OWNER_CABLES",
            "PRODUCT_OWNER_CONNECTORS",
            "PRODUCT_OWNER_SOFTWARE",
            "PRODUCT_OWNER_INFRASTRUCTURE",
            "PRODUCT_OWNER_GENERAL",
        ]
        
        for key in required_keys:
            value = env_dict.get(key) or os.getenv(key)
            if value:
                env_vars[key] = value
        
        logger.info(f"Environment variables loaded: {list(env_vars.keys())}")
    else:
        logger.warning(".env file not found. Using system environment variables.")
        # Fallback to critical system environment variables
        critical_keys = [
            "OPENAI_API_KEY",
            "RESEND_API_KEY",
            "SALES_AGENT_EMAIL",
            "PRODUCT_EXPERT_EMAIL",
            "SERVICES_AGENT_EMAIL",
            "NOTIFICATION_EMAIL"
        ]
        for key in critical_keys:
            value = os.getenv(key)
            if value:
                env_vars[key] = value
    
    return env_vars


# ============================================================================
# Main Deployment Logic
# ============================================================================

def validate_config():
    """Validate required configuration before deployment."""
    errors = []
    
    if not PROJECT_ID:
        errors.append("PROJECT_ID is not set")
    
    if not STAGING_BUCKET:
        errors.append("STAGING_BUCKET is not set (required for deployment)")
    
    if not os.getenv("OPENAI_API_KEY"):
        errors.append("OPENAI_API_KEY is not set (required for LLM)")
    
    # Warn about missing email configuration (not blocking, but recommended)
    if not os.getenv("RESEND_API_KEY"):
        logger.warning("⚠️  RESEND_API_KEY is not set - email notifications will not work")
    if not os.getenv("SALES_AGENT_EMAIL"):
        logger.warning("⚠️  SALES_AGENT_EMAIL is not set - lead emails will not be sent")
    if not os.getenv("PRODUCT_EXPERT_EMAIL"):
        logger.warning("⚠️  PRODUCT_EXPERT_EMAIL is not set - product complaint emails will not be sent")
    if not os.getenv("SERVICES_AGENT_EMAIL"):
        logger.warning("⚠️  SERVICES_AGENT_EMAIL is not set - IT support emails will not be sent")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease update your .env file with the required values.")
        sys.exit(1)
    
    logger.info("✅ Configuration validated successfully")


def deploy_lead_qualification_agent():
    """Deploy only the Lead Qualification agent."""
    import vertexai
    from vertexai import agent_engines
    from src.app import LeadQualificationAgentApp
    
    validate_config()
    
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET
    )
    
    agent_to_deploy = LeadQualificationAgentApp(
        project=PROJECT_ID,
        location=LOCATION,
        use_llm=True
    )
    
    env_vars = get_agent_env_vars()
    
    logger.info(f"Deploying Lead Qualification Agent to {LOCATION}...")
    
    remote_agent = agent_engines.create(
        agent_engine=agent_to_deploy,
        requirements="requirements.txt",
        extra_packages=["src"],
        display_name="Belden Lead Qualification Agent",
        description="AI-powered lead qualification with Salesforce and SAP integration",
        env_vars=env_vars,
    )
    
    logger.info(f"✅ Agent deployed: {remote_agent.name}")
    return remote_agent


def deploy_ticket_triage_agent():
    """Deploy only the Ticket Triage agent."""
    import vertexai
    from vertexai import agent_engines
    from src.app import TicketTriageAgentApp
    
    validate_config()
    
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET
    )
    
    agent_to_deploy = TicketTriageAgentApp(
        project=PROJECT_ID,
        location=LOCATION,
        use_llm=True
    )
    
    env_vars = get_agent_env_vars()
    
    logger.info(f"Deploying Ticket Triage Agent to {LOCATION}...")
    
    remote_agent = agent_engines.create(
        agent_engine=agent_to_deploy,
        requirements="requirements.txt",
        extra_packages=["src"],
        display_name="Belden Ticket Triage Agent",
        description="AI-powered support ticket triage with Salesforce integration",
        env_vars=env_vars,
    )
    
    logger.info(f"✅ Agent deployed: {remote_agent.name}")
    return remote_agent


def deploy_combined_agent():
    """Deploy the combined Belden Sales Agent."""
    import vertexai
    from vertexai import agent_engines
    from src.app import BeldenSalesAgentApp
    
    validate_config()
    
    logger.info(f"Initializing Vertex AI for project: {PROJECT_ID}, location: {LOCATION}")
    
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET
    )
    
    logger.info("Vertex AI SDK initialized successfully")
    
    # Create agent instance
    agent_to_deploy = BeldenSalesAgentApp(
        project=PROJECT_ID,
        location=LOCATION,
        use_llm=True
    )
    
    # Get environment variables
    env_vars = get_agent_env_vars()
    
    # Check for existing agent
    logger.info(f"Checking for existing agent: '{AGENT_DISPLAY_NAME}'...")
    
    try:
        existing_agents = agent_engines.list()
        found_agent = next(
            (agent for agent in existing_agents if agent.display_name == AGENT_DISPLAY_NAME),
            None
        )
    except Exception as e:
        logger.warning(f"Could not list existing agents: {e}")
        found_agent = None
    
    remote_agent = None
    
    try:
        if found_agent:
            logger.info(f"Found existing agent: {found_agent.name}")
            logger.info("Updating agent...")
            
            remote_agent = agent_engines.update(
                resource_name=found_agent.name,
                agent_engine=agent_to_deploy,
                requirements="requirements.txt",
                extra_packages=["src"],
                display_name=AGENT_DISPLAY_NAME,
                description=AGENT_DESCRIPTION,
                env_vars=env_vars,
            )
            
            logger.info("✅ Agent Engine updated successfully!")
        else:
            logger.info(f"No existing agent found. Creating new agent...")
            
            remote_agent = agent_engines.create(
                agent_engine=agent_to_deploy,
                requirements="requirements.txt",
                extra_packages=["src"],
                display_name=AGENT_DISPLAY_NAME,
                description=AGENT_DESCRIPTION,
                env_vars=env_vars,
            )
            
            logger.info("✅ New Agent Engine created successfully!")
        
        # Display results
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 DEPLOYMENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Agent Resource Name: {remote_agent.name}")
        logger.info(f"Project: {PROJECT_ID}")
        logger.info(f"Location: {LOCATION}")
        logger.info("")
        logger.info("📋 Available Operations:")
        logger.info("  - qualify_lead(lead_data={...}, use_llm=True)")
        logger.info("  - triage_ticket(case_data={...}, use_llm=True)")
        logger.info("  - query(action='health')")
        logger.info("")
        logger.info("🔗 Vertex AI Console:")
        logger.info(f"  https://console.cloud.google.com/vertex-ai/agents?project={PROJECT_ID}")
        logger.info("=" * 60)
        
        return remote_agent
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        sys.exit(1)


def test_deployed_agent(resource_name: str):
    """Test a deployed agent."""
    import vertexai
    from vertexai import agent_engines
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    logger.info(f"Testing agent: {resource_name}")
    
    # Get the agent
    agent = agent_engines.get(resource_name)
    
    # Test health check
    logger.info("Testing health check...")
    result = agent.query(action="health")
    logger.info(f"Health: {result}")
    
    # Test lead qualification with sample data
    logger.info("\nTesting lead qualification...")
    sample_lead = {
        "Id": "00Q000000TEST001",
        "Company": "Test Corp",
        "Title": "CTO",
        "Industry": "Technology",
        "Rating": "Hot",
        "AnnualRevenue": 5000000,
        "NumberOfEmployees": 500,
        "LeadSource": "Partner Referral"
    }
    result = agent.qualify_lead(lead_data=sample_lead, use_llm=True)
    logger.info(f"Lead qualification result: {result}")
    
    return result


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Main entry point for deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy Belden Sales Agent to Vertex AI Agent Engine"
    )
    parser.add_argument(
        "--mode",
        choices=["combined", "lead", "ticket", "test"],
        default="combined",
        help="Deployment mode (default: combined)"
    )
    parser.add_argument(
        "--resource-name",
        type=str,
        help="Agent resource name (required for test mode)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🚀 BELDEN SALES AGENT DEPLOYMENT")
    logger.info("=" * 60)
    logger.info(f"Project: {PROJECT_ID}")
    logger.info(f"Location: {LOCATION}")
    logger.info(f"Staging Bucket: {STAGING_BUCKET}")
    logger.info(f"Mode: {args.mode}")
    logger.info("=" * 60)
    
    if args.mode == "combined":
        deploy_combined_agent()
    elif args.mode == "lead":
        deploy_lead_qualification_agent()
    elif args.mode == "ticket":
        deploy_ticket_triage_agent()
    elif args.mode == "test":
        if not args.resource_name:
            logger.error("--resource-name is required for test mode")
            sys.exit(1)
        test_deployed_agent(args.resource_name)


if __name__ == "__main__":
    main()
