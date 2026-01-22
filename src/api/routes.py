"""
FastAPI Routes for LangGraph Orchestration
HTTP endpoints to trigger lead qualification and ticket triage workflows.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.graphs.lead_graph import run_lead_qualification, build_lead_graph
from src.graphs.ticket_graph import run_ticket_triage, build_ticket_graph
from src.tools import salesforce

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class LeadInput(BaseModel):
    """Input for lead qualification endpoint."""
    lead_id: Optional[str] = Field(
        None,
        description="Salesforce Lead ID. If not provided, fetches newest lead."
    )
    lead_data: Optional[dict] = Field(
        None,
        description="Full lead data object. If provided, skips fetch."
    )
    use_llm: bool = Field(
        True,
        description="Use LLM for intelligent scoring (default: True). Set to False for rule-based scoring."
    )


class TicketInput(BaseModel):
    """Input for ticket triage endpoint."""
    case_id: Optional[str] = Field(
        None,
        description="Salesforce Case ID. If not provided, fetches newest case."
    )
    case_data: Optional[dict] = Field(
        None,
        description="Full case data object. If provided, skips fetch."
    )
    use_llm: bool = Field(
        True,
        description="Use LLM for intelligent categorization (default: True). Set to False for rule-based."
    )


class WorkflowResponse(BaseModel):
    """Standard response for workflow execution."""
    success: bool
    workflow: str
    mode: str  # "llm" or "rule-based"
    timestamp: str
    execution_time_ms: float
    reasoning: Optional[str] = None  # LLM reasoning (prominent field)
    state: dict
    actions_executed: list[str]
    summary: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    services: dict


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(tags=["Orchestration"])


# ============================================================================
# Health Endpoint
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns system status and connectivity to external services.
    """
    logger.info("Health check requested")
    
    services = {
        "salesforce": "unknown",
        "sap": "unknown",
        "langgraph": "ok"
    }
    
    # Check Salesforce connectivity
    try:
        salesforce.authenticate()
        services["salesforce"] = "ok"
    except Exception as e:
        logger.warning(f"Salesforce health check failed: {e}")
        services["salesforce"] = "error"
    
    # SAP is mock by default, so always OK in demo mode
    from src.config import get_sap_config
    if get_sap_config().is_mock:
        services["sap"] = "ok (mock)"
    else:
        services["sap"] = "ok"
    
    overall_status = "healthy" if all(
        "ok" in v for v in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        services=services
    )


# ============================================================================
# Lead Qualification Endpoint
# ============================================================================

@router.post("/run/lead", response_model=WorkflowResponse)
async def run_lead_workflow(input_data: LeadInput = None):
    """
    Execute Lead Qualification & Routing workflow.
    
    This endpoint triggers the full lead qualification pipeline:
    1. Fetch lead from Salesforce (or use provided data)
    2. Enrich with SAP business context
    3. Calculate qualification score (LLM or rule-based)
    4. Determine routing (AE/SDR/Nurture)
    5. Execute actions (assign owner, create task, update status)
    
    **Demo Usage:**
    ```bash
    # Process newest lead with LLM (default)
    curl -X POST http://localhost:8000/run/lead
    
    # Process with rule-based scoring
    curl -X POST http://localhost:8000/run/lead \\
      -H "Content-Type: application/json" \\
      -d '{"use_llm": false}'
    
    # Process specific lead with LLM
    curl -X POST http://localhost:8000/run/lead \\
      -H "Content-Type: application/json" \\
      -d '{"lead_id": "00Q5g00000XXXXX", "use_llm": true}'
    ```
    """
    logger.info("=" * 60)
    logger.info("API: Lead Qualification Workflow Triggered")
    logger.info("=" * 60)
    
    start_time = datetime.utcnow()
    
    # Get use_llm flag (default True)
    use_llm = input_data.use_llm if input_data else True
    logger.info(f"Mode: {'🤖 LLM-Powered' if use_llm else '📊 Rule-Based'}")
    
    try:
        # Prepare lead data
        lead = None
        if input_data:
            if input_data.lead_data:
                lead = input_data.lead_data
                logger.info(f"Using provided lead data: {lead.get('Id', 'unknown')}")
            elif input_data.lead_id:
                lead = salesforce.get_lead_by_id(input_data.lead_id)
                if not lead:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Lead not found: {input_data.lead_id}"
                    )
                logger.info(f"Fetched lead by ID: {input_data.lead_id}")
        
        # Run workflow with LLM flag
        final_state = run_lead_qualification(lead, use_llm=use_llm)
        
        # Calculate execution time
        end_time = datetime.utcnow()
        execution_ms = (end_time - start_time).total_seconds() * 1000
        
        # Build summary with LLM analysis
        route = final_state.get("route", {})
        llm_analysis = final_state.get("llm_analysis", {})
        
        summary = {
            "lead_id": final_state.get("lead", {}).get("Id", "N/A"),
            "company": final_state.get("lead", {}).get("Company", "N/A"),
            "score": round(final_state.get("score", 0), 4),
            "mode": llm_analysis.get("model_used", "rule-based"),
            "routing": {
                "owner_type": route.get("owner_type", "N/A"),
                "priority": route.get("priority", "N/A"),
                "reason": route.get("reason", "N/A")[:200] if route.get("reason") else "N/A"
            },
            "llm_analysis": {
                "confidence": llm_analysis.get("confidence", 0),
                "reasoning": llm_analysis.get("reasoning", "")[:300] if llm_analysis.get("reasoning") else "",
                "key_factors": llm_analysis.get("key_factors", []),
                "recommended_action": llm_analysis.get("recommended_action", "")
            } if use_llm else None,
            "sap_enriched": bool(final_state.get("enriched", {}).get("business_partner_id")),
            "total_actions": len(final_state.get("actions_done", []))
        }
        
        logger.info(f"Workflow completed in {execution_ms:.2f}ms")
        logger.info(f"Summary: {summary}")
        
        # Extract reasoning for top-level display
        reasoning = llm_analysis.get("reasoning", "") if use_llm else "Rule-based scoring (no LLM reasoning)"
        
        return WorkflowResponse(
            success=True,
            workflow="lead_qualification",
            mode="🤖 LLM" if use_llm and llm_analysis.get("model_used") != "rule-based" else "📊 Rule-based",
            timestamp=start_time.isoformat(),
            execution_time_ms=round(execution_ms, 2),
            reasoning=reasoning,
            state=dict(final_state),
            actions_executed=final_state.get("actions_done", []),
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lead workflow failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


# ============================================================================
# Ticket Triage Endpoint
# ============================================================================

@router.post("/run/ticket", response_model=WorkflowResponse)
async def run_ticket_workflow(input_data: TicketInput = None):
    """
    Execute Customer Support Ticket Triage workflow.
    
    This endpoint triggers the full ticket triage pipeline:
    1. Fetch case from Salesforce (or use provided data)
    2. Categorize ticket (LLM or rule-based)
    3. Retrieve SAP order context
    4. Decide action (auto-reply, request info, escalate)
    5. Execute actions (post comment, update status, assign owner)
    
    **Demo Usage:**
    ```bash
    # Process newest case with LLM (default)
    curl -X POST http://localhost:8000/run/ticket
    
    # Process with rule-based categorization
    curl -X POST http://localhost:8000/run/ticket \\
      -H "Content-Type: application/json" \\
      -d '{"use_llm": false}'
    
    # Process specific case with LLM
    curl -X POST http://localhost:8000/run/ticket \\
      -H "Content-Type: application/json" \\
      -d '{"case_id": "5005g00000XXXXX", "use_llm": true}'
    ```
    """
    logger.info("=" * 60)
    logger.info("API: Ticket Triage Workflow Triggered")
    logger.info("=" * 60)
    
    start_time = datetime.utcnow()
    
    # Get use_llm flag (default True)
    use_llm = input_data.use_llm if input_data else True
    logger.info(f"Mode: {'🤖 LLM-Powered' if use_llm else '📊 Rule-Based'}")
    
    try:
        # Prepare case data
        case = None
        if input_data:
            if input_data.case_data:
                case = input_data.case_data
                logger.info(f"Using provided case data: {case.get('Id', 'unknown')}")
            elif input_data.case_id:
                case = salesforce.get_case_by_id(input_data.case_id)
                if not case:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Case not found: {input_data.case_id}"
                    )
                logger.info(f"Fetched case by ID: {input_data.case_id}")
        
        # Run workflow with LLM flag
        final_state = run_ticket_triage(case, use_llm=use_llm)
        
        # Calculate execution time
        end_time = datetime.utcnow()
        execution_ms = (end_time - start_time).total_seconds() * 1000
        
        # Build summary with LLM analysis
        decision = final_state.get("decision", {})
        llm_analysis = final_state.get("llm_analysis", {})
        
        summary = {
            "case_id": final_state.get("case", {}).get("Id", "N/A"),
            "case_number": final_state.get("case", {}).get("CaseNumber", "N/A"),
            "subject": final_state.get("case", {}).get("Subject", "N/A")[:50],
            "category": final_state.get("category", "N/A"),
            "mode": llm_analysis.get("model_used", "rule-based"),
            "action": decision.get("action", "N/A"),
            "escalated": decision.get("action") == "escalate",
            "priority_changed": decision.get("priority_change"),
            "kb_articles_suggested": len(final_state.get("kb_suggestions", [])),
            "sap_context_found": bool(final_state.get("sap_context", {}).get("business_partner_id")),
            "total_actions": len(final_state.get("actions_done", [])),
            "llm_analysis": {
                "confidence": llm_analysis.get("confidence", 0),
                "urgency": llm_analysis.get("urgency", ""),
                "sentiment": llm_analysis.get("sentiment", ""),
                "reasoning": llm_analysis.get("reasoning", "")[:300] if llm_analysis.get("reasoning") else "",
                "suggested_response_preview": llm_analysis.get("suggested_response", "")[:200] if llm_analysis.get("suggested_response") else ""
            } if use_llm else None
        }
        
        logger.info(f"Workflow completed in {execution_ms:.2f}ms")
        logger.info(f"Summary: {summary}")
        
        # Extract reasoning for top-level display
        reasoning = llm_analysis.get("reasoning", "") if use_llm else "Rule-based categorization (no LLM reasoning)"
        
        return WorkflowResponse(
            success=True,
            workflow="ticket_triage",
            mode="🤖 LLM" if use_llm and llm_analysis.get("model_used") != "rule-based" else "📊 Rule-based",
            timestamp=start_time.isoformat(),
            execution_time_ms=round(execution_ms, 2),
            reasoning=reasoning,
            state=dict(final_state),
            actions_executed=final_state.get("actions_done", []),
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ticket workflow failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


# ============================================================================
# Graph Visualization Endpoints
# ============================================================================

@router.get("/graphs/lead")
async def get_lead_graph_info():
    """
    Get information about the Lead Qualification graph structure.
    
    Useful for understanding the workflow nodes and edges.
    """
    graph = build_lead_graph()
    
    return {
        "name": "lead_qualification",
        "description": "Lead Qualification & Routing workflow",
        "nodes": [
            {"name": "FetchLead", "description": "Fetch lead from Salesforce"},
            {"name": "EnrichLead", "description": "Enrich with SAP business context"},
            {"name": "ScoreLead", "description": "Calculate qualification score"},
            {"name": "DecideRouting", "description": "Determine routing (AE/SDR/Nurture)"},
            {"name": "ExecuteActions", "description": "Execute Salesforce/SAP actions"}
        ],
        "edges": [
            {"from": "START", "to": "FetchLead"},
            {"from": "FetchLead", "to": "EnrichLead"},
            {"from": "EnrichLead", "to": "ScoreLead"},
            {"from": "ScoreLead", "to": "DecideRouting"},
            {"from": "DecideRouting", "to": "ExecuteActions"},
            {"from": "ExecuteActions", "to": "END"}
        ],
        "routing_rules": {
            "score >= 0.75": "Account Executive (P1)",
            "score 0.45-0.74": "Sales Dev Rep (P2)",
            "score < 0.45": "Nurture Campaign (P3)"
        }
    }


@router.get("/graphs/ticket")
async def get_ticket_graph_info():
    """
    Get information about the Ticket Triage graph structure.
    
    Useful for understanding the workflow nodes and edges.
    """
    graph = build_ticket_graph()
    
    return {
        "name": "ticket_triage",
        "description": "Customer Support Ticket Triage workflow",
        "nodes": [
            {"name": "FetchTicket", "description": "Fetch case from Salesforce"},
            {"name": "CategorizeTicket", "description": "Classify ticket category"},
            {"name": "RetrieveContext", "description": "Get SAP order context"},
            {"name": "DecideAction", "description": "Determine action based on category"},
            {"name": "ExecuteActions", "description": "Execute Salesforce/SAP actions"}
        ],
        "edges": [
            {"from": "START", "to": "FetchTicket"},
            {"from": "FetchTicket", "to": "CategorizeTicket"},
            {"from": "CategorizeTicket", "to": "RetrieveContext"},
            {"from": "RetrieveContext", "to": "DecideAction"},
            {"from": "DecideAction", "to": "ExecuteActions"},
            {"from": "ExecuteActions", "to": "END"}
        ],
        "categories": ["howto", "billing", "outage", "security", "other"],
        "decision_rules": {
            "howto": "Auto-reply with KB articles",
            "billing": "Request additional information",
            "outage": "Escalate to incident team",
            "security": "Escalate to security team",
            "other": "Request more information"
        }
    }


# ============================================================================
# Demo Data Endpoints
# ============================================================================

@router.get("/demo/leads")
async def get_demo_leads():
    """
    Get available demo leads for testing.
    
    In mock mode, returns predefined test leads.
    """
    salesforce.authenticate()
    leads = salesforce.get_new_leads(limit=10)
    
    return {
        "count": len(leads),
        "leads": [
            {
                "id": lead.get("Id"),
                "name": lead.get("Name"),
                "company": lead.get("Company"),
                "industry": lead.get("Industry"),
                "rating": lead.get("Rating"),
                "source": lead.get("LeadSource")
            }
            for lead in leads
        ]
    }


@router.get("/demo/cases")
async def get_demo_cases():
    """
    Get available demo cases for testing.
    
    In mock mode, returns predefined test cases.
    """
    salesforce.authenticate()
    cases = salesforce.get_new_cases(limit=10)
    
    return {
        "count": len(cases),
        "cases": [
            {
                "id": case.get("Id"),
                "case_number": case.get("CaseNumber"),
                "subject": case.get("Subject"),
                "priority": case.get("Priority"),
                "origin": case.get("Origin"),
                "type": case.get("Type")
            }
            for case in cases
        ]
    }


# ============================================================================
# LLM Prompts Endpoint (for demo)
# ============================================================================

@router.get("/prompts/{prompt_type}")
async def get_prompts(prompt_type: str):
    """
    Get LLM prompts used for scoring/categorization.
    
    Useful for demo to show the AI reasoning prompts.
    
    Args:
        prompt_type: "lead_scoring" or "ticket_categorization"
    """
    from src.tools.llm import get_prompt_for_demo
    
    prompts = get_prompt_for_demo(prompt_type)
    
    if "error" in prompts:
        raise HTTPException(status_code=404, detail=prompts["error"])
    
    return {
        "prompt_type": prompt_type,
        "prompts": prompts
    }


# ============================================================================
# Configuration Status Endpoint
# ============================================================================

@router.get("/status/config")
async def get_config_status():
    """
    Check configuration status for LLM and tracing.
    
    Useful for debugging API key configuration.
    """
    import os
    
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    langsmith_key = os.environ.get("LANGSMITH_API_KEY", "")
    tracing_v2 = os.environ.get("LANGCHAIN_TRACING_V2", "false")
    project = os.environ.get("LANGCHAIN_PROJECT", "default")
    
    return {
        "openai": {
            "configured": bool(openai_key) and not openai_key.startswith("your_"),
            "key_prefix": openai_key[:10] + "..." if openai_key and not openai_key.startswith("your_") else "NOT_SET"
        },
        "langsmith": {
            "configured": bool(langsmith_key) and not langsmith_key.startswith("your_"),
            "key_prefix": langsmith_key[:10] + "..." if langsmith_key and not langsmith_key.startswith("your_") else "NOT_SET",
            "tracing_enabled": tracing_v2.lower() == "true",
            "project": project,
            "dashboard_url": f"https://smith.langchain.com/o/default/projects/p/{project}" if project != "default" else "https://smith.langchain.com"
        },
        "salesforce": {
            "mode": os.environ.get("SALESFORCE_MODE", "mock")
        },
        "sap": {
            "mode": os.environ.get("SAP_MODE", "mock")
        },
        "recommendations": []
    }


@router.get("/test/llm")
async def test_llm_connection():
    """
    Test LLM connection with a simple query.
    
    Returns the model response to verify OpenAI API key is working.
    """
    import os
    
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    
    if not openai_key or openai_key.startswith("your_"):
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY not configured. Please set it in your .env file."
        )
    
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=50)
        response = llm.invoke("Say 'LLM connection successful!' in exactly those words.")
        
        return {
            "status": "success",
            "model": "gpt-4o-mini",
            "response": response.content,
            "tracing_enabled": os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM connection failed: {str(e)}"
        )
