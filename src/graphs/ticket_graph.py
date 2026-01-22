"""
Customer Support Ticket Triage Graph
LangGraph workflow for triaging and routing support tickets.

Nodes (in order):
1. FetchTicket - Get case from Salesforce
2. CategorizeTicket - Classify ticket category (Rule-based or LLM)
3. RetrieveContext - Get SAP order context
4. DecideAction - Determine action based on category
5. ExecuteActions - Apply changes to Salesforce/SAP

Supports both deterministic (rule-based) and LLM-powered categorization.
"""

import logging
import re
from typing import Literal

from langgraph.graph import StateGraph, END

from src.config import get_routing_config
from src.models.state import TicketState, create_initial_ticket_state, TicketCategory, TicketAction
from src.tools import salesforce, sap, kb
from src.tools.llm import categorize_ticket_with_llm

logger = logging.getLogger(__name__)


# ============================================================================
# Node Functions
# ============================================================================

def fetch_ticket(state: TicketState) -> dict:
    """
    Node 1: Fetch case/ticket from Salesforce.
    
    If state already has a case, uses that.
    Otherwise fetches the first new case.
    """
    logger.info("=== NODE: FetchTicket ===")
    
    case = state.get("case", {})
    
    if case and case.get("Id"):
        # Case already provided in state
        logger.info(f"Using provided case: {case['Id']}")
        return {"actions_done": [f"fetch_ticket:existing:{case['Id']}"]}
    
    # Fetch new cases from Salesforce
    cases = salesforce.get_new_cases(limit=1)
    
    if not cases:
        logger.warning("No new cases found")
        return {
            "case": {},
            "actions_done": ["fetch_ticket:none_found"]
        }
    
    case = cases[0]
    logger.info(f"Fetched case: {case['Id']} - {case.get('Subject', 'No Subject')[:50]}")
    
    return {
        "case": case,
        "actions_done": [f"fetch_ticket:fetched:{case['Id']}"]
    }


def categorize_ticket(state: TicketState) -> dict:
    """
    Node 2: Categorize ticket based on content.
    
    When use_llm=True:
    - Uses GPT-4 for intelligent categorization
    - Detects sentiment and urgency
    - Generates draft response
    
    When use_llm=False:
    - Uses rule-based pattern matching
    
    Categories:
    - howto: How-to questions
    - billing: Billing/payment issues
    - outage: System outages
    - security: Security concerns
    - other: Everything else
    """
    logger.info("=== NODE: CategorizeTicket ===")
    
    case = state.get("case", {})
    use_llm = state.get("use_llm", False)
    subject = case.get("Subject", "")
    description = case.get("Description", "")
    
    if not subject and not description:
        logger.warning("No content to categorize")
        return {
            "category": TicketCategory.OTHER,
            "llm_analysis": {"reasoning": "No content provided"},
            "actions_done": ["categorize_ticket:no_content"]
        }
    
    # We need SAP context for LLM, but it comes later in the pipeline
    # For now, pass empty context - the LLM will still work
    sap_context = state.get("sap_context", {})
    
    if use_llm:
        logger.info("🤖 Using LLM for ticket categorization...")
        try:
            llm_result = categorize_ticket_with_llm(case, sap_context)
            
            category = llm_result["category"]
            llm_analysis = {
                "reasoning": llm_result["reasoning"],
                "confidence": llm_result["confidence"],
                "urgency": llm_result["urgency"],
                "sentiment": llm_result["sentiment"],
                "suggested_response": llm_result["suggested_response"],
                "requires_escalation": llm_result["requires_escalation"],
                "model_used": "gpt-4o-mini"
            }
            
            logger.info(f"🤖 LLM Category: {category}")
            logger.info(f"   Urgency: {llm_result['urgency']}")
            logger.info(f"   Sentiment: {llm_result['sentiment']}")
            logger.info(f"   Confidence: {llm_result['confidence']:.2f}")
            logger.info(f"   Requires escalation: {llm_result['requires_escalation']}")
            
            return {
                "category": category,
                "llm_analysis": llm_analysis,
                "actions_done": [f"categorize_ticket:llm:{category}:{llm_result['confidence']:.2f}"]
            }
            
        except Exception as e:
            logger.warning(f"⚠️ LLM categorization failed, falling back to rules: {e}")
            # Fall through to rule-based
    
    # Rule-based categorization (default or fallback)
    logger.info("📊 Using rule-based categorization...")
    result = kb.categorize_ticket(subject, description)
    category = result["category"]
    confidence = result["confidence"]
    
    llm_analysis = {
        "reasoning": f"Rule-based categorization. Matched patterns: {result.get('matched_patterns', [])[:2]}",
        "confidence": confidence,
        "urgency": "high" if result.get("requires_escalation") else "medium",
        "sentiment": "neutral",
        "suggested_response": "",
        "requires_escalation": result.get("requires_escalation", False),
        "model_used": "rule-based"
    }
    
    logger.info(f"📊 Rule Category: {category} (confidence: {confidence:.2f})")
    if result.get("matched_patterns"):
        logger.info(f"   Matched patterns: {result['matched_patterns'][:3]}")
    
    return {
        "category": category,
        "llm_analysis": llm_analysis,
        "actions_done": [f"categorize_ticket:rules:{category}:{confidence:.2f}"]
    }


def retrieve_context(state: TicketState) -> dict:
    """
    Node 3: Retrieve SAP order context for the ticket.
    
    Looks up related orders and service history.
    """
    logger.info("=== NODE: RetrieveContext ===")
    
    case = state.get("case", {})
    account_id = case.get("AccountId", "")
    description = case.get("Description", "")
    
    # Try to extract order reference from description
    # Look for patterns like "Order #SAP-2024-1234" or "SO1234567"
    import re
    order_refs = re.findall(r'(?:order|so|sap)[#\s\-]*(\w+)', description.lower())
    
    sales_orders = []
    service_orders = []
    
    # If we have an account, look up SAP context
    if account_id:
        # Use account ID as reference for SAP lookup
        # In real implementation, would map SF Account to SAP BP
        sales_orders = sap.get_sales_orders(account_id, limit=5)
        service_orders = sap.get_service_orders(account_id, limit=3)
        logger.info(f"Retrieved SAP context for account {account_id}")
    elif order_refs:
        # Try to look up by order reference
        ref = order_refs[0]
        service_orders = sap.get_service_orders(ref, limit=3)
        logger.info(f"Retrieved SAP context for order ref: {ref}")
    else:
        logger.info("No account or order reference for SAP lookup")
    
    # Extract context
    sap_context = sap.extract_order_context(sales_orders, service_orders)
    
    logger.info(f"SAP Context: {len(sales_orders)} sales orders, {len(service_orders)} service orders")
    
    return {
        "sap_context": sap_context,
        "actions_done": [f"retrieve_context:sales={len(sales_orders)}:service={len(service_orders)}"]
    }


def decide_action(state: TicketState) -> dict:
    """
    Node 4: Decide action based on category and context.
    
    When LLM was used for categorization:
    - Uses LLM-generated response as template
    - Considers sentiment and urgency from LLM
    
    Decision logic:
    - howto: Auto-reply with KB articles
    - billing: Request more information
    - outage: Escalate to incident team
    - security: Escalate to security team
    - other: Request information
    """
    logger.info("=== NODE: DecideAction ===")
    
    case = state.get("case", {})
    category = state.get("category", TicketCategory.OTHER)
    sap_context = state.get("sap_context", {})
    llm_analysis = state.get("llm_analysis", {})
    use_llm = state.get("use_llm", False)
    
    # Search knowledge base for relevant articles
    subject = case.get("Subject", "")
    description = case.get("Description", "")
    query = f"{subject} {description}"
    
    kb_suggestions = kb.search_knowledge_base(query, category=category, limit=3)
    
    # Determine action (rule-based logic)
    decision = kb.determine_ticket_action(category, kb_suggestions)
    
    # Override with LLM analysis if available
    if use_llm and llm_analysis.get("model_used") != "rule-based":
        # Use LLM-generated response if available
        if llm_analysis.get("suggested_response"):
            decision["response_template"] = llm_analysis["suggested_response"]
            logger.info("🤖 Using LLM-generated response")
        
        # Check if LLM flagged for escalation
        if llm_analysis.get("requires_escalation") and decision["action"] != "escalate":
            decision["action"] = "escalate"
            decision["escalation_reason"] = llm_analysis.get("escalation_reason", 
                f"LLM flagged for escalation: {llm_analysis.get('reasoning', '')[:100]}")
            logger.info("🤖 LLM overrode to escalation")
        
        # Adjust priority based on urgency
        urgency = llm_analysis.get("urgency", "medium")
        if urgency == "critical":
            decision["priority_change"] = "Critical"
        elif urgency == "high" and not decision.get("priority_change"):
            decision["priority_change"] = "High"
    
    # Add SAP context to decision if relevant
    if category == "billing" and sap_context.get("has_open_orders"):
        decision["escalation_reason"] = (
            f"{decision.get('escalation_reason', '')} "
            f"Note: Customer has {len(sap_context.get('sales_orders', []))} open orders in SAP."
        ).strip()
    
    logger.info(f"Decision: {decision['action']}")
    if decision.get("priority_change"):
        logger.info(f"  Priority change: {decision['priority_change']}")
    if kb_suggestions:
        logger.info(f"  KB suggestions: {len(kb_suggestions)} articles")
    if llm_analysis.get("sentiment"):
        logger.info(f"  Customer sentiment: {llm_analysis['sentiment']}")
    
    return {
        "kb_suggestions": kb_suggestions,
        "decision": decision,
        "actions_done": [f"decide_action:{decision['action']}"]
    }


def execute_actions(state: TicketState) -> dict:
    """
    Node 5: Execute actions on Salesforce and SAP.
    
    Actions based on decision:
    - Post case comment (auto-reply or info request)
    - Update case status
    - Change case owner (escalation)
    - Change priority
    - Create SAP note
    """
    logger.info("=== NODE: ExecuteActions ===")
    
    case = state.get("case", {})
    category = state.get("category", "")
    decision = state.get("decision", {})
    sap_context = state.get("sap_context", {})
    
    if not case or not case.get("Id"):
        logger.warning("No case to process")
        return {"actions_done": ["execute_actions:no_case"]}
    
    case_id = case["Id"]
    action = decision.get("action", "")
    actions_executed = []
    routing_config = get_routing_config()
    
    # 1. Post comment/response
    response_text = decision.get("response_template", "")
    if response_text:
        comment_result = salesforce.post_case_comment(case_id, response_text)
        actions_executed.append(f"sf:post_comment:{comment_result.get('id', 'unknown')}")
        logger.info("Posted case comment")
    
    # 2. Update case fields based on action
    update_fields = {}
    
    if action == TicketAction.AUTO_REPLY:
        update_fields["Status"] = "Waiting on Customer"
        
    elif action == TicketAction.REQUEST_INFO:
        update_fields["Status"] = "Waiting on Customer"
        
    elif action == TicketAction.ESCALATE:
        update_fields["Status"] = "Escalated"
        update_fields["IsEscalated"] = True
        update_fields["OwnerId"] = routing_config.escalation_owner_id
        
        if decision.get("priority_change"):
            update_fields["Priority"] = decision["priority_change"]
        
        actions_executed.append(f"sf:escalate:{routing_config.escalation_owner_id}")
        logger.info(f"Escalated to: {routing_config.escalation_owner_id}")
    
    # Apply updates
    if update_fields:
        salesforce.update_case(case_id, update_fields)
        actions_executed.append(f"sf:update_case:{list(update_fields.keys())}")
        logger.info(f"Updated case fields: {list(update_fields.keys())}")
    
    # 3. Create SAP note if relevant context exists
    bp_id = sap_context.get("business_partner_id", "")
    if bp_id and category in ("billing", "outage"):
        note_text = (
            f"Salesforce Case: {case.get('CaseNumber', case_id)}\n"
            f"Category: {category.upper()}\n"
            f"Subject: {case.get('Subject', 'N/A')}\n"
            f"Action: {action}\n"
            f"Status: {update_fields.get('Status', 'Updated')}"
        )
        sap.create_note(bp_id, note_text, "GENERAL")
        actions_executed.append(f"sap:create_note:{bp_id}")
        logger.info(f"Created SAP note on BP: {bp_id}")
    
    logger.info(f"Executed {len(actions_executed)} actions")
    
    return {
        "actions_done": actions_executed
    }


# ============================================================================
# Graph Construction
# ============================================================================

def build_ticket_graph() -> StateGraph:
    """
    Build the Customer Support Ticket Triage graph.
    
    Flow:
    FetchTicket -> CategorizeTicket -> RetrieveContext -> DecideAction -> ExecuteActions -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building Ticket Triage Graph")
    
    # Create graph with state schema
    graph = StateGraph(TicketState)
    
    # Add nodes
    graph.add_node("FetchTicket", fetch_ticket)
    graph.add_node("CategorizeTicket", categorize_ticket)
    graph.add_node("RetrieveContext", retrieve_context)
    graph.add_node("DecideAction", decide_action)
    graph.add_node("ExecuteActions", execute_actions)
    
    # Define edges (linear flow)
    graph.set_entry_point("FetchTicket")
    graph.add_edge("FetchTicket", "CategorizeTicket")
    graph.add_edge("CategorizeTicket", "RetrieveContext")
    graph.add_edge("RetrieveContext", "DecideAction")
    graph.add_edge("DecideAction", "ExecuteActions")
    graph.add_edge("ExecuteActions", END)
    
    # Compile graph
    compiled = graph.compile()
    
    logger.info("Ticket Triage Graph compiled successfully")
    return compiled


def run_ticket_triage(case: dict = None, use_llm: bool = True) -> TicketState:
    """
    Run the ticket triage workflow.
    
    Args:
        case: Optional case data. If None, fetches newest case.
        use_llm: Whether to use LLM for categorization (default: True)
        
    Returns:
        Final state with all actions executed
    """
    logger.info("=" * 60)
    logger.info("STARTING TICKET TRIAGE WORKFLOW")
    logger.info(f"Mode: {'🤖 LLM-Powered' if use_llm else '📊 Rule-Based'}")
    logger.info("=" * 60)
    
    # Initialize Salesforce authentication
    salesforce.authenticate()
    
    # Build and run graph
    graph = build_ticket_graph()
    
    # Create initial state with LLM flag
    initial_state = create_initial_ticket_state(case or {}, use_llm=use_llm)
    
    # Execute graph with run config for LangSmith tracing
    config = {
        "run_name": f"Ticket Triage ({'LLM' if use_llm else 'Rules'})",
        "metadata": {
            "workflow": "ticket_triage",
            "use_llm": use_llm,
            "case_id": case.get("Id") if case else "auto"
        }
    }
    final_state = graph.invoke(initial_state, config=config)
    
    logger.info("=" * 60)
    logger.info("TICKET TRIAGE WORKFLOW COMPLETE")
    logger.info(f"Category: {final_state.get('category', 'N/A')}")
    logger.info(f"Action: {final_state.get('decision', {}).get('action', 'N/A')}")
    
    # Show LLM reasoning prominently
    llm_analysis = final_state.get("llm_analysis", {})
    if llm_analysis.get("reasoning"):
        logger.info("-" * 60)
        logger.info("🤖 AI REASONING:")
        logger.info(f"   {llm_analysis['reasoning']}")
        logger.info("-" * 60)
        logger.info(f"😊 Sentiment: {llm_analysis.get('sentiment', 'N/A')}")
        logger.info(f"⚡ Urgency: {llm_analysis.get('urgency', 'N/A')}")
        logger.info(f"🎯 Confidence: {llm_analysis.get('confidence', 0):.0%}")
        if llm_analysis.get("suggested_response"):
            logger.info("-" * 60)
            logger.info("📝 SUGGESTED RESPONSE:")
            logger.info(f"   {llm_analysis['suggested_response'][:200]}...")
    
    logger.info(f"Actions Executed: {len(final_state.get('actions_done', []))}")
    logger.info("=" * 60)
    
    return final_state
