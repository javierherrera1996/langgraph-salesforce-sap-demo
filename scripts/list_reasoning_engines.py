#!/usr/bin/env python3
"""
List all Reasoning Engines deployed in Vertex AI.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from google.cloud import aiplatform

def list_reasoning_engines():
    """List all deployed reasoning engines."""
    print("=" * 60)
    print("🔍 LISTING VERTEX AI REASONING ENGINES")
    print("=" * 60)

    project_id = os.getenv("PROJECT_ID", "logical-hallway-485016-r7")
    location = os.getenv("LOCATION", "us-central1")

    print(f"\nProject: {project_id}")
    print(f"Location: {location}")
    print("")

    try:
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Import the reasoning engine service
        from google.cloud.aiplatform_v1beta1 import ReasoningEngineServiceClient

        client = ReasoningEngineServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )

        parent = f"projects/{project_id}/locations/{location}"

        print(f"🔄 Fetching reasoning engines from: {parent}")
        print("")

        # List reasoning engines
        request = {"parent": parent}
        engines = list(client.list_reasoning_engines(request=request))

        if not engines:
            print("❌ NO REASONING ENGINES FOUND")
            print("")
            print("You need to deploy the agent first:")
            print("  python deploy_agent.py")
            print("")
            return None

        print(f"✅ FOUND {len(engines)} REASONING ENGINE(S):")
        print("")

        for i, engine in enumerate(engines, 1):
            engine_id = engine.name.split('/')[-1]
            print(f"Engine {i}:")
            print(f"  Name: {engine.display_name or 'N/A'}")
            print(f"  ID: {engine_id}")
            print(f"  Full Name: {engine.name}")
            print(f"  State: {engine.state.name if hasattr(engine, 'state') else 'N/A'}")
            print("")

            # Construct endpoint URL
            endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}:query"
            print(f"  🎯 AGENT_ENDPOINT:")
            print(f"  {endpoint}")
            print("")

        print("=" * 60)
        print("✅ NEXT STEPS:")
        print("=" * 60)
        print("")
        print("1. Copy the AGENT_ENDPOINT from above")
        print("")
        print("2. Update the Cloud Run backend:")
        print("   cd backend_for_lovable")
        print("   gcloud run services update belden-agent-gateway \\")
        print("     --region us-central1 \\")
        print(f"     --set-env-vars \"AGENT_ENDPOINT=PASTE_ENDPOINT_HERE\"")
        print("")
        print("3. Test the integration:")
        print("   curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health")
        print("")

        return engines[0] if engines else None

    except Exception as e:
        print(f"❌ Error: {e}")
        print("")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    list_reasoning_engines()
