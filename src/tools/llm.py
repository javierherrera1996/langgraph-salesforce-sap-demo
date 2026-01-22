"""
LLM Tools and Prompts
Centralized LLM configuration for lead scoring and ticket categorization.
Includes LangSmith tracing for full observability.
"""

import json
import logging
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.callbacks import CallbackManager
from langsmith import traceable
from pydantic import BaseModel, Field

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
# LLM Configuration
# ============================================================================

def get_llm(temperature: float = 0.0, model: str = "gpt-4o-mini") -> ChatOpenAI:
    """
    Get configured LLM instance with LangSmith tracing enabled.
    
    Args:
        temperature: Sampling temperature (0 = deterministic)
        model: Model name (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
    """
    # Ensure tracing is configured
    ensure_tracing_enabled()
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=1500,
        model_kwargs={"response_format": {"type": "json_object"}},
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
# Lead Scoring Prompts
# ============================================================================

LEAD_SCORING_SYSTEM_PROMPT = """You are an expert B2B sales lead qualification specialist at a Fortune 500 company.
Your analysis will be reviewed by sales leadership - provide clear, actionable reasoning.

## YOUR MISSION
Analyze each lead and assign a qualification score with DETAILED REASONING that explains:
1. WHY you assigned this specific score
2. WHAT factors were most influential (positive and negative)
3. HOW SAP data enriched your understanding
4. WHAT should happen next with this lead

## IDEAL CUSTOMER PROFILE (ICP)
Target: Enterprise companies that use Belden network infrastructure
- Industry fit: Technology, Financial Services, Healthcare, Manufacturing
- Company size: 500+ employees, $10M+ annual revenue
- Decision maker titles: C-level (CTO, CIO, CFO), VP, Director of IT/Engineering
- Buying signals: Hot/Warm rating, Referral/Event source, clear budget authority

## SCORING RUBRIC

### P1 / HOT (Score 0.75-1.0) → Route to Account Executive
Criteria (must meet 3+ of these):
✓ C-level or VP title with budget authority
✓ Enterprise company (1000+ employees OR $50M+ revenue)
✓ Target industry (Technology, Financial Services, Healthcare)
✓ Hot rating or Partner Referral source
✓ Existing SAP customer with A/A+ credit rating
✓ Clear description mentioning budget, timeline, or project

### P2 / WARM (Score 0.45-0.74) → Route to SDR for Qualification
Criteria (must meet 2+ of these):
✓ Director or Manager level with influence
✓ Mid-market company (100-999 employees OR $5M-50M revenue)
✓ Acceptable industry with potential
✓ Warm rating or Web/Event source
✓ Shows interest but needs discovery

### P3 / COLD (Score 0.00-0.44) → Route to Nurture Campaign
Criteria (any of these):
✗ Junior title (Analyst, Coordinator, Individual Contributor)
✗ Small company (<100 employees OR <$5M revenue)
✗ Poor industry fit (Consumer, Retail not in target)
✗ Cold rating or unclear buying intent
✗ No decision-making power indicated

## SAP ENRICHMENT BONUSES
- Existing customer with orders: +0.08 to score
- Credit rating A or A+: +0.05 to score
- Recent orders (active relationship): +0.03 to score
- High total revenue history: indicates strategic value

## REASONING FORMAT
Your reasoning MUST follow this structure:
"[VERDICT: P1/P2/P3] This lead scores [X.XX] because:
1. TITLE ANALYSIS: [analysis of job title and decision authority]
2. COMPANY FIT: [analysis of company size, industry, revenue]
3. BUYING SIGNALS: [analysis of rating, source, description intent]
4. SAP CONTEXT: [how SAP data influenced the score, if applicable]
CONCLUSION: [recommended action and why]"

Respond ONLY with valid JSON. Be specific in your reasoning - vague explanations are not acceptable."""

LEAD_SCORING_USER_PROMPT = """ANALYZE THIS LEAD FOR QUALIFICATION:

═══════════════════════════════════════════════════════════
LEAD PROFILE
═══════════════════════════════════════════════════════════
• Full Name: {name}
• Job Title: {title}
• Company: {company}
• Industry: {industry}
• Employee Count: {employees:,}
• Annual Revenue: ${revenue:,.0f}
• Lead Source: {source}
• Lead Rating: {rating}

LEAD DESCRIPTION:
"{description}"

═══════════════════════════════════════════════════════════
SAP ERP ENRICHMENT DATA
═══════════════════════════════════════════════════════════
• Existing SAP Customer: {is_customer}
• Business Partner ID: {bp_id}
• Historical Order Count: {total_orders}
• Lifetime Revenue: ${total_revenue:,.0f}
• Credit Rating: {credit_rating}
• Account Status: {account_status}

═══════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════
Provide comprehensive qualification analysis with:
1. score (0.0-1.0) - qualification score
2. confidence (0.0-1.0) - your confidence in this assessment
3. priority (P1, P2, or P3) - routing priority
4. reasoning (string) - DETAILED explanation following the format
5. key_factors (array) - top 3-5 factors that influenced your decision
6. recommended_action (string) - specific next step for sales

Remember: Your reasoning will be shown to sales leadership. Be specific and actionable."""


# ============================================================================
# Ticket Categorization Prompts
# ============================================================================

TICKET_CATEGORIZATION_SYSTEM_PROMPT = """You are an expert customer support triage specialist.

Your task is to categorize support tickets and draft appropriate responses.

## Categories
1. **howto** - Questions about how to use features, setup, configuration
   - Action: Auto-reply with KB articles
   - Urgency: Usually low/medium
   
2. **billing** - Payment issues, invoice questions, pricing, refunds
   - Action: Request additional information
   - Urgency: Medium (unless payment failure)
   
3. **outage** - System down, errors, performance issues, can't access
   - Action: ESCALATE to incident team
   - Urgency: High/Critical
   - Keywords: down, error, can't access, not working, slow, timeout
   
4. **security** - Unauthorized access, data concerns, vulnerabilities
   - Action: ESCALATE to security team immediately
   - Urgency: CRITICAL
   - Keywords: hack, breach, unauthorized, suspicious, vulnerability
   
5. **other** - Anything that doesn't fit above categories
   - Action: Request more information
   - Urgency: Based on tone

## Response Guidelines
- Be empathetic and professional
- Acknowledge the issue clearly
- Provide specific next steps
- For escalations, assure immediate attention

## Sentiment Detection
- **frustrated**: Multiple punctuation, caps, mentions of waiting
- **angry**: Strong language, threats, demands
- **positive**: Thanks, praise
- **neutral**: Factual, no strong emotion

Respond ONLY with valid JSON matching the schema."""

TICKET_CATEGORIZATION_USER_PROMPT = """Categorize this support ticket and draft a response:

## Ticket Details
- **Case Number**: {case_number}
- **Subject**: {subject}
- **Description**: 
{description}

- **Current Priority**: {priority}
- **Origin**: {origin}
- **Created**: {created_date}

## Customer Context from SAP
- **Has Open Orders**: {has_orders}
- **Total Order Value**: ${order_value:,.0f}
- **Business Partner**: {bp_id}

Provide your analysis as JSON with: category, confidence, urgency, reasoning, sentiment, suggested_response, requires_escalation, escalation_reason"""


# ============================================================================
# Product Complaint Classification Prompts (NEW)
# ============================================================================

PRODUCT_COMPLAINT_SYSTEM_PROMPT = """Eres un experto en clasificación de quejas y comentarios de clientes para Belden, 
una empresa líder en soluciones de infraestructura de red industrial.

## TU MISIÓN
Analizar cada ticket/comentario y determinar:
1. ¿Es una queja o problema relacionado con un PRODUCTO de Belden?
2. ¿Es un tema de IT/SOPORTE TÉCNICO general (no relacionado con productos)?
3. ¿Qué producto específico está involucrado?

## CATEGORÍAS DE PRODUCTOS BELDEN
- **switches**: Switches industriales (Hirschmann, Lumberg), switches Ethernet
- **cables**: Cables de red, cables industriales, fibra óptica
- **connectors**: Conectores, terminales, paneles de parcheo
- **software**: Software de gestión de red, firmware, aplicaciones
- **infrastructure**: Infraestructura de red, racks, gabinetes
- **general**: Productos Belden no especificados claramente

## EJEMPLOS DE QUEJAS DE PRODUCTO
- "El switch Hirschmann se reinicia solo" → switches
- "Los cables no funcionan correctamente" → cables  
- "El conector está defectuoso" → connectors
- "El firmware tiene bugs" → software
- "Producto llegó dañado" → Identificar qué producto

## EJEMPLOS DE IT SOPORTE (NO producto)
- "No puedo acceder al portal"
- "Olvidé mi contraseña"
- "Necesito ayuda para configurar mi VPN"
- "¿Cómo instalo el software?"
- "Problemas con mi cuenta"

## FORMATO DE RESPUESTA
Responde SIEMPRE en JSON válido con estos campos:
- is_product_complaint: true/false
- is_it_support: true/false
- product_category: switches|cables|connectors|software|infrastructure|general|none
- product_name: nombre específico o ""
- confidence: 0.0-1.0
- reasoning: explicación detallada
- sentiment: angry|frustrated|neutral|positive
- urgency: critical|high|medium|low
- complaint_summary: resumen breve
- suggested_response: respuesta sugerida al cliente

IMPORTANTE: Si NO es queja de producto NI IT soporte, pon is_product_complaint=false, is_it_support=false, product_category="none"
"""

PRODUCT_COMPLAINT_USER_PROMPT = """Clasifica el siguiente ticket/comentario:

## Información del Ticket
- **Número de Caso**: {case_number}
- **Asunto**: {subject}
- **Descripción completa**: 
{description}

- **Prioridad actual**: {priority}
- **Origen**: {origin}
- **Fecha de creación**: {created_date}

Analiza cuidadosamente y proporciona tu clasificación en formato JSON."""


# ============================================================================
# LLM Chains (with explicit naming for LangSmith)
# ============================================================================

def create_lead_scoring_chain():
    """Create the lead scoring chain with structured output and LangSmith naming."""
    llm = get_llm(temperature=0.0, model="gpt-4o-mini")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", LEAD_SCORING_SYSTEM_PROMPT),
        ("user", LEAD_SCORING_USER_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=LeadScoreOutput)
    
    # Create chain with explicit run name for LangSmith tracing
    chain = prompt | llm | parser
    return chain.with_config({"run_name": "🎯 Lead Scoring Chain"})


def create_ticket_categorization_chain():
    """Create the ticket categorization chain with structured output and LangSmith naming."""
    llm = get_llm(temperature=0.1, model="gpt-4o-mini")  # Slight creativity for responses
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", TICKET_CATEGORIZATION_SYSTEM_PROMPT),
        ("user", TICKET_CATEGORIZATION_USER_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=TicketCategoryOutput)
    
    # Create chain with explicit run name for LangSmith tracing
    chain = prompt | llm | parser
    return chain.with_config({"run_name": "🎫 Ticket Categorization Chain"})


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
        
        logger.info("📤 Sending to LLM...")
        
        # Invoke chain (traced by LangSmith)
        result = chain.invoke(input_data)
        
        # Ensure all required fields exist with defaults
        result = {
            "score": result.get("score", 0.5),
            "confidence": result.get("confidence", 0.7),
            "priority": result.get("priority", "P2"),
            "reasoning": result.get("reasoning", "No reasoning provided by LLM"),
            "key_factors": result.get("key_factors", ["LLM analysis completed"]),
            "recommended_action": result.get("recommended_action", "Follow up with lead based on score")
        }
        
        # Log detailed results
        logger.info("=" * 60)
        logger.info("✅ LLM SCORING COMPLETE")
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
        
        result = chain.invoke({
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
        
        logger.info("=" * 60)
        logger.info("✅ CATEGORIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"   CATEGORY: {result['category'].upper()}")
        logger.info(f"   URGENCY: {result['urgency']} | SENTIMENT: {result['sentiment']}")
        logger.info(f"   ESCALATE: {'⚠️ YES' if result['requires_escalation'] else 'No'}")
        logger.info("-" * 60)
        logger.info(f"📋 REASONING: {result['reasoning']}")
        logger.info("=" * 60)
        
        return result
        
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
        llm = get_llm(temperature=0.1, model="gpt-4o-mini")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PRODUCT_COMPLAINT_SYSTEM_PROMPT),
            ("user", PRODUCT_COMPLAINT_USER_PROMPT)
        ])
        
        parser = JsonOutputParser(pydantic_object=ProductComplaintOutput)
        chain = prompt | llm | parser
        chain = chain.with_config({"run_name": "📦 Product Complaint Chain"})
        
        input_data = {
            "case_number": case_number,
            "subject": subject,
            "description": case.get("Description", "No description"),
            "priority": case.get("Priority", "Unknown"),
            "origin": case.get("Origin", "Unknown"),
            "created_date": case.get("CreatedDate", "Unknown")
        }
        
        logger.info("📤 Sending to LLM for classification...")
        result = chain.invoke(input_data)
        
        # Ensure all required fields exist
        result = {
            "is_product_complaint": result.get("is_product_complaint", False),
            "is_it_support": result.get("is_it_support", False),
            "product_category": result.get("product_category", "none"),
            "product_name": result.get("product_name", ""),
            "confidence": result.get("confidence", 0.7),
            "reasoning": result.get("reasoning", "Classification completed"),
            "sentiment": result.get("sentiment", "neutral"),
            "urgency": result.get("urgency", "medium"),
            "complaint_summary": result.get("complaint_summary", subject),
            "suggested_response": result.get("suggested_response", "Thank you for contacting us.")
        }
        
        logger.info("=" * 60)
        logger.info("✅ CLASSIFICATION COMPLETE")
        logger.info("=" * 60)
        
        if result["is_product_complaint"]:
            logger.info(f"   📦 PRODUCT COMPLAINT DETECTED")
            logger.info(f"   Category: {result['product_category']}")
            logger.info(f"   Product: {result['product_name'] or 'Not specified'}")
        elif result["is_it_support"]:
            logger.info(f"   💻 IT SUPPORT REQUEST DETECTED")
        else:
            logger.info(f"   ❓ OTHER/GENERAL INQUIRY")
        
        logger.info(f"   Sentiment: {result['sentiment']}")
        logger.info(f"   Urgency: {result['urgency']}")
        logger.info(f"   Confidence: {result['confidence']:.0%}")
        logger.info("-" * 60)
        logger.info(f"📋 REASONING: {result['reasoning'][:100]}...")
        logger.info("=" * 60)
        
        return result
        
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
        Dictionary with system and user prompts
    """
    if prompt_type == "lead_scoring":
        return {
            "system": LEAD_SCORING_SYSTEM_PROMPT,
            "user": LEAD_SCORING_USER_PROMPT
        }
    elif prompt_type == "ticket_categorization":
        return {
            "system": TICKET_CATEGORIZATION_SYSTEM_PROMPT,
            "user": TICKET_CATEGORIZATION_USER_PROMPT
        }
    elif prompt_type == "product_complaint":
        return {
            "system": PRODUCT_COMPLAINT_SYSTEM_PROMPT,
            "user": PRODUCT_COMPLAINT_USER_PROMPT
        }
    else:
        return {"error": f"Unknown prompt type: {prompt_type}"}
