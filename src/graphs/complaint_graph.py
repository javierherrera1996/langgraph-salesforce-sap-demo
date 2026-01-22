"""
Product Complaint & IT Support Classification Graph

LangGraph workflow for classifying customer complaints:
- Product complaints → Email to product owner
- IT Support requests → Redirect to IT portal

Nodes (in order):
1. FetchTicket - Get case from Salesforce
2. ClassifyComplaint - LLM classifies Product vs IT vs Other
3. DecideAction - Determine action based on classification
4. ExecuteActions - Send email or redirect

Author: Belden AI Team
"""

import logging
import os
from typing import Literal, TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langsmith import traceable

from src.config import get_routing_config
from src.tools import salesforce
from src.tools.llm import classify_product_complaint_with_llm, ensure_tracing_enabled
from src.tools.email import (
    send_product_complaint_alert,
    send_ticket_analysis_email,
    get_it_support_redirect,
    NOTIFICATION_EMAIL
)

logger = logging.getLogger(__name__)

# Ensure LangSmith tracing is enabled
ensure_tracing_enabled()


# ============================================================================
# State Schema
# ============================================================================

class ProductClassification(TypedDict, total=False):
    """LLM classification results."""
    is_product_complaint: bool
    is_it_support: bool
    product_category: str
    product_name: str
    confidence: float
    reasoning: str
    sentiment: str
    urgency: str
    complaint_summary: str
    suggested_response: str


class ComplaintDecision(TypedDict, total=False):
    """Decision for complaint handling."""
    action: str  # "email_product_owner", "redirect_it", "escalate", "other"
    recipient_email: str
    email_sent: bool
    redirect_url: str
    message: str


class ComplaintState(TypedDict):
    """State schema for Product Complaint Classification graph."""
    case: dict
    classification: ProductClassification
    decision: ComplaintDecision
    use_llm: bool
    actions_done: Annotated[list[str], add]


def create_initial_complaint_state(case: dict, use_llm: bool = True) -> ComplaintState:
    """Create initial state for the complaint classification graph."""
    return ComplaintState(
        case=case,
        classification={
            "is_product_complaint": False,
            "is_it_support": False,
            "product_category": "none",
            "product_name": "",
            "confidence": 0.0,
            "reasoning": "",
            "sentiment": "neutral",
            "urgency": "medium",
            "complaint_summary": "",
            "suggested_response": ""
        },
        decision={
            "action": "",
            "recipient_email": "",
            "email_sent": False,
            "redirect_url": "",
            "message": ""
        },
        use_llm=use_llm,
        actions_done=[]
    )


# ============================================================================
# Node Functions
# ============================================================================

def fetch_ticket(state: ComplaintState) -> dict:
    """
    Node 1: Fetch case/ticket from Salesforce.
    """
    logger.info("=== NODE: FetchTicket (Complaint) ===")
    
    case = state.get("case", {})
    
    if case and case.get("Id"):
        logger.info(f"Using provided case: {case['Id']}")
        return {"actions_done": [f"fetch_ticket:existing:{case['Id']}"]}
    
    # Fetch new cases
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


def classify_complaint(state: ComplaintState) -> dict:
    """
    Node 2: Classify if complaint is Product-related or IT Support.
    
    Uses LLM to analyze:
    - Is it a product complaint? (switches, cables, connectors, etc.)
    - Is it an IT support request? (portal access, passwords, etc.)
    - What specific product is mentioned?
    - Customer sentiment and urgency
    """
    logger.info("=== NODE: ClassifyComplaint ===")
    
    case = state.get("case", {})
    use_llm = state.get("use_llm", True)
    
    subject = case.get("Subject", "")
    description = case.get("Description", "")
    
    if not subject and not description:
        logger.warning("No content to classify")
        return {
            "classification": {
                "is_product_complaint": False,
                "is_it_support": False,
                "product_category": "none",
                "reasoning": "No content provided"
            },
            "actions_done": ["classify_complaint:no_content"]
        }
    
    if use_llm:
        logger.info("🤖 Using LLM for complaint classification...")
        try:
            llm_result = classify_product_complaint_with_llm(case)
            
            classification = {
                "is_product_complaint": llm_result.get("is_product_complaint", False),
                "is_it_support": llm_result.get("is_it_support", False),
                "product_category": llm_result.get("product_category", "none"),
                "product_name": llm_result.get("product_name", ""),
                "confidence": llm_result.get("confidence", 0.7),
                "reasoning": llm_result.get("reasoning", ""),
                "sentiment": llm_result.get("sentiment", "neutral"),
                "urgency": llm_result.get("urgency", "medium"),
                "complaint_summary": llm_result.get("complaint_summary", subject),
                "suggested_response": llm_result.get("suggested_response", "")
            }
            
            # Log classification result
            if classification["is_product_complaint"]:
                logger.info(f"📦 PRODUCT COMPLAINT: {classification['product_category']}")
                logger.info(f"   Product: {classification['product_name'] or 'General'}")
            elif classification["is_it_support"]:
                logger.info(f"💻 IT SUPPORT REQUEST detected")
            else:
                logger.info(f"❓ OTHER/GENERAL inquiry")
            
            logger.info(f"   Sentiment: {classification['sentiment']}")
            logger.info(f"   Urgency: {classification['urgency']}")
            logger.info(f"   Confidence: {classification['confidence']:.0%}")
            
            return {
                "classification": classification,
                "actions_done": [f"classify_complaint:llm:{classification['product_category']}:{classification['confidence']:.2f}"]
            }
            
        except Exception as e:
            logger.warning(f"⚠️ LLM classification failed: {e}")
            # Fall through to rule-based
    
    # Rule-based classification (fallback)
    logger.info("📊 Using rule-based classification...")
    
    content = f"{subject} {description}".lower()
    
    # Product keywords
    product_keywords = {
        "switches": ["switch", "hirschmann", "ethernet switch", "industrial switch"],
        "cables": ["cable", "wire", "fiber", "cabling", "conductor"],
        "connectors": ["connector", "terminal", "plug", "socket", "patch"],
        "software": ["software", "firmware", "app", "application", "update"],
        "infrastructure": ["rack", "cabinet", "enclosure", "infrastructure"]
    }
    
    # IT Support keywords
    it_keywords = ["password", "login", "portal", "access", "account", "vpn", "email", "computer"]
    
    is_product = False
    product_category = "none"
    
    for category, keywords in product_keywords.items():
        if any(kw in content for kw in keywords):
            is_product = True
            product_category = category
            break
    
    is_it = any(kw in content for kw in it_keywords) and not is_product
    
    classification = {
        "is_product_complaint": is_product,
        "is_it_support": is_it,
        "product_category": product_category if is_product else "none",
        "product_name": "",
        "confidence": 0.6,
        "reasoning": f"Rule-based classification based on keyword matching",
        "sentiment": "neutral",
        "urgency": "medium",
        "complaint_summary": subject,
        "suggested_response": ""
    }
    
    return {
        "classification": classification,
        "actions_done": [f"classify_complaint:rules:{product_category}"]
    }


def decide_action(state: ComplaintState) -> dict:
    """
    Node 3: Decide action based on classification.
    
    - Product complaint → Send email to product owner
    - IT Support → Redirect to IT portal
    - Other → General handling
    """
    logger.info("=== NODE: DecideAction (Complaint) ===")
    
    classification = state.get("classification", {})
    
    is_product = classification.get("is_product_complaint", False)
    is_it = classification.get("is_it_support", False)
    product_category = classification.get("product_category", "none")
    
    decision = {
        "action": "other",
        "recipient_email": "",
        "email_sent": False,
        "redirect_url": "",
        "message": ""
    }
    
    if is_product:
        # Product complaint → Email to product owner
        decision["action"] = "email_product_owner"
        decision["recipient_email"] = NOTIFICATION_EMAIL  # In production, map to actual product owner
        decision["message"] = f"Queja de producto ({product_category}) detectada. Se enviará email al encargado."
        logger.info(f"📧 Action: Send email to product owner for {product_category}")
        
    elif is_it:
        # IT Support → Redirect to portal
        it_info = get_it_support_redirect()
        decision["action"] = "redirect_it"
        decision["redirect_url"] = it_info["url"]
        decision["message"] = it_info["message"]
        logger.info(f"🔗 Action: Redirect to IT Support portal")
        
    else:
        # Other → General handling
        decision["action"] = "general_handling"
        decision["message"] = "Ticket clasificado como consulta general."
        logger.info(f"📋 Action: General handling")
    
    return {
        "decision": decision,
        "actions_done": [f"decide_action:{decision['action']}"]
    }


def execute_actions(state: ComplaintState) -> dict:
    """
    Node 4: Execute the decided action.
    
    ALWAYS sends email with AI analysis (for ALL ticket types).
    Also:
    - Update Salesforce case with comment
    - Record redirect for IT support
    """
    logger.info("=== NODE: ExecuteActions (Complaint) ===")
    
    case = state.get("case", {})
    classification = state.get("classification", {})
    decision = state.get("decision", {})
    
    if not case or not case.get("Id"):
        logger.warning("No case to process")
        return {"actions_done": ["execute_actions:no_case"]}
    
    case_id = case["Id"]
    action = decision.get("action", "")
    actions_executed = []
    email_sent = False
    
    # ========================================================================
    # 1. ALWAYS SEND EMAIL WITH AI ANALYSIS (for all ticket types)
    # ========================================================================
    logger.info("📧 Sending AI analysis email...")
    
    email_result = send_ticket_analysis_email(
        ticket=case,
        classification=classification,
        recipient_email=NOTIFICATION_EMAIL
    )
    
    if email_result.get("success") or email_result.get("id"):
        email_sent = True
        actions_executed.append(f"email:ai_analysis:{NOTIFICATION_EMAIL}")
        logger.info(f"✅ AI analysis email sent successfully!")
    else:
        actions_executed.append("email:ai_analysis:failed")
        logger.warning(f"⚠️ Failed to send email: {email_result.get('error')}")
    
    # ========================================================================
    # 2. UPDATE SALESFORCE CASE WITH AI COMMENT
    # ========================================================================
    
    # Determine type label
    if classification.get("is_product_complaint"):
        type_emoji = "📦"
        type_label = "PRODUCT COMPLAINT"
        type_detail = f"Category: {classification.get('product_category', 'N/A').upper()}\n🏷️ Product: {classification.get('product_name') or 'Not specified'}"
    elif classification.get("is_it_support"):
        type_emoji = "💻"
        type_label = "IT SUPPORT REQUEST"
        redirect_url = decision.get("redirect_url", "")
        type_detail = f"Redirect URL: {redirect_url}"
        actions_executed.append(f"redirect:it_portal:{redirect_url}")
        logger.info(f"🔗 IT redirect recorded: {redirect_url}")
    else:
        type_emoji = "📋"
        type_label = "GENERAL INQUIRY"
        type_detail = "Requires manual review"
    
    comment = f"""
🤖 AI Classification Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{type_emoji} Type: {type_label}
{type_detail}

😊 Sentiment: {classification.get('sentiment', 'neutral')}
⚡ Urgency: {classification.get('urgency', 'medium')}
📊 Confidence: {classification.get('confidence', 0):.0%}

📧 AI Analysis Email: {'✅ Sent' if email_sent else '❌ Not sent'}

🤖 AI Reasoning:
{classification.get('reasoning', 'N/A')}

💬 Suggested Response:
{classification.get('suggested_response') or 'N/A'}
    """.strip()
    
    salesforce.post_case_comment(case_id, comment)
    actions_executed.append("sf:post_comment")
    
    logger.info(f"Executed {len(actions_executed)} actions")
    
    # Update decision with email status
    updated_decision = {**decision, "email_sent": email_sent}
    
    return {
        "decision": updated_decision,
        "actions_done": actions_executed
    }


# ============================================================================
# Graph Construction
# ============================================================================

def build_complaint_graph():
    """
    Build the Product Complaint Classification graph.
    
    Flow:
    FetchTicket -> ClassifyComplaint -> DecideAction -> ExecuteActions -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building Complaint Classification Graph")
    
    graph = StateGraph(ComplaintState)
    
    # Add nodes
    graph.add_node("FetchTicket", fetch_ticket)
    graph.add_node("ClassifyComplaint", classify_complaint)
    graph.add_node("DecideAction", decide_action)
    graph.add_node("ExecuteActions", execute_actions)
    
    # Define edges
    graph.set_entry_point("FetchTicket")
    graph.add_edge("FetchTicket", "ClassifyComplaint")
    graph.add_edge("ClassifyComplaint", "DecideAction")
    graph.add_edge("DecideAction", "ExecuteActions")
    graph.add_edge("ExecuteActions", END)
    
    compiled = graph.compile()
    
    logger.info("Complaint Classification Graph compiled successfully")
    return compiled


@traceable(
    name="Product Complaint Classification Workflow",
    run_type="chain",
    tags=["product-complaint", "classification", "langgraph"]
)
def run_complaint_classification(case: dict = None, use_llm: bool = True) -> ComplaintState:
    """
    Run the complaint classification workflow.
    
    Args:
        case: Optional case data. If None, fetches newest case.
        use_llm: Whether to use LLM for classification (default: True)
        
    Returns:
        Final state with classification and actions
    """
    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    logger.info("=" * 60)
    logger.info("🚀 STARTING COMPLAINT CLASSIFICATION WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"   Mode: {'🤖 LLM-Powered' if use_llm else '📊 Rule-Based'}")
    logger.info(f"   LangSmith Tracing: {'✅ ENABLED' if tracing_enabled else '❌ DISABLED'}")
    logger.info("=" * 60)
    
    # Authenticate with Salesforce
    salesforce.authenticate()
    
    # Build and run graph
    graph = build_complaint_graph()
    
    initial_state = create_initial_complaint_state(case or {}, use_llm=use_llm)
    
    config = {
        "run_name": f"📦 Complaint: {(case or {}).get('Subject', 'Auto')[:30]} ({'LLM' if use_llm else 'Rules'})",
        "tags": ["complaint-classification", f"mode:{'llm' if use_llm else 'rules'}"],
        "metadata": {
            "workflow": "complaint_classification",
            "use_llm": use_llm,
            "case_id": (case or {}).get("Id", "auto")
        }
    }
    
    final_state = graph.invoke(initial_state, config=config)
    
    # Log results
    classification = final_state.get("classification", {})
    decision = final_state.get("decision", {})
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ COMPLAINT CLASSIFICATION COMPLETE")
    logger.info("=" * 60)
    
    if classification.get("is_product_complaint"):
        logger.info(f"   📦 PRODUCT COMPLAINT")
        logger.info(f"   Category: {classification.get('product_category', 'N/A')}")
        logger.info(f"   Product: {classification.get('product_name') or 'General'}")
        logger.info(f"   📧 Email sent: {'✅' if decision.get('email_sent') else '❌'}")
    elif classification.get("is_it_support"):
        logger.info(f"   💻 IT SUPPORT")
        logger.info(f"   🔗 Redirect URL: {decision.get('redirect_url', 'N/A')}")
    else:
        logger.info(f"   📋 GENERAL INQUIRY")
    
    logger.info(f"   Sentiment: {classification.get('sentiment', 'N/A')}")
    logger.info(f"   Urgency: {classification.get('urgency', 'N/A')}")
    logger.info(f"   Actions: {len(final_state.get('actions_done', []))}")
    logger.info("=" * 60)
    
    return final_state
