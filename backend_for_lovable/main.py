#!/usr/bin/env python3
"""
API Gateway for Lovable to connect to Vertex AI Agent
This backend uses Vertex AI SDK to call the Agent Engine correctly
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Vertex AI imports
import vertexai
from vertexai import agent_engines

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

# Extract engine ID from AGENT_ENDPOINT
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT")
AGENT_ENGINE_ID = None

if AGENT_ENDPOINT:
    # Extract ID from URL like: .../reasoningEngines/123456789:query
    parts = AGENT_ENDPOINT.split("/reasoningEngines/")
    if len(parts) > 1:
        AGENT_ENGINE_ID = parts[1].replace(":query", "")
        logger.info(f"Extracted engine ID: {AGENT_ENGINE_ID}")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Global agent instance
_agent = None


def get_agent():
    """Get or initialize the Agent Engine."""
    global _agent

    if _agent is None:
        if not AGENT_ENGINE_ID:
            raise HTTPException(
                status_code=500,
                detail="AGENT_ENDPOINT not configured or invalid format"
            )

        try:
            logger.info(f"Initializing Agent Engine: {AGENT_ENGINE_ID}")
            resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
            _agent = agent_engines.get(resource_name)
            logger.info("Agent Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize agent: {str(e)}"
            )

    return _agent


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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Belden AI Agent API Gateway",
        "version": "3.0.0",
        "agent_endpoint": AGENT_ENDPOINT,
        "engine_id": AGENT_ENGINE_ID
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        agent = get_agent()
        result = agent.query(action="health")
        return {
            "status": "healthy",
            "agent_status": result,
            "agent_endpoint": AGENT_ENDPOINT,
            "engine_id": AGENT_ENGINE_ID
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "agent_endpoint": AGENT_ENDPOINT
        }


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat endpoint for Lovable frontend.

    Routes to the appropriate agent action based on the request.
    """
    logger.info(f"Received request with message: {request.message[:50]}...")

    try:
        agent = get_agent()

        # Determine action based on request data
        if request.lead_data:
            logger.info("Qualifying lead...")
            # Extract 'lead' from lead_data if it exists, otherwise use lead_data directly
            lead_data = request.lead_data.get('lead', request.lead_data)
            logger.info(f"Lead data: Company={lead_data.get('Company', 'N/A')}, Title={lead_data.get('Title', 'N/A')}")
            result = agent.query(
                action="qualify_lead",
                lead_data=lead_data,
                use_llm=True
            )

            # Format response
            response_text = f"Lead qualification complete.\n"
            response_text += f"Score: {result.get('score', 0.0):.0%}\n"
            response_text += f"Routing: {result.get('routing', {}).get('owner_type', 'N/A')}\n"
            response_text += f"Reasoning: {result.get('reasoning', 'N/A')}"

        elif request.ticket_data:
            logger.info("Classifying ticket...")
            # Extract 'case' from ticket_data if it exists, otherwise use ticket_data directly
            case_data = request.ticket_data.get('case', request.ticket_data)
            logger.info(f"Case data: Subject={case_data.get('Subject', 'N/A')}, Description={case_data.get('Description', 'N/A')[:50]}...")
            result = agent.query(
                action="classify_complaint",
                case_data=case_data,
                use_llm=True
            )

            # Format response
            response_text = f"Ticket classified.\n"
            if result.get('is_product_complaint'):
                response_text += f"Type: Product Complaint\n"
                response_text += f"Category: {result.get('product_category', 'N/A')}\n"
            elif result.get('is_it_support'):
                response_text += "Type: IT Support\n"
            response_text += f"Action: {result.get('action_taken', 'N/A')}\n"
            response_text += f"Reasoning: {result.get('reasoning', 'N/A')}"

        else:
            # Just a message - treat as health check
            if request.message.lower().strip() in ["health", "ping", "status"]:
                result = agent.query(action="health")
                response_text = f"Agent Status: {result.get('status', 'unknown')}"
            else:
                return ChatResponse(
                    success=False,
                    response="Please use /qualify-lead or /classify-ticket endpoints.",
                    error="Generic chat not supported"
                )

        logger.info("Agent response received successfully")

        return ChatResponse(
            success=True,
            response=response_text,
            session_id=request.session_id,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@app.post("/qualify-lead")
async def qualify_lead(lead_data: Dict[str, Any]):
    """
    Endpoint specifically for lead qualification.
    """
    logger.info(f"Lead qualification request for: {lead_data.get('Name', 'Unknown')}")

    request = ChatRequest(
        message="Qualify lead",
        lead_data=lead_data
    )

    return await chat_with_agent(request)


@app.post("/classify-ticket")
async def classify_ticket(ticket_data: Dict[str, Any]):
    """
    Endpoint specifically for ticket classification.
    """
    logger.info(f"Ticket classification request: {ticket_data.get('Subject', 'Unknown')}")

    request = ChatRequest(
        message="Classify ticket",
        ticket_data=ticket_data
    )

    return await chat_with_agent(request)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
