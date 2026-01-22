"""
Main Application Entry Point
FastAPI application for LangGraph Salesforce SAP orchestration demo.
"""

# CRITICAL: Load environment variables FIRST before any other imports
# This ensures LangSmith tracing is configured before langchain is imported
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Force LangSmith tracing environment variables
if os.environ.get("LANGSMITH_API_KEY") and not os.environ.get("LANGSMITH_API_KEY", "").startswith("your_"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    print(f"🔍 LangSmith Tracing: ENABLED (Project: {os.environ.get('LANGCHAIN_PROJECT', 'default')})")
else:
    print("⚠️ LangSmith Tracing: DISABLED (no valid API key)")

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.config import get_settings


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging():
    """Configure logging for the application."""
    settings = get_settings()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("LangGraph Salesforce SAP Demo - Starting Up")
    logger.info("=" * 60)
    
    settings = get_settings()
    
    # Configure LangSmith tracing
    settings.configure_langsmith()
    logger.info(f"LangSmith Project: {settings.langsmith.project}")
    logger.info(f"LangSmith Tracing: {settings.langsmith.tracing_v2}")
    
    # Log configuration (without secrets)
    logger.info(f"Salesforce Instance: {settings.salesforce.instance_url}")
    logger.info(f"SAP Mode: {settings.sap.mode}")
    logger.info(f"Debug Mode: {settings.debug}")
    
    # Pre-authenticate with Salesforce
    try:
        from src.tools import salesforce
        salesforce.authenticate()
        logger.info("Salesforce authentication: SUCCESS")
    except Exception as e:
        logger.warning(f"Salesforce authentication: MOCK MODE ({e})")
    
    logger.info("=" * 60)
    logger.info("Application Ready - Listening for requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("LangGraph Salesforce SAP Demo - Shutting Down")
    logger.info("=" * 60)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="LangGraph Salesforce SAP Demo",
    description="""
## Enterprise AI Orchestration Demo

This API demonstrates LangGraph-based orchestration of **Salesforce CRM** and **SAP** 
for two enterprise use cases:

### 🎯 Use Case 1: Lead Qualification & Routing
Automatically qualify leads, calculate scores, and route to the appropriate team:
- **Account Executive (AE)** - High-value leads (score ≥ 0.75)
- **Sales Dev Rep (SDR)** - Qualified leads (score 0.45-0.74)
- **Nurture Campaign** - Early-stage leads (score < 0.45)

### 🎫 Use Case 2: Ticket Triage
Automatically categorize support tickets and take appropriate action:
- **howto** → Auto-reply with KB articles
- **billing** → Request additional information
- **outage** → Escalate to incident team
- **security** → Escalate to security team

### 🔧 Key Features
- **LangGraph** for workflow orchestration
- **Deterministic routing** (no hidden LLM decisions)
- **LangSmith tracing** for full observability
- **Mock mode** for demo without live credentials

### 📚 Demo Instructions
1. Call `GET /demo/leads` or `GET /demo/cases` to see available test data
2. Call `POST /run/lead` or `POST /run/ticket` to execute workflows
3. View traces in LangSmith dashboard
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================================================
# Middleware
# ============================================================================

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if get_settings().debug else "An unexpected error occurred"
        }
    )


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "LangGraph Salesforce SAP Demo",
        "version": "1.0.0",
        "description": "Enterprise AI orchestration demo using LangGraph",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "lead_qualification": "POST /run/lead",
            "ticket_triage": "POST /run/ticket",
            "demo_leads": "GET /demo/leads",
            "demo_cases": "GET /demo/cases",
            "graph_info_lead": "GET /graphs/lead",
            "graph_info_ticket": "GET /graphs/ticket"
        }
    }


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(router)


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Run the application with uvicorn."""
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
