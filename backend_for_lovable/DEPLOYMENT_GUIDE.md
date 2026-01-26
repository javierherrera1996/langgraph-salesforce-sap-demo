# Complete Deployment Guide: From Agent to Lovable

This guide walks you through the complete deployment process: Main Agent → API Gateway → Lovable Integration.

## Overview

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│  Lovable        │─────▶│  API Gateway     │─────▶│  Vertex AI Agent    │
│  Frontend       │      │  (Cloud Run)     │      │  Engine             │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Service Account │
                         │  (Auto Auth)     │
                         └──────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Salesforce API  │
                         └──────────────────┘
```

## Phase 1: Deploy Main Vertex AI Agent

### Step 1: Verify Authentication

```bash
cd /Users/javierherrera/Documents/programacion/belden-demo/langgraph-salesforce-sap-demo

# Test Vertex AI authentication
python scripts/test_vertex_auth.py

# Test Salesforce authentication
python scripts/test_salesforce_auth.py
```

Both tests should pass with ✅ marks.

### Step 2: Deploy the Agent

```bash
# Deploy to Vertex AI Agent Engine
python deploy_agent.py
```

**IMPORTANT**: Save the endpoint URL from the output. It will look like:
```
https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/1234567890:query
```

### Step 3: Test the Deployed Agent (Optional)

```bash
# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Test the agent
curl -X POST "YOUR_AGENT_ENDPOINT_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to report a complaint about a defective cable"
  }'
```

## Phase 2: Deploy API Gateway to Cloud Run

### Step 1: Navigate to Backend Directory

```bash
cd backend_for_lovable
```

### Step 2: Set Agent Endpoint (from Phase 1, Step 2)

```bash
export AGENT_ENDPOINT="YOUR_AGENT_ENDPOINT_URL_FROM_PHASE_1"
```

### Step 3: Deploy to Cloud Run

```bash
bash deploy.sh
```

This will:
- Build the Docker container
- Deploy to Cloud Run
- Configure environment variables
- Return your API Gateway URL

**IMPORTANT**: Save the Service URL from the output. It will look like:
```
https://belden-agent-gateway-xxxxx-uc.a.run.app
```

### Step 4: Test the API Gateway

```bash
# Test health endpoint
curl https://YOUR_GATEWAY_URL/health

# Test chat endpoint
curl -X POST https://YOUR_GATEWAY_URL/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "I need help with a product issue"
  }'
```

You should get a response from the agent!

## Phase 3: Integrate with Lovable

### Step 1: Update Lovable Frontend Code

In your Lovable project, add the API configuration:

```javascript
// config.js or similar
const BELDEN_API = {
  baseUrl: "https://YOUR_GATEWAY_URL", // from Phase 2, Step 3
  endpoints: {
    chat: "/chat",
    qualifyLead: "/qualify-lead",
    classifyTicket: "/classify-ticket",
    health: "/health"
  }
};

export default BELDEN_API;
```

### Step 2: Create API Client

```javascript
// api/beldenAgent.js
import BELDEN_API from './config';

class BeldenAgentClient {
  constructor() {
    this.baseUrl = BELDEN_API.baseUrl;
    this.sessionId = localStorage.getItem('belden_session_id') || null;
  }

  async chat(message, additionalData = {}) {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: this.sessionId,
          ...additionalData
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      // Save session ID for conversation continuity
      if (data.session_id) {
        this.sessionId = data.session_id;
        localStorage.setItem('belden_session_id', data.session_id);
      }

      return data;
    } catch (error) {
      console.error('Belden Agent API Error:', error);
      throw error;
    }
  }

  async qualifyLead(leadData) {
    try {
      const response = await fetch(`${this.baseUrl}/qualify-lead`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(leadData)
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Lead Qualification Error:', error);
      throw error;
    }
  }

  async classifyTicket(ticketData) {
    try {
      const response = await fetch(`${this.baseUrl}/classify-ticket`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(ticketData)
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ticket Classification Error:', error);
      throw error;
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health Check Error:', error);
      return { status: 'unhealthy', error: error.message };
    }
  }

  clearSession() {
    this.sessionId = null;
    localStorage.removeItem('belden_session_id');
  }
}

export default new BeldenAgentClient();
```

### Step 3: Use in Components

#### Chat Component Example

```javascript
import React, { useState } from 'react';
import beldenAgent from './api/beldenAgent';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Call Belden Agent API
      const response = await beldenAgent.chat(input);

      // Add agent response
      const agentMessage = {
        role: 'assistant',
        content: response.response
      };
      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'error',
        content: 'Sorry, I encountered an error. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="loading">Agent is thinking...</div>}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

#### Lead Qualification Form Example

```javascript
import React, { useState } from 'react';
import beldenAgent from './api/beldenAgent';

function LeadForm() {
  const [formData, setFormData] = useState({
    Name: '',
    Company: '',
    Email: '',
    Phone: '',
    Industry: '',
    AnnualRevenue: ''
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await beldenAgent.qualifyLead(formData);
      setResult(response);
    } catch (error) {
      setResult({
        success: false,
        error: 'Failed to qualify lead'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Name"
        value={formData.Name}
        onChange={(e) => setFormData({...formData, Name: e.target.value})}
      />
      <input
        type="text"
        placeholder="Company"
        value={formData.Company}
        onChange={(e) => setFormData({...formData, Company: e.target.value})}
      />
      <input
        type="email"
        placeholder="Email"
        value={formData.Email}
        onChange={(e) => setFormData({...formData, Email: e.target.value})}
      />
      {/* Add other fields */}

      <button type="submit" disabled={loading}>
        {loading ? 'Qualifying...' : 'Qualify Lead'}
      </button>

      {result && (
        <div className="result">
          {result.success ? (
            <p>Lead qualified successfully!</p>
          ) : (
            <p>Error: {result.error}</p>
          )}
        </div>
      )}
    </form>
  );
}

export default LeadForm;
```

## Verification Checklist

### ✅ Phase 1: Vertex AI Agent
- [ ] Service Account created and configured
- [ ] Salesforce authentication working (test_salesforce_auth.py passes)
- [ ] Vertex AI authentication working (test_vertex_auth.py passes)
- [ ] Agent deployed to Vertex AI (deploy_agent.py succeeds)
- [ ] Agent endpoint URL saved

### ✅ Phase 2: API Gateway
- [ ] Backend deployed to Cloud Run (deploy.sh succeeds)
- [ ] AGENT_ENDPOINT environment variable set
- [ ] Health check returns "healthy" status
- [ ] Chat endpoint returns valid responses
- [ ] Gateway URL saved

### ✅ Phase 3: Lovable Integration
- [ ] API configuration added to Lovable
- [ ] API client implemented
- [ ] Chat interface working
- [ ] Lead qualification working (if needed)
- [ ] Ticket classification working (if needed)

## Troubleshooting

### Agent Endpoint Not Set
**Error**: "AGENT_ENDPOINT not configured"

**Solution**:
```bash
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=YOUR_ENDPOINT_URL"
```

### CORS Errors in Lovable
**Error**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution**: The backend is configured to allow all origins. If still seeing errors:
1. Check browser console for exact error
2. Verify the Gateway URL is correct
3. Try clearing browser cache

### Authentication Failures
**Error**: "Authentication failed" or "401 Unauthorized"

**Solution**:
1. Verify Service Account has proper permissions
2. Check Cloud Run service identity
3. Run: `gcloud run services describe belden-agent-gateway --region us-central1`

### Timeout Errors
**Error**: "Request timed out"

**Solution**:
1. Agent processing may take time (especially first request)
2. Increase timeout in Cloud Run:
```bash
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --timeout 120
```

## Monitoring

### View API Gateway Logs
```bash
gcloud run services logs read belden-agent-gateway \
  --region us-central1 \
  --limit 100
```

### View Agent Logs
```bash
gcloud logging read \
  "resource.type=aiplatform.googleapis.com/ReasoningEngine" \
  --limit 50
```

### Monitor Health
Set up a cron job or monitoring service to ping:
```
GET https://YOUR_GATEWAY_URL/health
```

## Security Best Practices

1. **CORS Configuration**: Update `main.py` to restrict origins in production:
   ```python
   allow_origins=["https://your-lovable-domain.com"]
   ```

2. **API Authentication**: Consider adding API key authentication:
   ```python
   from fastapi import Header, HTTPException

   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("API_KEY"):
           raise HTTPException(status_code=401)
   ```

3. **Rate Limiting**: Implement rate limiting to prevent abuse

4. **Service Account**: Regularly rotate Service Account keys

## Cost Optimization

- **Cloud Run**: Pay only for actual usage
- **Vertex AI**: Pay per query
- **Optimization tips**:
  - Set `--max-instances` to control scaling
  - Use `--min-instances=0` (default) for zero cost when idle
  - Monitor usage in Cloud Console

## Support

For issues:
1. Check logs (see Monitoring section)
2. Verify all checklist items
3. Review Troubleshooting section
4. Check Service Account permissions
