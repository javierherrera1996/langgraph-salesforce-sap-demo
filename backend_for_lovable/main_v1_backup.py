#!/usr/bin/env python3
"""
API Gateway for Lovable to connect to Vertex AI Agent
This backend handles authentication automatically using Service Account
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Belden AI Agent API Gateway")

# CORS configuration for Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Lovable's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment variables
PROJECT_ID = os.getenv("PROJECT_ID", "logical-hallway-485016-r7")
LOCATION = os.getenv("LOCATION", "us-central1")
SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Vertex AI Agent endpoint (will be set after deployment)
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT")  # e.g., https://us-central1-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/reasoningEngines/{engine_id}:query


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    session_id: Optional[str] = None
    lead_data: Optional[Dict[str, Any]] = None
    ticket_data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    response: str
    session_id: Optional[str] = None
    error: Optional[str] = None


def get_access_token() -> str:
    """
    Generate access token using Service Account.
    This token is valid for 1 hour and is refreshed automatically.
    """
    try:
        if SERVICE_ACCOUNT_PATH:
            # Use Service Account from file
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        else:
            # Use Application Default Credentials (for Cloud Run)
            from google.auth import default
            credentials, _ = default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )

        # Refresh token
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Belden AI Agent API Gateway",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test token generation
        token = get_access_token()
        return {
            "status": "healthy",
            "authentication": "ok",
            "agent_endpoint": AGENT_ENDPOINT or "not_configured"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat endpoint for Lovable frontend.

    This endpoint:
    1. Receives a message from Lovable
    2. Generates a GCP token automatically
    3. Calls Vertex AI Agent Engine
    4. Returns the response to Lovable
    """
    logger.info(f"Received chat request: {request.message[:50]}...")

    if not AGENT_ENDPOINT:
        raise HTTPException(
            status_code=500,
            detail="AGENT_ENDPOINT not configured. Please set the environment variable."
        )

    try:
        # 1. Get access token automatically
        access_token = get_access_token()
        logger.info("✅ Access token generated successfully")

        # 2. Prepare request to Vertex AI
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Build the payload based on request type
        # The Vertex AI agent expects: action, lead_data, case_data, use_llm

        # Determine action based on what data is provided
        if request.lead_data:
            action = "qualify_lead"
            payload = {
                "action": action,
                "lead_data": request.lead_data,
                "use_llm": True
            }
        elif request.ticket_data:
            action = "classify_complaint"
            payload = {
                "action": action,
                "case_data": request.ticket_data,
                "use_llm": True
            }
        else:
            # If just a message, treat as health check or error
            if request.message.lower().strip() in ["health", "ping", "status"]:
                payload = {"action": "health"}
            else:
                # Return error for unsupported message format
                return ChatResponse(
                    success=False,
                    response="Please use the /qualify-lead or /classify-ticket endpoints for specific actions.",
                    error="Generic chat not supported. Use structured endpoints."
                )

        # 3. Call Vertex AI Agent Engine
        logger.info(f"Calling Vertex AI Agent at: {AGENT_ENDPOINT}")
        response = requests.post(
            AGENT_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60  # 60 second timeout
        )

        response.raise_for_status()

        # 4. Parse and return response
        result = response.json()
        logger.info("✅ Agent response received successfully")

        # Format the response based on the action
        if request.lead_data:
            # Lead qualification response
            response_text = f"Lead qualification complete.\n"
            response_text += f"Score: {result.get('score', 0.0):.0%}\n"
            response_text += f"Routing: {result.get('routing', {}).get('owner_type', 'N/A')}\n"
            response_text += f"Reasoning: {result.get('reasoning', 'N/A')}"
        elif request.ticket_data:
            # Ticket classification response
            response_text = f"Ticket classified.\n"
            if result.get('is_product_complaint'):
                response_text += f"Type: Product Complaint\n"
                response_text += f"Category: {result.get('product_category', 'N/A')}\n"
            elif result.get('is_it_support'):
                response_text += "Type: IT Support\n"
            response_text += f"Action: {result.get('action_taken', 'N/A')}\n"
            response_text += f"Reasoning: {result.get('reasoning', 'N/A')}"
        else:
            # Health check or other
            response_text = str(result)

        return ChatResponse(
            success=True,
            response=response_text,
            session_id=request.session_id,
            error=None
        )

    except requests.exceptions.Timeout:
        logger.error("Request to Vertex AI timed out")
        raise HTTPException(status_code=504, detail="Request timed out")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Vertex AI: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Vertex AI error: {e.response.text}"
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qualify-lead")
async def qualify_lead(lead_data: Dict[str, Any]):
    """
    Endpoint specifically for lead qualification.
    Lovable can call this directly with lead data.
    """
    logger.info(f"Lead qualification request for: {lead_data.get('Name', 'Unknown')}")

    request = ChatRequest(
        message=f"Qualify this lead: {lead_data}",
        lead_data=lead_data
    )

    return await chat_with_agent(request)


@app.post("/classify-ticket")
async def classify_ticket(ticket_data: Dict[str, Any]):
    """
    Endpoint specifically for ticket classification.
    Lovable can call this directly with ticket data.
    """
    logger.info(f"Ticket classification request: {ticket_data.get('subject', 'Unknown')}")

    request = ChatRequest(
        message=f"Classify this ticket: {ticket_data}",
        ticket_data=ticket_data
    )

    return await chat_with_agent(request)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
