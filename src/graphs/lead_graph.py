"""
Lead Qualification & Routing Graph
LangGraph workflow for qualifying and routing Salesforce leads.

Nodes (in order):
1. FetchLead - Get lead from Salesforce
2. EnrichLead - Enrich with SAP business context
3. ScoreLead - Calculate qualification score (Rule-based or LLM)
4. DecideRouting - Determine owner/priority
5. ExecuteActions - Apply changes to Salesforce/SAP

Supports both deterministic (rule-based) and LLM-powered scoring.
All operations are traced to LangSmith for full observability.
"""

import logging
import os
from typing import Literal

from langgraph.graph import StateGraph, END
from langsmith import traceable

from src.config import get_routing_config
from src.models.state import LeadState, create_initial_lead_state
from src.tools import salesforce, sap, scoring
from src.tools.llm import score_lead_with_llm, ensure_tracing_enabled
from src.tools.email import send_high_value_lead_alert

logger = logging.getLogger(__name__)


# Ensure LangSmith tracing is enabled at module load
ensure_tracing_enabled()


# ============================================================================
# Node Functions
# ============================================================================

def fetch_lead(state: LeadState) -> dict:
    """
    Node 1: Fetch lead data from Salesforce.
    
    If state already has a lead, uses that.
    Otherwise fetches the first new lead.
    """
    logger.info("=== NODE: FetchLead ===")
    
    lead = state.get("lead", {})
    
    if lead and lead.get("Id"):
        # Lead already provided in state
        logger.info(f"Using provided lead: {lead['Id']}")
        return {"actions_done": [f"fetch_lead:existing:{lead['Id']}"]}
    
    # Fetch new leads from Salesforce
    leads = salesforce.get_new_leads(limit=1)
    
    if not leads:
        logger.warning("No new leads found")
        return {
            "lead": {},
            "actions_done": ["fetch_lead:none_found"]
        }
    
    lead = leads[0]
    logger.info(f"Fetched lead: {lead['Id']} - {lead.get('Company', 'Unknown')}")
    
    return {
        "lead": lead,
        "actions_done": [f"fetch_lead:fetched:{lead['Id']}"]
    }


def enrich_lead(state: LeadState) -> dict:
    """
    Node 2: Enrich lead with SAP business context.
    
    Looks up business partner by company name and
    retrieves order history for context.
    """
    logger.info("=== NODE: EnrichLead ===")
    
    lead = state.get("lead", {})
    company = lead.get("Company", "")
    
    if not company:
        logger.warning("No company name for SAP lookup")
        return {
            "enriched": {},
            "actions_done": ["enrich_lead:no_company"]
        }
    
    # Look up SAP business partner
    bp_data = sap.get_business_partner(company)
    
    if not bp_data:
        logger.info(f"No SAP business partner found for: {company}")
        return {
            "enriched": {},
            "actions_done": [f"enrich_lead:bp_not_found:{company}"]
        }
    
    # Get sales order history
    bp_id = bp_data.get("BusinessPartner", "")
    orders = sap.get_sales_orders(bp_id, limit=10) if bp_id else []
    
    # Extract enrichment data
    enriched = sap.extract_enrichment_data(bp_data, orders)
    
    logger.info(f"Enriched with SAP data: BP={bp_id}, Orders={len(orders)}")
    
    return {
        "enriched": enriched,
        "actions_done": [f"enrich_lead:success:bp={bp_id}:orders={len(orders)}"]
    }


def score_lead(state: LeadState) -> dict:
    """
    Node 3: Calculate lead qualification score.
    
    When use_llm=True:
    - Uses GPT-4 for intelligent scoring with reasoning
    - Provides detailed analysis and recommendations
    
    When use_llm=False (default fallback):
    - Uses deterministic rule-based scoring
    - Based on employees, revenue, rating, source, title
    """
    logger.info("=== NODE: ScoreLead ===")
    
    lead = state.get("lead", {})
    enriched = state.get("enriched", {})
    use_llm = state.get("use_llm", False)
    
    if not lead:
        logger.warning("No lead to score")
        return {
            "score": 0.0,
            "llm_analysis": {"reasoning": "No lead data provided"},
            "actions_done": ["score_lead:no_lead"]
        }
    
    if use_llm:
        # LLM-based scoring
        logger.info("🤖 Using LLM for lead scoring...")
        try:
            llm_result = score_lead_with_llm(lead, enriched)
            
            total_score = llm_result["score"]
            llm_analysis = {
                "reasoning": llm_result["reasoning"],
                "confidence": llm_result["confidence"],
                "key_factors": llm_result["key_factors"],
                "recommended_action": llm_result["recommended_action"],
                "model_used": "gpt-4o-mini"
            }
            
            logger.info(f"🤖 LLM Score: {total_score:.4f}")
            logger.info(f"   Confidence: {llm_result['confidence']:.2f}")
            logger.info(f"   Key factors: {', '.join(llm_result['key_factors'][:2])}")
            logger.info(f"   Reasoning: {llm_result['reasoning'][:100]}...")
            
            return {
                "score": total_score,
                "llm_analysis": llm_analysis,
                "actions_done": [f"score_lead:llm:score={total_score:.4f}"]
            }
            
        except Exception as e:
            logger.warning(f"⚠️ LLM scoring failed, falling back to rules: {e}")
            # Fall through to rule-based scoring
    
    # Rule-based scoring (default or fallback)
    logger.info("📊 Using rule-based scoring...")
    score_result = scoring.calculate_lead_score(lead, enriched)
    total_score = score_result["total_score"]
    
    llm_analysis = {
        "reasoning": f"Rule-based scoring. Base: {score_result['base_score']:.2f}, SAP bonus: {score_result['sap_bonus']:.2f}",
        "confidence": 1.0,  # Rules are deterministic
        "key_factors": list(score_result["components"].keys())[:3],
        "recommended_action": "Follow standard lead handling process",
        "model_used": "rule-based"
    }
    
    logger.info(f"📊 Rule Score: {total_score:.4f}")
    logger.info(f"   Base score: {score_result['base_score']:.4f}")
    logger.info(f"   SAP bonus: {score_result['sap_bonus']:.4f}")
    
    return {
        "score": total_score,
        "llm_analysis": llm_analysis,
        "actions_done": [f"score_lead:rules:score={total_score:.4f}"]
    }


def decide_routing(state: LeadState) -> dict:
    """
    Node 4: Determine lead routing based on score.
    
    Deterministic routing:
    - Score >= 0.75: Account Executive (P1)
    - Score 0.45-0.74: Sales Dev Rep (P2)  
    - Score < 0.45: Nurture Campaign (P3)
    
    When LLM was used, includes AI reasoning in the decision.
    """
    logger.info("=== NODE: DecideRouting ===")
    
    score = state.get("score", 0.0)
    llm_analysis = state.get("llm_analysis", {})
    routing_config = get_routing_config()
    
    # Get routing decision
    routing = scoring.determine_routing(score)
    
    # Map owner type to actual owner ID
    owner_type = routing["owner_type"]
    if owner_type == "AE":
        owner_id = routing_config.ae_owner_id
    elif owner_type == "SDR":
        owner_id = routing_config.sdr_owner_id
    else:
        owner_id = routing_config.nurture_owner_id
    
    # Enhance reason with LLM analysis if available
    reason = routing["reason"]
    if llm_analysis.get("reasoning") and llm_analysis.get("model_used") != "rule-based":
        reason = f"{reason}\n\n🤖 AI Analysis: {llm_analysis['reasoning']}"
        if llm_analysis.get("recommended_action"):
            reason += f"\n\n📋 Recommended: {llm_analysis['recommended_action']}"
    
    route = {
        "owner_id": owner_id,
        "owner_type": owner_type,
        "priority": routing["priority"],
        "reason": reason
    }
    
    logger.info(f"Routing decision: {owner_type} / {routing['priority']}")
    logger.info(f"  Owner ID: {owner_id}")
    logger.info(f"  Reason: {routing['reason'][:80]}...")
    
    return {
        "route": route,
        "actions_done": [f"decide_routing:{owner_type}:{routing['priority']}"]
    }


def execute_actions(state: LeadState) -> dict:
    """
    Node 5: Execute actions on Salesforce and SAP.
    
    Actions:
    - Assign lead to new owner
    - Update lead status
    - Create follow-up task
    - (Optional) Create SAP note
    """
    logger.info("=== NODE: ExecuteActions ===")
    
    lead = state.get("lead", {})
    route = state.get("route", {})
    enriched = state.get("enriched", {})
    score = state.get("score", 0.0)
    
    if not lead or not lead.get("Id"):
        logger.warning("No lead to process")
        return {"actions_done": ["execute_actions:no_lead"]}
    
    lead_id = lead["Id"]
    actions_executed = []
    
    # 1. Assign owner
    owner_id = route.get("owner_id", "")
    if owner_id:
        result = salesforce.assign_owner(lead_id, owner_id, "Lead")
        actions_executed.append(f"sf:assign_owner:{owner_id}")
        logger.info(f"Assigned lead to owner: {owner_id}")
    
    # 2. Update status based on routing
    owner_type = route.get("owner_type", "")
    if owner_type == "AE":
        new_status = "Working - Contacted"
    elif owner_type == "SDR":
        new_status = "Open - Not Contacted"
    else:
        new_status = "Nurturing"
    
    result = salesforce.update_lead_status(lead_id, new_status)
    actions_executed.append(f"sf:update_status:{new_status}")
    logger.info(f"Updated lead status: {new_status}")
    
    # 3. Create follow-up task
    priority = route.get("priority", "P3")
    task_subject = f"[{priority}] Follow up with {lead.get('Name', 'Lead')}"
    task_description = (
        f"Lead Qualification Summary:\n"
        f"- Score: {score:.2f}\n"
        f"- Company: {lead.get('Company', 'N/A')}\n"
        f"- Industry: {lead.get('Industry', 'N/A')}\n"
        f"- Routing: {owner_type} ({route.get('reason', '')})\n"
    )
    
    if enriched:
        task_description += (
            f"\nSAP Context:\n"
            f"- Business Partner: {enriched.get('business_partner_id', 'N/A')}\n"
            f"- Total Orders: {enriched.get('total_orders', 0)}\n"
            f"- Total Revenue: ${enriched.get('total_revenue', 0):,.2f}\n"
            f"- Credit Rating: {enriched.get('credit_rating', 'N/A')}\n"
        )
    
    result = salesforce.create_task(lead_id, task_description, task_subject)
    actions_executed.append(f"sf:create_task:{result.get('id', 'unknown')}")
    logger.info(f"Created follow-up task: {task_subject}")
    
    # 4. Create SAP note if business partner exists
    bp_id = enriched.get("business_partner_id", "")
    if bp_id:
        note_text = (
            f"Salesforce Lead Qualified\n"
            f"Lead ID: {lead_id}\n"
            f"Score: {score:.2f}\n"
            f"Routing: {owner_type} / {priority}\n"
            f"Company: {lead.get('Company', 'N/A')}"
        )
        result = sap.create_note(bp_id, note_text, "GENERAL")
        actions_executed.append(f"sap:create_note:{bp_id}")
        logger.info(f"Created SAP note on BP: {bp_id}")
    
    # 5. Send email alert for high-value leads (score >= 60%)
    if score >= 0.60:
        logger.info(f"📧 High-value lead detected (score: {score:.0%}) - Sending email alert...")
        llm_analysis = state.get("llm_analysis", {})
        reasoning = llm_analysis.get("reasoning", f"Lead scored {score:.0%}")
        
        email_result = send_high_value_lead_alert(
            lead=lead,
            score=score,
            reasoning=reasoning,
            routing=route
        )
        
        if email_result.get("success"):
            actions_executed.append(f"email:lead_alert:{email_result.get('to', 'unknown')}")
            logger.info(f"📧 Email alert sent successfully!")
        else:
            logger.warning(f"⚠️ Failed to send email alert: {email_result.get('error', 'Unknown error')}")
            actions_executed.append(f"email:lead_alert:failed")
    
    logger.info(f"Executed {len(actions_executed)} actions")
    
    return {
        "actions_done": actions_executed
    }


# ============================================================================
# Graph Construction
# ============================================================================

def build_lead_graph():
    """
    Build the Lead Qualification & Routing graph.
    
    Flow:
    FetchLead -> EnrichLead -> ScoreLead -> DecideRouting -> ExecuteActions -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building Lead Qualification Graph")
    
    # Create graph with state schema
    graph = StateGraph(LeadState)
    
    # Add nodes
    graph.add_node("FetchLead", fetch_lead)
    graph.add_node("EnrichLead", enrich_lead)
    graph.add_node("ScoreLead", score_lead)
    graph.add_node("DecideRouting", decide_routing)
    graph.add_node("ExecuteActions", execute_actions)
    
    # Define edges (linear flow)
    graph.set_entry_point("FetchLead")
    graph.add_edge("FetchLead", "EnrichLead")
    graph.add_edge("EnrichLead", "ScoreLead")
    graph.add_edge("ScoreLead", "DecideRouting")
    graph.add_edge("DecideRouting", "ExecuteActions")
    graph.add_edge("ExecuteActions", END)
    
    # Compile graph with name for LangSmith tracing
    compiled = graph.compile()
    
    logger.info("Lead Qualification Graph compiled successfully")
    return compiled


@traceable(
    name="Lead Qualification Workflow",
    run_type="chain",
    tags=["lead-qualification", "langgraph", "salesforce", "sap"]
)
def run_lead_qualification(lead: dict = None, use_llm: bool = True) -> LeadState:
    """
    Run the lead qualification workflow with full LangSmith tracing.
    
    This is the main entry point for lead qualification, decorated with
    @traceable to ensure all operations are logged to LangSmith.
    
    Args:
        lead: Optional lead data. If None, fetches newest lead.
        use_llm: Whether to use LLM for scoring (default: True)
        
    Returns:
        Final state with all actions executed
    """
    # Verify tracing is active
    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key_set = bool(os.environ.get("LANGSMITH_API_KEY"))
    
    logger.info("=" * 60)
    logger.info("🚀 STARTING LEAD QUALIFICATION WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"   Mode: {'🤖 LLM-Powered' if use_llm else '📊 Rule-Based'}")
    logger.info(f"   LangSmith Tracing: {'✅ ENABLED' if tracing_enabled and api_key_set else '❌ DISABLED'}")
    logger.info(f"   Project: {os.environ.get('LANGCHAIN_PROJECT', 'not set')}")
    logger.info("=" * 60)
    
    # Initialize Salesforce authentication
    salesforce.authenticate()
    
    # Build and run graph
    graph = build_lead_graph()
    
    # Create initial state with LLM flag
    initial_state = create_initial_lead_state(lead or {}, use_llm=use_llm)
    
    # Determine lead info for run name
    lead_company = lead.get("Company", "Auto") if lead else "Auto"
    lead_id = lead.get("Id", "auto") if lead else "auto"
    
    # Execute graph with run config for LangSmith tracing
    config = {
        "run_name": f"🎯 Lead: {lead_company} ({'LLM' if use_llm else 'Rules'})",
        "tags": ["lead-qualification", f"mode:{'llm' if use_llm else 'rules'}"],
        "metadata": {
            "workflow": "lead_qualification",
            "use_llm": use_llm,
            "lead_id": lead_id,
            "lead_company": lead_company,
        }
    }
    
    logger.info("📊 Executing LangGraph workflow...")
    final_state = graph.invoke(initial_state, config=config)
    
    # Log completion with detailed results
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ LEAD QUALIFICATION WORKFLOW COMPLETE")
    logger.info("=" * 60)
    logger.info(f"   FINAL SCORE: {final_state.get('score', 0):.2f}")
    logger.info(f"   ROUTING: {final_state.get('route', {}).get('owner_type', 'N/A')} / {final_state.get('route', {}).get('priority', 'N/A')}")
    
    # Show LLM reasoning prominently (this is what the user wants to see!)
    llm_analysis = final_state.get("llm_analysis", {})
    if llm_analysis.get("reasoning"):
        logger.info("")
        logger.info("=" * 60)
        logger.info("🤖 AI REASONING (Displayed to Sales Team):")
        logger.info("=" * 60)
        logger.info("")
        # Print reasoning with nice formatting
        reasoning_lines = llm_analysis['reasoning'].split('\n')
        for line in reasoning_lines:
            logger.info(f"   {line}")
        logger.info("")
        logger.info("-" * 60)
        
        if llm_analysis.get("key_factors"):
            logger.info("🔑 KEY FACTORS:")
            for i, factor in enumerate(llm_analysis['key_factors'], 1):
                logger.info(f"   {i}. {factor}")
        
        if llm_analysis.get("recommended_action"):
            logger.info("")
            logger.info(f"💡 RECOMMENDED ACTION: {llm_analysis['recommended_action']}")
        
        logger.info(f"🎯 AI CONFIDENCE: {llm_analysis.get('confidence', 0):.0%}")
    else:
        logger.info("")
        logger.info("📊 Rule-based scoring (no LLM reasoning)")
    
    logger.info("")
    logger.info(f"📋 Total Actions Executed: {len(final_state.get('actions_done', []))}")
    logger.info("=" * 60)
    
    return final_state
