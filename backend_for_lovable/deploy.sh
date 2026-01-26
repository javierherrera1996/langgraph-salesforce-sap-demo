#!/bin/bash
# Deploy Belden AI Agent API Gateway to Cloud Run

set -e

# Configuration
PROJECT_ID="logical-hallway-485016-r7"
REGION="us-central1"
SERVICE_NAME="belden-agent-gateway"

echo "======================================================================="
echo "🚀 DEPLOYING BELDEN AI AGENT API GATEWAY TO CLOUD RUN"
echo "======================================================================="
echo ""
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "❌ Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Check if AGENT_ENDPOINT is provided
if [ -z "$AGENT_ENDPOINT" ]; then
    echo "⚠️  AGENT_ENDPOINT not set"
    echo ""
    echo "You need to deploy the main Vertex AI Agent first to get the endpoint URL."
    echo "After deployment, you can update the service with:"
    echo ""
    echo "  export AGENT_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/reasoningEngines/YOUR_ENGINE_ID:query"
    echo "  gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars \"AGENT_ENDPOINT=\$AGENT_ENDPOINT\""
    echo ""
    read -p "Continue deployment without AGENT_ENDPOINT? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
    AGENT_ENDPOINT_FLAG=""
else
    echo "✅ AGENT_ENDPOINT: $AGENT_ENDPOINT"
    AGENT_ENDPOINT_FLAG="AGENT_ENDPOINT=$AGENT_ENDPOINT,"
fi

echo ""
echo "🔄 Deploying to Cloud Run..."
echo ""

# Deploy using source-based deployment (simplest method)
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 60 \
    --set-env-vars "${AGENT_ENDPOINT_FLAG}PROJECT_ID=$PROJECT_ID,LOCATION=$REGION" \
    --project $PROJECT_ID

echo ""
echo "======================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================================================================="
echo ""

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)')

echo "🎯 Service URL: $SERVICE_URL"
echo ""
echo "📋 Next Steps:"
echo ""

if [ -z "$AGENT_ENDPOINT" ]; then
    echo "1. Deploy the main Vertex AI Agent:"
    echo "   cd .. && python deploy_agent.py"
    echo ""
    echo "2. Get the agent endpoint URL from the deployment output"
    echo ""
    echo "3. Update this service with the endpoint:"
    echo "   export AGENT_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/reasoningEngines/YOUR_ENGINE_ID:query"
    echo "   gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars \"AGENT_ENDPOINT=\$AGENT_ENDPOINT\""
    echo ""
fi

echo "4. Test the health endpoint:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "5. Update your Lovable frontend with this URL:"
echo "   const API_URL = \"$SERVICE_URL\";"
echo ""
echo "6. Test a chat request:"
echo "   curl -X POST $SERVICE_URL/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"Hello, I need help with a product\"}'"
echo ""

# Show logs command
echo "📊 View logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50"
echo ""
