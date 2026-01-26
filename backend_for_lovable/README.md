# Belden AI Agent API Gateway for Lovable

This backend API gateway allows Lovable (or any frontend) to connect to the Vertex AI Agent without handling Google Cloud authentication tokens directly.

## Features

- **Automatic Token Management**: Service Account handles token generation and refresh automatically
- **RESTful API**: Simple HTTP endpoints for chat, lead qualification, and ticket classification
- **CORS Enabled**: Cross-origin requests supported for frontend integration
- **Health Checks**: Built-in endpoints for monitoring

## Architecture

```
Lovable Frontend → API Gateway (this backend) → Vertex AI Agent Engine
                         ↓
                  Service Account Auth
                  (automatic token refresh)
```

## Prerequisites

1. **Deployed Vertex AI Agent**: You must have deployed the main agent to Vertex AI Agent Engine first
2. **Service Account**: Google Cloud Service Account with Vertex AI permissions
3. **Agent Endpoint URL**: The URL of your deployed Vertex AI Agent

## Local Development

### 1. Install Dependencies

```bash
cd backend_for_lovable
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
# Google Cloud Configuration
PROJECT_ID=logical-hallway-485016-r7
LOCATION=us-central1

# Service Account (for local development)
GOOGLE_APPLICATION_CREDENTIALS=/Users/javierherrera/belden-ai-service-account.json

# Agent Endpoint (get this after deploying the main agent)
AGENT_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID:query
```

### 3. Run Locally

```bash
python main.py
```

The API will be available at `http://localhost:8080`

## Deploy to Cloud Run

### Option 1: Using gcloud CLI

```bash
# 1. Build and deploy in one command
gcloud run deploy belden-agent-gateway \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "PROJECT_ID=logical-hallway-485016-r7,LOCATION=us-central1,AGENT_ENDPOINT=YOUR_AGENT_ENDPOINT_URL"

# 2. Note the Service URL that gets printed (e.g., https://belden-agent-gateway-xxxxx.run.app)
```

### Option 2: Using Docker and Artifact Registry

```bash
# 1. Set variables
PROJECT_ID=logical-hallway-485016-r7
REGION=us-central1
SERVICE_NAME=belden-agent-gateway

# 2. Build Docker image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest .

# 3. Push to Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest

# 4. Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},AGENT_ENDPOINT=YOUR_AGENT_ENDPOINT_URL"
```

### Important: Set AGENT_ENDPOINT

After deploying the main agent to Vertex AI, you'll get an endpoint URL. Update the Cloud Run service:

```bash
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID:query"
```

## API Endpoints

### 1. Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "authentication": "ok",
  "agent_endpoint": "https://..."
}
```

### 2. Chat with Agent

```bash
POST /chat
Content-Type: application/json

{
  "message": "I want to report a complaint about a defective cable",
  "session_id": "optional-session-id",
  "lead_data": {},  // optional
  "ticket_data": {}  // optional
}
```

**Response:**
```json
{
  "success": true,
  "response": "I'll help you with that complaint...",
  "session_id": "session-123",
  "error": null
}
```

### 3. Qualify Lead

```bash
POST /qualify-lead
Content-Type: application/json

{
  "Name": "John Doe",
  "Company": "Acme Corp",
  "Email": "john@acme.com",
  "Industry": "Manufacturing"
}
```

### 4. Classify Ticket

```bash
POST /classify-ticket
Content-Type: application/json

{
  "subject": "Cable not working",
  "description": "The cable stopped working after 2 months",
  "priority": "High"
}
```

## Lovable Integration

### Frontend Code Example

```javascript
// Configure the API endpoint
const API_URL = "https://belden-agent-gateway-xxxxx.run.app";

// Chat function
async function chatWithAgent(message) {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      session_id: localStorage.getItem('session_id') || null
    })
  });

  const data = await response.json();

  // Save session ID for conversation continuity
  if (data.session_id) {
    localStorage.setItem('session_id', data.session_id);
  }

  return data.response;
}

// Lead qualification function
async function qualifyLead(leadData) {
  const response = await fetch(`${API_URL}/qualify-lead`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(leadData)
  });

  return await response.json();
}

// Ticket classification function
async function classifyTicket(ticketData) {
  const response = await fetch(`${API_URL}/classify-ticket`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(ticketData)
  });

  return await response.json();
}
```

## Security Notes

1. **Service Account**: In Cloud Run, Application Default Credentials are used automatically (no JSON key file needed)
2. **CORS**: Currently set to allow all origins (`*`). In production, update to:
   ```python
   allow_origins=["https://your-lovable-domain.com"]
   ```
3. **Authentication**: Consider adding API key authentication for production use

## Monitoring

View logs in Cloud Run:

```bash
gcloud run services logs read belden-agent-gateway \
  --region us-central1 \
  --limit 50
```

## Troubleshooting

### Error: "AGENT_ENDPOINT not configured"
- Make sure you've deployed the main agent first
- Set the AGENT_ENDPOINT environment variable in Cloud Run

### Error: "Authentication failed"
- Verify the Service Account has `roles/aiplatform.user` permission
- Check Cloud Run service identity has necessary permissions

### Error: "Request timed out"
- Agent processing may take time for complex queries
- Consider increasing timeout in main.py if needed

## Cost Optimization

Cloud Run charges based on:
- Request time (billed per 100ms)
- Memory allocation
- Number of requests

To optimize:
1. Use minimum memory allocation (512MB should be sufficient)
2. Set max instances to control costs: `--max-instances=10`
3. Enable request concurrency: `--concurrency=80`

## Next Steps

1. Deploy the main Vertex AI Agent
2. Get the agent endpoint URL
3. Deploy this backend to Cloud Run
4. Update Lovable frontend with the Cloud Run service URL
5. Test the integration
