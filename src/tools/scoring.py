"""
Lead Scoring Tools
Deterministic scoring functions for lead qualification.
No LLM decisions - pure rule-based scoring.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Scoring Weights Configuration
# ============================================================================

SCORING_WEIGHTS = {
    # Company size score (by employee count)
    "employees": {
        "ranges": [
            (1000, 1.0),    # Enterprise
            (500, 0.9),     # Large
            (100, 0.7),     # Mid-market
            (50, 0.5),      # SMB
            (10, 0.3),      # Small
            (0, 0.1),       # Micro
        ],
        "weight": 0.20
    },
    # Annual revenue score
    "revenue": {
        "ranges": [
            (10000000, 1.0),   # $10M+
            (5000000, 0.9),    # $5M+
            (1000000, 0.7),    # $1M+
            (500000, 0.5),     # $500K+
            (100000, 0.3),     # $100K+
            (0, 0.1),          # Below
        ],
        "weight": 0.20
    },
    # Lead rating score
    "rating": {
        "values": {
            "Hot": 1.0,
            "Warm": 0.7,
            "Cold": 0.3,
        },
        "default": 0.5,
        "weight": 0.25
    },
    # Lead source score
    "source": {
        "values": {
            "Customer Referral": 1.0,
            "Partner": 0.9,
            "Employee Referral": 0.85,
            "Web": 0.7,
            "Webinar": 0.65,
            "Trade Show": 0.6,
            "Advertisement": 0.5,
            "Cold Call": 0.4,
            "Other": 0.3,
        },
        "default": 0.5,
        "weight": 0.15
    },
    # Title/seniority score
    "title": {
        "keywords": {
            "ceo": 1.0,
            "cto": 1.0,
            "cfo": 1.0,
            "cio": 1.0,
            "chief": 1.0,
            "president": 0.95,
            "owner": 0.95,
            "founder": 0.95,
            "vp": 0.85,
            "vice president": 0.85,
            "director": 0.75,
            "head": 0.75,
            "senior": 0.65,
            "manager": 0.55,
            "lead": 0.50,
            "engineer": 0.40,
            "analyst": 0.35,
        },
        "default": 0.3,
        "weight": 0.10
    },
    # SAP enrichment bonus
    "sap_enrichment": {
        "has_bp": 0.05,          # Has existing business partner
        "good_credit": 0.05,     # A or A+ credit rating
        "active_customer": 0.05, # Active account status
        "weight": 1.0            # Applied as bonus
    }
}


# ============================================================================
# Score Calculation Functions
# ============================================================================

def _score_range(value: float, ranges: list[tuple[float, float]]) -> float:
    """Score a numeric value against range thresholds."""
    for threshold, score in ranges:
        if value >= threshold:
            return score
    return 0.0


def _score_title(title: str) -> float:
    """Score a job title based on seniority keywords."""
    if not title:
        return SCORING_WEIGHTS["title"]["default"]
    
    title_lower = title.lower()
    keywords = SCORING_WEIGHTS["title"]["keywords"]
    
    best_score = 0.0
    for keyword, score in keywords.items():
        if keyword in title_lower:
            best_score = max(best_score, score)
    
    return best_score if best_score > 0 else SCORING_WEIGHTS["title"]["default"]


def calculate_lead_score(lead: dict, enriched: Optional[dict] = None) -> dict:
    """
    Calculate lead qualification score.
    
    This is a deterministic, rule-based scoring function.
    No LLM decisions - pure business logic.
    
    Args:
        lead: Salesforce Lead data
        enriched: Optional SAP enrichment data
        
    Returns:
        Dictionary with total score and component breakdown
    """
    logger.info(f"Calculating score for lead: {lead.get('Id', 'unknown')}")
    
    components = {}
    
    # Employee count score
    employees = lead.get("NumberOfEmployees", 0) or 0
    emp_config = SCORING_WEIGHTS["employees"]
    emp_score = _score_range(employees, emp_config["ranges"])
    components["employees"] = {
        "value": employees,
        "score": emp_score,
        "weighted": emp_score * emp_config["weight"]
    }
    
    # Annual revenue score
    revenue = lead.get("AnnualRevenue", 0) or 0
    rev_config = SCORING_WEIGHTS["revenue"]
    rev_score = _score_range(revenue, rev_config["ranges"])
    components["revenue"] = {
        "value": revenue,
        "score": rev_score,
        "weighted": rev_score * rev_config["weight"]
    }
    
    # Rating score
    rating = lead.get("Rating", "")
    rat_config = SCORING_WEIGHTS["rating"]
    rat_score = rat_config["values"].get(rating, rat_config["default"])
    components["rating"] = {
        "value": rating,
        "score": rat_score,
        "weighted": rat_score * rat_config["weight"]
    }
    
    # Lead source score
    source = lead.get("LeadSource", "")
    src_config = SCORING_WEIGHTS["source"]
    src_score = src_config["values"].get(source, src_config["default"])
    components["source"] = {
        "value": source,
        "score": src_score,
        "weighted": src_score * src_config["weight"]
    }
    
    # Title score
    title = lead.get("Title", "")
    title_score = _score_title(title)
    title_config = SCORING_WEIGHTS["title"]
    components["title"] = {
        "value": title,
        "score": title_score,
        "weighted": title_score * title_config["weight"]
    }
    
    # Base score (sum of weighted components)
    base_score = sum(c["weighted"] for c in components.values())
    
    # SAP enrichment bonus
    sap_bonus = 0.0
    if enriched:
        sap_config = SCORING_WEIGHTS["sap_enrichment"]
        
        # Has business partner
        if enriched.get("business_partner_id"):
            sap_bonus += sap_config["has_bp"]
            
        # Good credit rating
        if enriched.get("credit_rating") in ("A", "A+"):
            sap_bonus += sap_config["good_credit"]
            
        # Active customer
        if enriched.get("account_status") == "Active":
            sap_bonus += sap_config["active_customer"]
    
    components["sap_bonus"] = {
        "value": "enriched" if enriched else "none",
        "score": sap_bonus,
        "weighted": sap_bonus
    }
    
    # Final score (capped at 1.0)
    total_score = min(base_score + sap_bonus, 1.0)
    
    result = {
        "total_score": round(total_score, 4),
        "base_score": round(base_score, 4),
        "sap_bonus": round(sap_bonus, 4),
        "components": components
    }
    
    logger.info(f"Lead score calculated: {result['total_score']}")
    return result


def determine_routing(score: float) -> dict:
    """
    Determine lead routing based on score.
    
    Deterministic routing logic:
    - Score >= 0.75: Account Executive (P1)
    - Score 0.45-0.74: Sales Dev Rep (P2)
    - Score < 0.45: Nurture Campaign (P3)
    
    Args:
        score: Qualification score (0.0 - 1.0)
        
    Returns:
        Routing decision dictionary
    """
    logger.info(f"Determining routing for score: {score}")
    
    if score >= 0.75:
        routing = {
            "owner_type": "AE",
            "priority": "P1",
            "reason": f"High-value lead (score: {score:.2f}) - immediate AE engagement"
        }
    elif score >= 0.45:
        routing = {
            "owner_type": "SDR",
            "priority": "P2",
            "reason": f"Qualified lead (score: {score:.2f}) - SDR qualification needed"
        }
    else:
        routing = {
            "owner_type": "Nurture",
            "priority": "P3",
            "reason": f"Early-stage lead (score: {score:.2f}) - nurture campaign"
        }
    
    logger.info(f"Routing decision: {routing['owner_type']} / {routing['priority']}")
    return routing


# ============================================================================
# Industry-Specific Adjustments
# ============================================================================

INDUSTRY_MULTIPLIERS = {
    "Technology": 1.1,
    "Software": 1.1,
    "Financial Services": 1.15,
    "Healthcare": 1.1,
    "Manufacturing": 1.05,
    "Retail": 1.0,
    "Education": 0.95,
    "Government": 1.0,
    "Non-Profit": 0.85,
}


def apply_industry_adjustment(base_score: float, industry: str) -> float:
    """
    Apply industry-specific score adjustment.
    
    Args:
        base_score: Base qualification score
        industry: Lead's industry
        
    Returns:
        Adjusted score (capped at 1.0)
    """
    multiplier = INDUSTRY_MULTIPLIERS.get(industry, 1.0)
    adjusted = base_score * multiplier
    return min(adjusted, 1.0)
