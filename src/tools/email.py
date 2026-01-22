"""
Email notifications using Resend.

This module handles email notifications for:
- High-value lead alerts (score >= 60%)
- Product complaint notifications
- IT support redirections

Resend Setup:
1. Create account at https://resend.com
2. Get API key from dashboard
3. Verify your domain or use onboarding@resend.dev for testing
4. Set RESEND_API_KEY in environment
"""

import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Resend configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
DEFAULT_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")  # Email para recibir notificaciones

# Product owners mapping (producto -> email del encargado)
PRODUCT_OWNERS = {
    "switches": os.getenv("PRODUCT_OWNER_SWITCHES", NOTIFICATION_EMAIL),
    "cables": os.getenv("PRODUCT_OWNER_CABLES", NOTIFICATION_EMAIL),
    "connectors": os.getenv("PRODUCT_OWNER_CONNECTORS", NOTIFICATION_EMAIL),
    "software": os.getenv("PRODUCT_OWNER_SOFTWARE", NOTIFICATION_EMAIL),
    "infrastructure": os.getenv("PRODUCT_OWNER_INFRASTRUCTURE", NOTIFICATION_EMAIL),
    "general": os.getenv("PRODUCT_OWNER_GENERAL", NOTIFICATION_EMAIL),
}

# IT Support page URL
IT_SUPPORT_URL = os.getenv("IT_SUPPORT_URL", "https://support.belden.com/it")


def _check_resend_configured() -> bool:
    """Check if Resend is properly configured."""
    if not RESEND_API_KEY:
        logger.warning("⚠️ RESEND_API_KEY not configured - emails will be simulated")
        return False
    return True


def send_email(
    to: str,
    subject: str,
    html_content: str,
    from_email: Optional[str] = None
) -> dict:
    """
    Send an email using Resend API.
    
    Args:
        to: Recipient email address
        subject: Email subject
        html_content: HTML body of the email
        from_email: Sender email (defaults to configured sender)
        
    Returns:
        dict with status and message id
    """
    if not _check_resend_configured():
        # Simulate email for demo
        logger.info(f"📧 [SIMULATED] Email to: {to}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Content preview: {html_content[:100]}...")
        return {
            "success": True,
            "simulated": True,
            "to": to,
            "subject": subject
        }
    
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        
        params = {
            "from": from_email or DEFAULT_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        
        logger.info(f"📧 Email sent successfully to: {to}")
        logger.info(f"   Message ID: {response.get('id', 'N/A')}")
        
        return {
            "success": True,
            "simulated": False,
            "message_id": response.get("id"),
            "to": to,
            "subject": subject
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return {
            "success": False,
            "error": str(e),
            "to": to,
            "subject": subject
        }


def send_high_value_lead_alert(
    lead: dict,
    score: float,
    reasoning: str,
    routing: dict,
    recipient_email: Optional[str] = None
) -> dict:
    """
    Send alert email for high-value leads (score >= 60%).
    
    Args:
        lead: Lead data from Salesforce
        score: Qualification score (0.0 - 1.0)
        reasoning: AI reasoning for the score
        routing: Routing decision (owner_type, priority)
        recipient_email: Override recipient (defaults to NOTIFICATION_EMAIL)
    """
    to_email = recipient_email or NOTIFICATION_EMAIL
    
    if not to_email:
        logger.warning("⚠️ No notification email configured for lead alerts")
        return {"success": False, "error": "No recipient email configured"}
    
    # Determine priority styling
    if score >= 0.75:
        priority_color = "#10B981"  # Green
        priority_label = "🔥 P1 - HOT LEAD"
    elif score >= 0.60:
        priority_color = "#F59E0B"  # Orange
        priority_label = "⚡ P2 - WARM LEAD"
    else:
        priority_color = "#6B7280"
        priority_label = "Lead Alert"
    
    subject = f"{priority_label}: {lead.get('Company', 'Unknown')} - Score {score:.0%}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, {priority_color}, #1E3A5F); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
            .score-box {{ background: white; padding: 20px; text-align: center; border: 3px solid {priority_color}; }}
            .score {{ font-size: 48px; font-weight: bold; color: {priority_color}; }}
            .content {{ background: #F8FAFC; padding: 20px; }}
            .section {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {priority_color}; }}
            .label {{ font-weight: bold; color: #6B7280; font-size: 12px; text-transform: uppercase; }}
            .value {{ font-size: 16px; color: #1E3A5F; }}
            .reasoning {{ background: #FEF3C7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 12px; }}
            .cta {{ display: inline-block; background: {priority_color}; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0;">{priority_label}</h1>
                <p style="margin:5px 0 0 0;">New high-value lead requires attention</p>
            </div>
            
            <div class="score-box">
                <div class="score">{score:.0%}</div>
                <div>Qualification Score</div>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="label">Company</div>
                    <div class="value" style="font-size: 24px;">{lead.get('Company', 'N/A')}</div>
                </div>
                
                <div class="section">
                    <div class="label">Contact</div>
                    <div class="value">{lead.get('FirstName', '')} {lead.get('LastName', '')} - {lead.get('Title', 'N/A')}</div>
                    <div class="value">{lead.get('Email', 'N/A')} | {lead.get('Phone', 'N/A')}</div>
                </div>
                
                <div class="section">
                    <div class="label">Lead Details</div>
                    <table style="width: 100%;">
                        <tr><td class="label">Industry</td><td class="value">{lead.get('Industry', 'N/A')}</td></tr>
                        <tr><td class="label">Rating</td><td class="value">{lead.get('Rating', 'N/A')}</td></tr>
                        <tr><td class="label">Revenue</td><td class="value">${lead.get('AnnualRevenue', 0):,.0f}</td></tr>
                        <tr><td class="label">Employees</td><td class="value">{lead.get('NumberOfEmployees', 'N/A')}</td></tr>
                        <tr><td class="label">Source</td><td class="value">{lead.get('LeadSource', 'N/A')}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <div class="label">Routing Decision</div>
                    <div class="value">Assigned to: <strong>{routing.get('owner_type', 'N/A')}</strong> ({routing.get('priority', 'N/A')})</div>
                </div>
                
                <div class="reasoning">
                    <div class="label">🤖 AI Reasoning</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{reasoning}</div>
                </div>
                
                {f'<div class="section"><div class="label">Description</div><div class="value">{lead.get("Description", "N/A")}</div></div>' if lead.get("Description") else ''}
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="#" class="cta">View in Salesforce →</a>
                </div>
            </div>
            
            <div class="footer">
                <p>Sent by Belden AI Sales Agent</p>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)


def send_product_complaint_alert(
    ticket: dict,
    product_category: str,
    product_name: str,
    analysis: dict,
    recipient_email: Optional[str] = None
) -> dict:
    """
    Send alert email for product complaints to the product owner.
    
    Args:
        ticket: Ticket/case data
        product_category: Category of product (switches, cables, etc.)
        product_name: Specific product name if identified
        analysis: AI analysis results
        recipient_email: Override recipient (defaults to product owner)
    """
    # Get product owner email
    to_email = recipient_email or PRODUCT_OWNERS.get(product_category.lower(), NOTIFICATION_EMAIL)
    
    if not to_email:
        logger.warning(f"⚠️ No email configured for product: {product_category}")
        return {"success": False, "error": "No recipient email configured"}
    
    sentiment = analysis.get("sentiment", "neutral")
    urgency = analysis.get("urgency", "medium")
    
    # Determine urgency color
    urgency_colors = {
        "critical": "#DC2626",
        "high": "#F59E0B",
        "medium": "#3B82F6",
        "low": "#10B981"
    }
    urgency_color = urgency_colors.get(urgency, "#6B7280")
    
    subject = f"⚠️ Product Complaint: {product_name or product_category.upper()} - {ticket.get('Subject', 'No Subject')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #EF4444, #B91C1C); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            .urgency-badge {{ background: {urgency_color}; color: white; }}
            .product-badge {{ background: #1E3A5F; color: white; }}
            .content {{ background: #F8FAFC; padding: 20px; }}
            .section {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #EF4444; }}
            .label {{ font-weight: bold; color: #6B7280; font-size: 12px; text-transform: uppercase; }}
            .value {{ font-size: 16px; color: #1E3A5F; }}
            .complaint-box {{ background: #FEE2E2; padding: 15px; border-radius: 8px; border: 1px solid #EF4444; }}
            .reasoning {{ background: #FEF3C7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0;">⚠️ Product Complaint Alert</h1>
                <p style="margin:5px 0 0 0;">A customer has reported an issue with a Belden product</p>
            </div>
            
            <div class="content">
                <div style="text-align: center; margin-bottom: 20px;">
                    <span class="badge product-badge">📦 {product_category.upper()}</span>
                    <span class="badge urgency-badge">🔥 {urgency.upper()}</span>
                </div>
                
                <div class="section">
                    <div class="label">Product Identified</div>
                    <div class="value" style="font-size: 24px;">{product_name or f"General {product_category.title()}"}</div>
                </div>
                
                <div class="section">
                    <div class="label">Case Information</div>
                    <table style="width: 100%;">
                        <tr><td class="label">Case #</td><td class="value">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</td></tr>
                        <tr><td class="label">Subject</td><td class="value">{ticket.get('Subject', 'N/A')}</td></tr>
                        <tr><td class="label">Priority</td><td class="value">{ticket.get('Priority', 'N/A')}</td></tr>
                        <tr><td class="label">Origin</td><td class="value">{ticket.get('Origin', 'N/A')}</td></tr>
                        <tr><td class="label">Customer Sentiment</td><td class="value">{sentiment.capitalize()}</td></tr>
                    </table>
                </div>
                
                <div class="complaint-box">
                    <div class="label">📝 Complaint Details</div>
                    <div style="margin-top: 10px; white-space: pre-wrap;">{ticket.get('Description', 'No description provided')}</div>
                </div>
                
                <div class="reasoning">
                    <div class="label">🤖 AI Analysis</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{analysis.get('reasoning', 'No analysis available')}</div>
                </div>
                
                {f'<div class="section"><div class="label">Suggested Response</div><div class="value">{analysis.get("suggested_response", "N/A")}</div></div>' if analysis.get("suggested_response") else ''}
            </div>
            
            <div class="footer">
                <p>This complaint requires your attention as the {product_category.title()} Product Owner</p>
                <p>Sent by Belden AI Sales Agent | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)


def get_it_support_redirect() -> dict:
    """
    Get IT support redirect information.
    
    Returns:
        dict with redirect URL and message
    """
    return {
        "action": "redirect_to_it",
        "url": IT_SUPPORT_URL,
        "message": f"Este ticket ha sido identificado como un tema de IT/Soporte técnico. Por favor visite: {IT_SUPPORT_URL}",
        "instructions": [
            "1. Visite el portal de IT Support",
            "2. Inicie sesión con sus credenciales corporativas",
            "3. Abra un nuevo ticket en la categoría correspondiente",
            "4. Incluya el número de referencia original del caso"
        ]
    }
