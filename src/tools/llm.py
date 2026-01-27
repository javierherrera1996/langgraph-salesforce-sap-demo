"""
LLM Tools and Prompts
Centralized LLM configuration for lead scoring and ticket categorization.
Includes LangSmith tracing for full observability.
Prompts are loaded from LangSmith Hub first, with local fallback.
"""

import json
import logging
import os
from typing import Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
# JsonOutputParser no longer needed - using with_structured_output() instead
from langchain_core.callbacks import CallbackManager
from langsmith import traceable
from pydantic import BaseModel, Field

# Import local prompts for fallback
from .prompts import (
    get_local_prompts,
    get_langsmith_prompt_name,
    PROMPT_REGISTRY,
)

logger = logging.getLogger(__name__)


# ============================================================================
# LangSmith Tracing Setup
# ============================================================================

def ensure_tracing_enabled():
    """Ensure LangSmith tracing is properly configured."""
    # Set tracing environment variables if not already set
    if not os.environ.get("LANGCHAIN_TRACING_V2"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if not os.environ.get("LANGCHAIN_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = "langgraph-salesforce-sap-demo"
    
    api_key = os.environ.get("LANGSMITH_API_KEY", "")
    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    if tracing_enabled and api_key:
        logger.info("🔍 LangSmith tracing: ENABLED")
    else:
        logger.warning("⚠️ LangSmith tracing: DISABLED (missing LANGSMITH_API_KEY)")
    
    return tracing_enabled and bool(api_key)


# ============================================================================
# Prompt Loading (LangSmith Hub with Local Fallback)
# ============================================================================

def get_prompt(prompt_type: str) -> Tuple[ChatPromptTemplate, str]:
    """
    Get a prompt, trying LangSmith Hub first, then falling back to local.

    Args:
        prompt_type: "lead_scoring", "ticket_categorization", or "product_complaint"

    Returns:
        Tuple of (ChatPromptTemplate, source) where source is "langsmith" or "local"
    """
    langsmith_name = get_langsmith_prompt_name(prompt_type)

    # Try LangSmith Hub first
    try:
        from langchain import hub

        # Try to pull from LangSmith Hub
        # Format: "owner/prompt-name" or just "prompt-name" for your own prompts
        prompt = hub.pull(langsmith_name)
        logger.info(f"✅ Loaded prompt '{prompt_type}' from LangSmith Hub ({langsmith_name})")
        return prompt, "langsmith"

    except Exception as e:
        logger.warning(f"⚠️ Could not load '{prompt_type}' from LangSmith Hub: {e}")
        logger.info(f"📁 Using local fallback for '{prompt_type}'")

        # Fallback to local prompts
        local_prompts = get_local_prompts(prompt_type)
        prompt = ChatPromptTemplate.from_messages([
            ("system", local_prompts["system"]),
            ("user", local_prompts["user"])
        ])
        return prompt, "local"


def get_prompt_with_details(prompt_type: str) -> dict:
    """
    Get prompt with metadata about its source.

    Args:
        prompt_type: "lead_scoring", "ticket_categorization", or "product_complaint"

    Returns:
        Dictionary with prompt, source, and langsmith_name
    """
    prompt, source = get_prompt(prompt_type)
    return {
        "prompt": prompt,
        "source": source,
        "langsmith_name": get_langsmith_prompt_name(prompt_type),
        "prompt_type": prompt_type,
    }


# ============================================================================
# LLM Configuration
# ============================================================================

def get_llm(temperature: float = 0.0, model: str = "gpt-4o-mini", use_json_mode: bool = True) -> ChatOpenAI:
    """
    Get LLM instance with deterministic settings for consistent scoring.

    Note: Temperature is set to 0.0 for maximum determinism.
    For lead scoring, we want consistent results for the same input.

    Args:
        temperature: Sampling temperature (0 = deterministic)
        model: Model name (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
        use_json_mode: If True, forces JSON output. Set to False when using with_structured_output()
    """
    # Ensure tracing is configured
    ensure_tracing_enabled()

    model_kwargs = {"seed": 42}  # Add seed for reproducibility

    # Only add json_object response format if not using structured output
    # with_structured_output() uses function calling which is incompatible with json_object mode
    if use_json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=2000,
        model_kwargs=model_kwargs,
    )


# ============================================================================
# Output Schemas
# ============================================================================

class LeadScoreOutput(BaseModel):
    """Structured output for lead scoring."""
    score: float = Field(description="Lead score from 0.0 to 1.0")
    confidence: float = Field(description="Confidence in the score from 0.0 to 1.0")
    priority: str = Field(description="Priority level: P1, P2, or P3")
    reasoning: str = Field(description="Explanation of the scoring decision")
    key_factors: list[str] = Field(description="Top 3 factors that influenced the score")
    recommended_action: str = Field(description="Suggested next action for this lead")


class ProductComplaintOutput(BaseModel):
    """Structured output for product complaint classification."""
    is_product_complaint: bool = Field(description="True if this is a product-related complaint/issue")
    is_it_support: bool = Field(description="True if this is an IT/technical support request")
    product_category: str = Field(description="Product category: switches, cables, connectors, software, infrastructure, general, none")
    product_name: str = Field(description="Specific product name if mentioned, or empty string")
    confidence: float = Field(description="Confidence in the classification from 0.0 to 1.0")
    reasoning: str = Field(description="Explanation of why this was classified this way")
    sentiment: str = Field(description="Customer sentiment: angry, frustrated, neutral, positive")
    urgency: str = Field(description="Urgency level: critical, high, medium, low")
    complaint_summary: str = Field(description="Brief summary of the complaint/issue")
    suggested_response: str = Field(description="Suggested response to the customer")


class TicketCategoryOutput(BaseModel):
    """Structured output for ticket categorization."""
    category: str = Field(description="Category: howto, billing, outage, security, or other")
    confidence: float = Field(description="Confidence in the categorization from 0.0 to 1.0")
    urgency: str = Field(description="Urgency level: low, medium, high, or critical")
    reasoning: str = Field(description="Explanation of the categorization")
    sentiment: str = Field(description="Customer sentiment: positive, neutral, frustrated, angry")
    suggested_response: str = Field(description="Draft response to the customer")
    requires_escalation: bool = Field(description="Whether this ticket should be escalated")
    escalation_reason: Optional[str] = Field(description="Reason for escalation if required")


# ============================================================================
# LLM Chains (with explicit naming for LangSmith)
# ============================================================================

def create_lead_scoring_chain():
    """Create the lead scoring chain with GUARANTEED structured output.

    Prompts are loaded from LangSmith Hub first, with local fallback.
    Uses with_structured_output() for reliable schema enforcement via function calling.
    Temperature=0.0 for maximum determinism - same input should produce same output.
    """
    # use_json_mode=False because with_structured_output uses function calling
    llm = get_llm(temperature=0.0, model="gpt-4o-mini", use_json_mode=False)

    # Use with_structured_output to GUARANTEE the schema
    structured_llm = llm.with_structured_output(LeadScoreOutput)

    # Load prompt from LangSmith Hub (with local fallback)
    prompt, source = get_prompt("lead_scoring")
    logger.info(f"📝 Lead scoring prompt source: {source}")

    # Chain returns Pydantic model directly (no parser needed)
    chain = prompt | structured_llm
    return chain.with_config({"run_name": "🎯 Lead Scoring Chain (Structured)"})


def create_ticket_categorization_chain():
    """Create the ticket categorization chain with GUARANTEED structured output.

    Prompts are loaded from LangSmith Hub first, with local fallback.
    """
    # use_json_mode=False because with_structured_output uses function calling
    llm = get_llm(temperature=0.1, model="gpt-4o-mini", use_json_mode=False)

    # Use with_structured_output to GUARANTEE the schema
    structured_llm = llm.with_structured_output(TicketCategoryOutput)

    # Load prompt from LangSmith Hub (with local fallback)
    prompt, source = get_prompt("ticket_categorization")
    logger.info(f"📝 Ticket categorization prompt source: {source}")

    # Chain returns Pydantic model directly (no parser needed)
    chain = prompt | structured_llm
    return chain.with_config({"run_name": "🎫 Ticket Categorization Chain (Structured)"})


# ============================================================================
# Main Functions (with LangSmith Tracing)
# ============================================================================

@traceable(
    name="🎯 Lead Qualification LLM",
    run_type="llm",
    tags=["lead-scoring", "qualification", "gpt-4o-mini"]
)
def score_lead_with_llm(lead: dict, enriched: dict) -> dict:
    """
    Score a lead using LLM reasoning with full LangSmith tracing.
    
    This function is decorated with @traceable to send traces to LangSmith,
    allowing you to see the full prompt, response, and reasoning.
    
    Args:
        lead: Salesforce Lead data
        enriched: SAP enrichment data
        
    Returns:
        LeadScoreOutput as dictionary with:
        - score: 0.0-1.0 qualification score
        - confidence: 0.0-1.0 model confidence
        - priority: P1, P2, or P3
        - reasoning: Detailed explanation
        - key_factors: List of influential factors
        - recommended_action: Next step
    """
    lead_id = lead.get('Id', 'unknown')
    company = lead.get('Company', 'Unknown')
    
    logger.info("=" * 60)
    logger.info(f"🤖 LLM LEAD SCORING - {company}")
    logger.info("=" * 60)
    logger.info(f"   Lead ID: {lead_id}")
    logger.info(f"   Title: {lead.get('Title', 'Unknown')}")
    logger.info(f"   SAP Customer: {'Yes' if enriched.get('business_partner_id') else 'No'}")
    
    try:
        chain = create_lead_scoring_chain()
        
        # Prepare input data
        input_data = {
            "name": lead.get("Name", "Unknown"),
            "company": company,
            "title": lead.get("Title", "Unknown"),
            "industry": lead.get("Industry", "Unknown"),
            "employees": lead.get("NumberOfEmployees", 0) or 0,
            "revenue": lead.get("AnnualRevenue", 0) or 0,
            "source": lead.get("LeadSource", "Unknown"),
            "rating": lead.get("Rating", "Unknown"),
            "description": lead.get("Description", "No description provided"),
            "is_customer": "Yes ✓" if enriched.get("business_partner_id") else "No",
            "bp_id": enriched.get("business_partner_id", "N/A"),
            "total_orders": enriched.get("total_orders", 0),
            "total_revenue": enriched.get("total_revenue", 0) or 0,
            "credit_rating": enriched.get("credit_rating", "Unknown"),
            "account_status": enriched.get("account_status", "Unknown"),
        }
        
        logger.info("📤 Sending to LLM (with_structured_output)...")

        # Invoke chain - returns Pydantic model directly
        result: LeadScoreOutput = chain.invoke(input_data)

        # Convert Pydantic model to dict
        # with_structured_output guarantees all fields are present and correctly typed
        result = result.model_dump()
        
        # Log detailed results
        logger.info("=" * 60)
        logger.info("✅ LLM SCORING COMPLETE (Structured Output)")
        logger.info("=" * 60)
        logger.info(f"   SCORE: {result['score']:.2f} | PRIORITY: {result['priority']}")
        logger.info(f"   CONFIDENCE: {result['confidence']:.0%}")
        logger.info("-" * 60)
        logger.info("📋 REASONING:")
        logger.info(f"   {result['reasoning']}")
        logger.info("-" * 60)
        logger.info("🔑 KEY FACTORS:")
        for i, factor in enumerate(result.get('key_factors', []), 1):
            logger.info(f"   {i}. {factor}")
        logger.info("-" * 60)
        logger.info(f"📌 RECOMMENDED ACTION: {result['recommended_action']}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ LLM SCORING FAILED: {e}")
        logger.error("=" * 60)
        
        # Return fallback with clear explanation
        fallback = {
            "score": 0.5,
            "confidence": 0.0,
            "priority": "P2",
            "reasoning": f"[FALLBACK] LLM scoring encountered an error: {str(e)}. Using default mid-range score (0.5) which routes to SDR for manual qualification. Please review this lead manually.",
            "key_factors": [
                "Error in LLM processing",
                "Requires manual review",
                f"Technical issue: {str(e)[:50]}"
            ],
            "recommended_action": "Manual qualification required - contact SDR team"
        }
        
        logger.info(f"   Using fallback score: {fallback['score']}")
        return fallback


@traceable(
    name="🎫 Ticket Categorization LLM",
    run_type="llm",
    tags=["ticket-triage", "categorization", "gpt-4o-mini"]
)
def categorize_ticket_with_llm(case: dict, sap_context: dict) -> dict:
    """
    Categorize a ticket using LLM reasoning with full LangSmith tracing.
    
    Args:
        case: Salesforce Case data
        sap_context: SAP order context
        
    Returns:
        TicketCategoryOutput as dictionary
    """
    case_number = case.get('CaseNumber', 'Unknown')
    subject = case.get('Subject', 'No subject')
    
    logger.info("=" * 60)
    logger.info(f"🤖 LLM TICKET CATEGORIZATION - Case #{case_number}")
    logger.info("=" * 60)
    logger.info(f"   Subject: {subject[:50]}...")
    
    try:
        chain = create_ticket_categorization_chain()

        logger.info("📤 Sending to LLM (with_structured_output)...")

        # Invoke chain - returns Pydantic model directly
        result: TicketCategoryOutput = chain.invoke({
            "case_number": case_number,
            "subject": subject,
            "description": case.get("Description", "No description"),
            "priority": case.get("Priority", "Medium"),
            "origin": case.get("Origin", "Unknown"),
            "created_date": case.get("CreatedDate", "Unknown"),
            "has_orders": "Yes" if sap_context.get("has_open_orders") else "No",
            "order_value": sap_context.get("total_order_value", 0) or 0,
            "bp_id": sap_context.get("business_partner_id", "N/A"),
        })

        # Convert Pydantic model to dict
        result_dict = result.model_dump()

        logger.info("=" * 60)
        logger.info("✅ CATEGORIZATION COMPLETE (Structured Output)")
        logger.info("=" * 60)
        logger.info(f"   CATEGORY: {result_dict['category'].upper()}")
        logger.info(f"   URGENCY: {result_dict['urgency']} | SENTIMENT: {result_dict['sentiment']}")
        logger.info(f"   ESCALATE: {'⚠️ YES' if result_dict['requires_escalation'] else 'No'}")
        logger.info("-" * 60)
        logger.info(f"📋 REASONING: {result_dict['reasoning']}")
        logger.info("=" * 60)

        return result_dict
        
    except Exception as e:
        logger.error(f"❌ LLM categorization failed: {e}")
        return {
            "category": "other",
            "confidence": 0.0,
            "urgency": "medium",
            "reasoning": f"[FALLBACK] LLM categorization failed: {str(e)}. Routing to general support.",
            "sentiment": "neutral",
            "suggested_response": "Thank you for contacting support. A representative will review your case shortly.",
            "requires_escalation": False,
            "escalation_reason": None
        }


@traceable(
    name="📦 Product Complaint Classification LLM",
    run_type="llm",
    tags=["product-complaint", "classification", "gpt-4o-mini"]
)
def classify_product_complaint_with_llm(case: dict) -> dict:
    """
    Classify if a ticket is a product complaint or IT support issue.

    Uses with_structured_output() to GUARANTEE the output structure matches
    the ProductComplaintOutput Pydantic model. This prevents JSON parsing errors
    and ensures all fields are present with correct types.

    Args:
        case: Salesforce Case data

    Returns:
        ProductComplaintOutput as dictionary with:
        - is_product_complaint: True if product-related
        - is_it_support: True if IT support
        - product_category: Category of product
        - product_name: Specific product if identified
        - etc.
    """
    case_number = case.get('CaseNumber', case.get('Id', 'Unknown'))
    subject = case.get('Subject', 'No subject')

    logger.info("=" * 60)
    logger.info(f"🤖 LLM PRODUCT CLASSIFICATION - Case #{case_number}")
    logger.info("=" * 60)
    logger.info(f"   Subject: {subject[:50]}...")

    try:
        # Use use_json_mode=False because with_structured_output uses function calling
        llm = get_llm(temperature=0.1, model="gpt-4o-mini", use_json_mode=False)

        # Use with_structured_output to GUARANTEE the schema
        # This uses function calling under the hood, which is more reliable than JSON mode
        structured_llm = llm.with_structured_output(ProductComplaintOutput)

        # Load prompt from LangSmith Hub (with local fallback)
        prompt, source = get_prompt("product_complaint")
        logger.info(f"📝 Product complaint prompt source: {source}")

        # Chain: prompt -> structured LLM (returns Pydantic model directly)
        chain = prompt | structured_llm
        chain = chain.with_config({"run_name": "📦 Product Complaint Chain (Structured)"})

        input_data = {
            "case_number": case_number,
            "subject": subject,
            "description": case.get("Description", "No description"),
            "priority": case.get("Priority", "Unknown"),
            "origin": case.get("Origin", "Unknown"),
            "created_date": case.get("CreatedDate", "Unknown")
        }

        logger.info("📤 Sending to LLM for classification (with_structured_output)...")
        result: ProductComplaintOutput = chain.invoke(input_data)

        # Convert Pydantic model to dict
        # with_structured_output guarantees all fields are present and correctly typed
        result_dict = result.model_dump()

        logger.info("=" * 60)
        logger.info("✅ CLASSIFICATION COMPLETE (Structured Output)")
        logger.info("=" * 60)

        if result_dict["is_product_complaint"]:
            logger.info(f"   📦 PRODUCT COMPLAINT DETECTED")
            logger.info(f"   Category: {result_dict['product_category']}")
            logger.info(f"   Product: {result_dict['product_name'] or 'Not specified'}")
        elif result_dict["is_it_support"]:
            logger.info(f"   💻 IT SUPPORT REQUEST DETECTED")
        else:
            logger.info(f"   ❓ OTHER/GENERAL INQUIRY")

        logger.info(f"   Sentiment: {result_dict['sentiment']}")
        logger.info(f"   Urgency: {result_dict['urgency']}")
        logger.info(f"   Confidence: {result_dict['confidence']:.0%}")
        logger.info("-" * 60)
        logger.info(f"📋 REASONING: {result_dict['reasoning'][:100]}...")
        logger.info("=" * 60)

        return result_dict

    except Exception as e:
        logger.error(f"❌ LLM classification failed: {e}")
        return {
            "is_product_complaint": False,
            "is_it_support": False,
            "product_category": "none",
            "product_name": "",
            "confidence": 0.0,
            "reasoning": f"[FALLBACK] Classification failed: {str(e)}",
            "sentiment": "neutral",
            "urgency": "medium",
            "complaint_summary": subject,
            "suggested_response": "Thank you for contacting us. A representative will review your case."
        }


# ============================================================================
# Utility Functions
# ============================================================================

def get_prompt_for_demo(prompt_type: str) -> dict:
    """
    Get prompt text for demo/documentation purposes.

    Args:
        prompt_type: "lead_scoring", "ticket_categorization", or "product_complaint"

    Returns:
        Dictionary with system and user prompts, and source info
    """
    try:
        local_prompts = get_local_prompts(prompt_type)
        return {
            "system": local_prompts["system"],
            "user": local_prompts["user"],
            "source": "local",
            "langsmith_name": get_langsmith_prompt_name(prompt_type),
        }
    except ValueError as e:
        return {"error": str(e)}
