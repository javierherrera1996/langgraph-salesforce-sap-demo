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
    Get LLM instance with deterministic settings for consistent scoring.
    
    Note: Temperature is set to 0.0 for maximum determinism.
    For lead scoring, we want consistent results for the same input.
    """
    """
    Get configured LLM instance with LangSmith tracing enabled.
    
    Args:
        temperature: Sampling temperature (0 = deterministic)
        model: Model name (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
    """
    # Ensure tracing is configured
    ensure_tracing_enabled()
    
    # Force deterministic JSON output for consistent scoring
    return ChatOpenAI(
        model=model,
        temperature=temperature,  # Should be 0.0 for lead scoring
        max_tokens=2000,  # Increased for detailed reasoning
        model_kwargs={
            "response_format": {"type": "json_object"},
            "seed": 42  # Add seed for reproducibility (if supported)
        },
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

LEAD_SCORING_SYSTEM_PROMPT = """You are a deterministic B2B sales lead qualification specialist. 
You MUST provide CONSISTENT scores for the same lead data. Use strict numerical rules.

## CRITICAL: DETERMINISTIC SCORING
- Same input data MUST produce the same score (within 0.02 variance)
- Use the scoring formula below - do NOT use intuition
- Calculate points systematically, then convert to 0.0-1.0 scale

## SCORING FORMULA (Base Score Calculation)

### Step 1: Title Score (0.0 - 0.30 points)
- C-Level (CEO, CTO, CIO, CFO, COO): 0.30 points
- VP (Vice President, VP Engineering, VP IT): 0.25 points
- Director (Director of IT, Director Engineering): 0.18 points
- Manager (IT Manager, Engineering Manager): 0.12 points
- Senior/Lead (Senior Engineer, Lead Developer): 0.08 points
- Individual Contributor/Analyst/Coordinator: 0.03 points
- Owner (small business): 0.10 points
- Other/Unknown: 0.05 points

### Step 2: Company Size Score (0.0 - 0.25 points)
- 10,000+ employees OR $500M+ revenue: 0.25 points
- 5,000-9,999 employees OR $200M-499M revenue: 0.22 points
- 1,000-4,999 employees OR $50M-199M revenue: 0.18 points
- 500-999 employees OR $20M-49M revenue: 0.15 points
- 100-499 employees OR $5M-19M revenue: 0.10 points
- 50-99 employees OR $2M-4.9M revenue: 0.06 points
- 10-49 employees OR $500K-1.9M revenue: 0.03 points
- <10 employees OR <$500K revenue: 0.01 points

### Step 3: Industry Fit Score (0.0 - 0.15 points)
- Technology: 0.15 points
- Financial Services: 0.15 points
- Healthcare: 0.15 points
- Manufacturing: 0.12 points
- Telecommunications: 0.12 points
- Energy/Utilities: 0.10 points
- Logistics/Transportation: 0.08 points
- Retail/Consumer: 0.03 points
- Other: 0.05 points

### Step 4: Buying Signals Score (0.0 - 0.20 points)
- Rating: Hot = 0.10, Warm = 0.06, Cold = 0.02
- Source: Partner Referral = 0.08, Event = 0.06, Web = 0.04, Cold Call = 0.02
- Description contains: "budget" = +0.02, "timeline" = +0.02, "project" = +0.02, "approved" = +0.02

### Step 5: SAP Enrichment Bonus (0.0 - 0.10 points)
- Existing customer with orders: +0.08 points
- Credit rating A or A+: +0.05 points
- Credit rating B: +0.03 points
- Recent orders (last 6 months): +0.02 points
- High lifetime revenue ($1M+): +0.02 points

## FINAL SCORE CALCULATION
Total Points = Title + Company Size + Industry + Buying Signals + SAP Bonus
Final Score = min(1.0, Total Points)  # Cap at 1.0

## PRIORITY ASSIGNMENT (Based on Final Score)
- Score 0.75-1.00 → P1 (HOT) → Route to Account Executive
- Score 0.45-0.74 → P2 (WARM) → Route to SDR
- Score 0.00-0.44 → P3 (COLD) → Route to Nurture Campaign

## REASONING FORMAT (Required Structure)
"[VERDICT: P1/P2/P3] This lead scores [X.XX] calculated as:
1. TITLE: [title] = [X.XX] points
2. COMPANY SIZE: [employees] employees, ${revenue} revenue = [X.XX] points
3. INDUSTRY: [industry] = [X.XX] points
4. BUYING SIGNALS: Rating=[rating] ([X.XX]), Source=[source] ([X.XX]), Description keywords=[keywords] ([X.XX]) = [X.XX] total
5. SAP BONUS: [details] = [X.XX] points
TOTAL: [sum] points → Final Score: [X.XX]
CONCLUSION: [recommended action]"

## CRITICAL RULES
1. ALWAYS calculate points using the formula above
2. ALWAYS show your calculation in reasoning
3. Same input = same calculation = same score
4. Round final score to 2 decimal places (e.g., 0.75, not 0.753)
5. Be deterministic - no guessing or intuition

Respond ONLY with valid JSON following the exact structure."""

LEAD_SCORING_USER_PROMPT = """CALCULATE LEAD QUALIFICATION SCORE USING THE FORMULA:

═══════════════════════════════════════════════════════════
LEAD DATA
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
1. Calculate points for EACH category using the formula:
   - Title Score: Look up {title} in the title scoring table
   - Company Size Score: Use {employees:,} employees OR ${revenue:,.0f} revenue
   - Industry Score: Look up {industry} in the industry table
   - Buying Signals: Rating={rating}, Source={source}, check description for keywords
   - SAP Bonus: Check {is_customer}, {credit_rating}, {total_orders}, ${total_revenue:,.0f}

2. Sum all points: Total = Title + Company + Industry + Buying + SAP

3. Final Score = min(1.0, Total) rounded to 2 decimals

4. Priority: P1 if score >= 0.75, P2 if score >= 0.45, P3 otherwise

5. Provide reasoning showing your calculation step-by-step

CRITICAL: Use the exact formula. Same data = same calculation = same score.
Be deterministic and show your math."""


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

PRODUCT_COMPLAINT_SYSTEM_PROMPT = """You are an expert in classifying customer complaints and comments for Belden, 
a leading company in industrial network infrastructure solutions.

## YOUR MISSION
Analyze each ticket/comment and determine with HIGH CONFIDENCE:
1. Is it a complaint or issue related to a Belden PHYSICAL PRODUCT or SOFTWARE? → Send to Product Expert
2. Is it a SERVICES/WEB PAGE/IT/ACCOUNT issue? → Send to Services Agent
3. What specific product is involved? (if applicable)

## CRITICAL DISTINCTION

### 📦 PRODUCT COMPLAINT (Send to Product Expert) - Physical items or software
**MUST be about a tangible Belden product or Belden software:**
- **switches**: Industrial switches (Hirschmann, Lumberg), Ethernet switches, network switches
- **cables**: Network cables, industrial cables, fiber optic cables, copper cables, patch cables
- **connectors**: Connectors, terminals, patch panels, RJ45 connectors, fiber connectors
- **software**: Belden network management software, Belden firmware, Belden applications
- **infrastructure**: Belden network infrastructure, Belden racks, Belden cabinets
- **general**: Any Belden physical product or Belden software not clearly specified

**KEY INDICATORS:**
- Mentions specific product names (Hirschmann, Lumberg, model numbers)
- Physical product issues (broken, defective, not working, damaged)
- Software/firmware bugs or issues with Belden software
- Product specifications, compatibility, installation of Belden products
- Product arrived damaged, wrong product received
- Product performance issues

**Examples**: 
- "The Hirschmann switch keeps restarting" → switches
- "The cable broke after 2 weeks" → cables
- "The connector doesn't fit" → connectors
- "The firmware update caused bugs" → software
- "Product arrived damaged" → general product

### 🌐 SERVICES/IT/ACCOUNT (Send to Services Agent) - NOT about products
**MUST be about services, accounts, or IT support:**
- Website/portal access problems (cannot log in, cannot access)
- Account issues (password reset, account locked, account information)
- Login/authentication problems
- Order tracking, invoice access, billing portal
- General IT support (VPN setup, computer issues, network configuration help)
- Service requests (installation services, support services)
- Online platform issues (website down, portal not loading)

**KEY INDICATORS:**
- Cannot access, cannot log in, password issues
- Account-related problems
- Portal, website, online platform issues
- Service requests (not product issues)
- IT support requests (not product defects)

**Examples**: 
- "I cannot access the customer portal" → IT/Account
- "I forgot my password" → IT/Account
- "I need help setting up VPN" → IT Support
- "The website is not loading" → IT/Service
- "I can't find my order in the portal" → IT/Account
- "My account is locked" → IT/Account

## DECISION RULES
1. If it mentions a Belden PRODUCT (switch, cable, connector, software) having an issue → PRODUCT
2. If it's about accessing websites, portals, accounts, passwords → SERVICES/IT
3. If it's unclear but mentions physical items or software → PRODUCT (default)
4. If it's about services, accounts, or IT help → SERVICES/IT

## PRODUCT COMPLAINT EXAMPLES
- "The Hirschmann switch keeps restarting" → switches
- "The cables are not working correctly" → cables  
- "The connector is defective" → connectors
- "The firmware has bugs" → software
- "Product arrived damaged" → Identify which product

## IT SUPPORT EXAMPLES (NOT product)
- "I cannot access the portal"
- "I forgot my password"
- "I need help configuring my VPN"
- "How do I install the software?"
- "Problems with my account"

## RESPONSE FORMAT
Always respond with valid JSON containing these fields:
- is_product_complaint: true/false
- is_it_support: true/false
- product_category: switches|cables|connectors|software|infrastructure|general|none
- product_name: specific product name or ""
- confidence: 0.0-1.0
- reasoning: detailed explanation in English
- sentiment: angry|frustrated|neutral|positive
- urgency: critical|high|medium|low
- complaint_summary: brief summary in English
- suggested_response: suggested response to customer in English

IMPORTANT: If it's NOT a product complaint NOR IT support, set is_product_complaint=false, is_it_support=false, product_category="none"
"""

PRODUCT_COMPLAINT_USER_PROMPT = """Classify the following ticket/comment:

## Ticket Information
- **Case Number**: {case_number}
- **Subject**: {subject}
- **Full Description**: 
{description}

- **Current Priority**: {priority}
- **Origin**: {origin}
- **Created Date**: {created_date}

## Your Task
Analyze carefully and determine:
1. Is this about a Belden PRODUCT (physical item or software) having an issue? → is_product_complaint = true
2. Is this about SERVICES/IT/ACCOUNT (portal access, passwords, website)? → is_it_support = true
3. If product: What category? (switches, cables, connectors, software, infrastructure, general)
4. If product: What specific product name? (extract from description)

Provide your classification in JSON format. All responses must be in English."""


# ============================================================================
# LLM Chains (with explicit naming for LangSmith)
# ============================================================================

def create_lead_scoring_chain():
    """Create the lead scoring chain with structured output and LangSmith naming.
    
    Uses temperature=0.0 for maximum determinism - same input should produce same output.
    """
    # Force temperature to 0.0 for deterministic scoring
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
