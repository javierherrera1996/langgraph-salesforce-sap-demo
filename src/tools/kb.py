"""
Knowledge Base Tools
Deterministic knowledge base lookup and ticket categorization.
No LLM decisions - rule-based pattern matching.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Knowledge Base Articles (Mock Data)
# ============================================================================

KB_ARTICLES = [
    {
        "article_id": "KB0001",
        "title": "How to Reset Your Password",
        "category": "howto",
        "keywords": ["password", "reset", "forgot", "login", "access", "locked"],
        "summary": "Step-by-step guide to reset your account password via email verification.",
        "url": "/kb/articles/KB0001",
        "relevance_base": 0.9
    },
    {
        "article_id": "KB0002",
        "title": "Two-Factor Authentication Setup",
        "category": "howto",
        "keywords": ["2fa", "two-factor", "mfa", "authentication", "security", "setup"],
        "summary": "Guide to enabling and configuring two-factor authentication for your account.",
        "url": "/kb/articles/KB0002",
        "relevance_base": 0.85
    },
    {
        "article_id": "KB0003",
        "title": "Understanding Your Invoice",
        "category": "billing",
        "keywords": ["invoice", "bill", "charge", "payment", "price", "cost", "fee"],
        "summary": "Explanation of invoice line items, taxes, and payment terms.",
        "url": "/kb/articles/KB0003",
        "relevance_base": 0.88
    },
    {
        "article_id": "KB0004",
        "title": "Payment Methods and Options",
        "category": "billing",
        "keywords": ["payment", "credit card", "bank", "wire", "ach", "method"],
        "summary": "Available payment methods including credit card, ACH, and wire transfer.",
        "url": "/kb/articles/KB0004",
        "relevance_base": 0.85
    },
    {
        "article_id": "KB0005",
        "title": "System Status and Monitoring",
        "category": "outage",
        "keywords": ["status", "down", "outage", "incident", "monitoring", "uptime"],
        "summary": "How to check system status and subscribe to incident notifications.",
        "url": "/kb/articles/KB0005",
        "relevance_base": 0.9
    },
    {
        "article_id": "KB0006",
        "title": "Incident Response Procedures",
        "category": "outage",
        "keywords": ["incident", "response", "sla", "recovery", "emergency", "urgent"],
        "summary": "Our incident response procedures and SLA commitments.",
        "url": "/kb/articles/KB0006",
        "relevance_base": 0.87
    },
    {
        "article_id": "KB0007",
        "title": "Security Best Practices",
        "category": "security",
        "keywords": ["security", "breach", "hack", "unauthorized", "suspicious", "protect"],
        "summary": "Security best practices and how to report suspicious activity.",
        "url": "/kb/articles/KB0007",
        "relevance_base": 0.92
    },
    {
        "article_id": "KB0008",
        "title": "Data Privacy and Compliance",
        "category": "security",
        "keywords": ["privacy", "gdpr", "compliance", "data", "personal", "deletion"],
        "summary": "Our data privacy policies and compliance certifications.",
        "url": "/kb/articles/KB0008",
        "relevance_base": 0.88
    },
    {
        "article_id": "KB0009",
        "title": "Getting Started Guide",
        "category": "howto",
        "keywords": ["start", "begin", "new", "onboarding", "tutorial", "guide"],
        "summary": "Complete onboarding guide for new users.",
        "url": "/kb/articles/KB0009",
        "relevance_base": 0.8
    },
    {
        "article_id": "KB0010",
        "title": "API Documentation Overview",
        "category": "howto",
        "keywords": ["api", "integration", "developer", "documentation", "endpoint"],
        "summary": "Overview of our REST API and integration capabilities.",
        "url": "/kb/articles/KB0010",
        "relevance_base": 0.75
    }
]


# ============================================================================
# Category Classification Patterns
# ============================================================================

CATEGORY_PATTERNS = {
    "security": {
        "patterns": [
            r"\b(hack|breach|unauthorized|suspicious|security)\b",
            r"\b(attack|compromise|intrusion|malware|virus)\b",
            r"\b(phishing|scam|fraud|identity)\b",
            r"\bunauthorized\s+access\b",
            r"\bsecurity\s+(concern|issue|problem|alert)\b",
        ],
        "priority_boost": True,
        "weight": 1.0
    },
    "outage": {
        "patterns": [
            r"\b(down|outage|unavailable|not\s+working)\b",
            r"\b(error|crash|fail|broken)\b",
            r"\b(urgent|emergency|critical|production)\b",
            r"\bsystem\s+(down|not\s+responding)\b",
            r"\bcan'?t\s+(access|connect|reach|load)\b",
        ],
        "priority_boost": True,
        "weight": 0.95
    },
    "billing": {
        "patterns": [
            r"\b(invoice|bill|charge|payment)\b",
            r"\b(price|cost|fee|discount)\b",
            r"\b(refund|credit|overcharge)\b",
            r"\b(subscription|renewal|cancel)\b",
            r"\bdiscrepancy\b",
        ],
        "priority_boost": False,
        "weight": 0.85
    },
    "howto": {
        "patterns": [
            r"\b(how\s+(do|can|to)|what\s+is)\b",
            r"\b(help|guide|tutorial|instructions)\b",
            r"\b(setup|configure|enable|disable)\b",
            r"\b(password|login|account|profile)\b",
            r"\bstep\s*-?\s*by\s*-?\s*step\b",
        ],
        "priority_boost": False,
        "weight": 0.7
    }
}


# ============================================================================
# Response Templates
# ============================================================================

RESPONSE_TEMPLATES = {
    "howto": {
        "auto_reply": """Thank you for contacting support.

Based on your question, I found some helpful resources that may assist you:

{kb_articles}

If these articles don't answer your question, please reply to this message and a support representative will follow up within 24 hours.

Best regards,
Support Team""",
        "info_request": None
    },
    "billing": {
        "auto_reply": None,
        "info_request": """Thank you for contacting our billing department.

To assist you with your billing inquiry, please provide:
1. Invoice number or date range
2. Specific line items in question
3. Your expected amount vs. charged amount

Our billing team will review your case within 1-2 business days.

Best regards,
Billing Support"""
    },
    "outage": {
        "auto_reply": None,
        "info_request": None,
        "escalation": """[ESCALATED - SYSTEM OUTAGE]

This ticket has been automatically escalated to our incident response team.

Current system status: https://status.example.com
Incident updates will be posted to the status page.

If this is affecting production systems, our on-call engineer has been notified.

Ticket Priority: HIGH"""
    },
    "security": {
        "auto_reply": None,
        "info_request": None,
        "escalation": """[ESCALATED - SECURITY CONCERN]

This ticket has been automatically escalated to our Security Operations team.

DO NOT share any sensitive information in this ticket.

A security analyst will contact you within 1 hour during business hours.
For critical security issues, call our security hotline: 1-800-XXX-XXXX

Ticket Priority: CRITICAL"""
    },
    "other": {
        "auto_reply": None,
        "info_request": """Thank you for contacting support.

We've received your request and need some additional information to assist you:
1. Please describe the issue in more detail
2. What were you trying to accomplish?
3. Any error messages or screenshots would be helpful

A support representative will follow up within 24-48 hours.

Best regards,
Support Team"""
    }
}


# ============================================================================
# Classification Functions
# ============================================================================

def categorize_ticket(subject: str, description: str) -> dict:
    """
    Categorize a support ticket based on content analysis.
    
    Uses deterministic pattern matching - no LLM decisions.
    
    Args:
        subject: Ticket subject line
        description: Ticket description/body
        
    Returns:
        Category result with confidence and matched patterns
    """
    logger.info("Categorizing ticket")
    
    # Combine and normalize text
    text = f"{subject} {description}".lower()
    
    category_scores = {}
    matched_patterns = {}
    
    for category, config in CATEGORY_PATTERNS.items():
        score = 0.0
        matches = []
        
        for pattern in config["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1.0
                matches.append(pattern)
        
        if matches:
            # Normalize by number of patterns and apply weight
            normalized = (score / len(config["patterns"])) * config["weight"]
            category_scores[category] = normalized
            matched_patterns[category] = matches
    
    # Determine best category
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category]
    else:
        best_category = "other"
        confidence = 0.5
    
    result = {
        "category": best_category,
        "confidence": round(confidence, 3),
        "all_scores": category_scores,
        "matched_patterns": matched_patterns.get(best_category, []),
        "requires_escalation": CATEGORY_PATTERNS.get(
            best_category, {}
        ).get("priority_boost", False)
    }
    
    logger.info(f"Ticket categorized as: {result['category']} ({result['confidence']:.2f})")
    return result


def search_knowledge_base(
    query: str,
    category: Optional[str] = None,
    limit: int = 3
) -> list[dict]:
    """
    Search knowledge base for relevant articles.
    
    Uses keyword matching - deterministic results.
    
    Args:
        query: Search query (typically ticket subject + description)
        category: Optional category filter
        limit: Maximum articles to return
        
    Returns:
        List of relevant KB articles with relevance scores
    """
    logger.info(f"Searching KB for: {query[:50]}...")
    
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    scored_articles = []
    
    for article in KB_ARTICLES:
        # Filter by category if specified
        if category and article["category"] != category:
            continue
        
        # Calculate keyword match score
        keyword_matches = sum(
            1 for kw in article["keywords"]
            if kw in query_lower or any(kw in word for word in query_words)
        )
        
        if keyword_matches > 0:
            # Relevance = base relevance * keyword match ratio
            match_ratio = keyword_matches / len(article["keywords"])
            relevance = article["relevance_base"] * (0.5 + 0.5 * match_ratio)
            
            scored_articles.append({
                "article_id": article["article_id"],
                "title": article["title"],
                "relevance_score": round(relevance, 3),
                "summary": article["summary"],
                "url": article["url"],
                "keyword_matches": keyword_matches
            })
    
    # Sort by relevance and limit
    scored_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
    results = scored_articles[:limit]
    
    logger.info(f"Found {len(results)} relevant KB articles")
    return results


def get_response_template(category: str, action: str) -> Optional[str]:
    """
    Get response template for a category and action.
    
    Args:
        category: Ticket category
        action: Action type (auto_reply, info_request, escalation)
        
    Returns:
        Response template string or None
    """
    templates = RESPONSE_TEMPLATES.get(category, RESPONSE_TEMPLATES["other"])
    return templates.get(action)


def format_kb_articles_for_response(articles: list[dict]) -> str:
    """
    Format KB articles for inclusion in response template.
    
    Args:
        articles: List of KB article dictionaries
        
    Returns:
        Formatted string for template insertion
    """
    if not articles:
        return "No specific articles found. Please describe your question in more detail."
    
    lines = []
    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. **{article['title']}**")
        lines.append(f"   {article['summary']}")
        lines.append(f"   Read more: {article['url']}")
        lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# Decision Functions
# ============================================================================

def determine_ticket_action(category: str, kb_suggestions: list[dict]) -> dict:
    """
    Determine the action to take for a ticket.
    
    Deterministic decision logic based on category:
    - howto: Auto-reply with KB articles
    - billing: Request more information
    - outage/security: Escalate immediately
    - other: Request more information
    
    Args:
        category: Ticket category
        kb_suggestions: Available KB articles
        
    Returns:
        Decision dictionary with action and details
    """
    logger.info(f"Determining action for category: {category}")
    
    decision = {
        "action": "",
        "owner_id": None,
        "response_template": None,
        "escalation_reason": None,
        "priority_change": None
    }
    
    if category == "howto" and kb_suggestions:
        # Auto-reply with KB articles
        template = get_response_template("howto", "auto_reply")
        if template:
            kb_text = format_kb_articles_for_response(kb_suggestions)
            decision["action"] = "auto_reply"
            decision["response_template"] = template.format(kb_articles=kb_text)
    
    elif category == "billing":
        # Request additional billing information
        decision["action"] = "request_info"
        decision["response_template"] = get_response_template("billing", "info_request")
    
    elif category in ("outage", "security"):
        # Escalate critical issues
        decision["action"] = "escalate"
        decision["response_template"] = get_response_template(category, "escalation")
        decision["escalation_reason"] = f"Auto-escalated: {category.upper()} category detected"
        decision["priority_change"] = "High" if category == "outage" else "Critical"
    
    else:
        # Default: request more information
        decision["action"] = "request_info"
        decision["response_template"] = get_response_template("other", "info_request")
    
    logger.info(f"Ticket action determined: {decision['action']}")
    return decision
