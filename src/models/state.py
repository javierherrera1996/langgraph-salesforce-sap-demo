"""
State schemas for LangGraph workflows.
These TypedDict classes define the explicit state structure for each graph.
"""

from typing import TypedDict, Optional, Annotated
from operator import add


class LeadData(TypedDict, total=False):
    """Salesforce Lead object structure."""
    Id: str
    Name: str
    FirstName: str
    LastName: str
    Company: str
    Email: str
    Phone: str
    Title: str
    Industry: str
    LeadSource: str
    Status: str
    Rating: str
    AnnualRevenue: float
    NumberOfEmployees: int
    Website: str
    Description: str
    OwnerId: str
    CreatedDate: str


class EnrichedData(TypedDict, total=False):
    """SAP-enriched business context."""
    business_partner_id: str
    business_partner_name: str
    credit_rating: str
    payment_terms: str
    total_orders: int
    total_revenue: float
    last_order_date: str
    open_orders: int
    customer_since: str
    industry_segment: str
    account_status: str


class RouteDecision(TypedDict):
    """Routing decision for a lead."""
    owner_id: str
    owner_type: str  # "AE", "SDR", "Nurture"
    priority: str  # "P1", "P2", "P3"
    reason: str


class LLMLeadAnalysis(TypedDict, total=False):
    """LLM analysis results for lead scoring."""
    reasoning: str
    confidence: float
    key_factors: list[str]
    recommended_action: str
    model_used: str


class LeadInputState(TypedDict, total=False):
    """
    Input schema for Lead Qualification graph.
    Only requires lead data and use_llm flag.
    """
    lead: LeadData
    use_llm: bool


class LeadState(TypedDict):
    """
    State schema for Lead Qualification & Routing graph.

    Attributes:
        lead: Raw Salesforce Lead data
        enriched: SAP business context (optional)
        score: Calculated qualification score (0.0 - 1.0)
        route: Routing decision (owner, priority)
        llm_analysis: LLM reasoning and analysis (when use_llm=True)
        use_llm: Whether to use LLM for scoring
        actions_done: List of executed actions for tracing
    """
    lead: LeadData
    enriched: EnrichedData
    score: float
    route: RouteDecision
    llm_analysis: LLMLeadAnalysis
    use_llm: bool
    actions_done: Annotated[list[str], add]


class CaseData(TypedDict, total=False):
    """Salesforce Case object structure."""
    Id: str
    CaseNumber: str
    Subject: str
    Description: str
    Status: str
    Priority: str
    Origin: str
    Type: str
    Reason: str
    ContactId: str
    AccountId: str
    OwnerId: str
    CreatedDate: str
    ClosedDate: str
    IsClosed: bool
    IsEscalated: bool


class KBSuggestion(TypedDict):
    """Knowledge base article suggestion."""
    article_id: str
    title: str
    relevance_score: float
    summary: str
    url: str


class SAPOrderContext(TypedDict, total=False):
    """SAP order context for ticket enrichment."""
    sales_orders: list[dict]
    service_orders: list[dict]
    business_partner_id: str
    has_open_orders: bool
    total_order_value: float


class TicketDecision(TypedDict):
    """Decision for ticket handling."""
    action: str  # "auto_reply", "request_info", "escalate", "assign"
    owner_id: Optional[str]
    response_template: Optional[str]
    escalation_reason: Optional[str]
    priority_change: Optional[str]


class LLMTicketAnalysis(TypedDict, total=False):
    """LLM analysis results for ticket categorization."""
    reasoning: str
    confidence: float
    urgency: str
    sentiment: str
    suggested_response: str
    requires_escalation: bool
    model_used: str


class TicketState(TypedDict):
    """
    State schema for Customer Support Ticket Triage graph.
    
    Attributes:
        case: Raw Salesforce Case data
        category: Classified category (howto, billing, outage, security, other)
        sap_context: SAP order/service context
        kb_suggestions: Relevant knowledge base articles
        decision: Action decision for the ticket
        llm_analysis: LLM reasoning and analysis (when use_llm=True)
        use_llm: Whether to use LLM for categorization
        actions_done: List of executed actions for tracing
    """
    case: CaseData
    category: str
    sap_context: SAPOrderContext
    kb_suggestions: list[KBSuggestion]
    decision: TicketDecision
    llm_analysis: LLMTicketAnalysis
    use_llm: bool
    actions_done: Annotated[list[str], add]


# ============================================================================
# State Factory Functions
# ============================================================================

def create_initial_lead_state(lead: dict, use_llm: bool = True) -> LeadState:
    """
    Create initial state for the lead qualification graph.
    
    Args:
        lead: Raw Salesforce Lead data
        use_llm: Whether to use LLM for scoring (default: True)
        
    Returns:
        Initialized LeadState
    """
    return LeadState(
        lead=lead,
        enriched={},
        score=0.0,
        route={
            "owner_id": "",
            "owner_type": "",
            "priority": "",
            "reason": ""
        },
        llm_analysis={
            "reasoning": "",
            "confidence": 0.0,
            "key_factors": [],
            "recommended_action": "",
            "model_used": ""
        },
        use_llm=use_llm,
        actions_done=[]
    )


def create_initial_ticket_state(case: dict, use_llm: bool = True) -> TicketState:
    """
    Create initial state for the ticket triage graph.
    
    Args:
        case: Raw Salesforce Case data
        use_llm: Whether to use LLM for categorization (default: True)
        
    Returns:
        Initialized TicketState
    """
    return TicketState(
        case=case,
        category="",
        sap_context={
            "sales_orders": [],
            "service_orders": [],
            "business_partner_id": "",
            "has_open_orders": False,
            "total_order_value": 0.0
        },
        kb_suggestions=[],
        decision={
            "action": "",
            "owner_id": None,
            "response_template": None,
            "escalation_reason": None,
            "priority_change": None
        },
        llm_analysis={
            "reasoning": "",
            "confidence": 0.0,
            "urgency": "",
            "sentiment": "",
            "suggested_response": "",
            "requires_escalation": False,
            "model_used": ""
        },
        use_llm=use_llm,
        actions_done=[]
    )


# ============================================================================
# Category and Priority Constants
# ============================================================================

class TicketCategory:
    """Ticket category constants."""
    HOWTO = "howto"
    BILLING = "billing"
    OUTAGE = "outage"
    SECURITY = "security"
    OTHER = "other"
    
    ALL = [HOWTO, BILLING, OUTAGE, SECURITY, OTHER]


class LeadPriority:
    """Lead priority constants."""
    P1 = "P1"  # High priority - Account Executive
    P2 = "P2"  # Medium priority - Sales Dev Rep
    P3 = "P3"  # Low priority - Nurture campaign


class TicketAction:
    """Ticket action constants."""
    AUTO_REPLY = "auto_reply"
    REQUEST_INFO = "request_info"
    ESCALATE = "escalate"
    ASSIGN = "assign"
