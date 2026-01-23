"""
Email notifications using Resend.

This module handles email notifications for:
- High-value lead alerts (score >= 60%)
- Product complaint notifications
- IT support redirections
- AI analysis emails for all tickets

Resend Setup:
1. Create account at https://resend.com
2. Get API key from dashboard
3. Verify your domain or use onboarding@resend.dev for testing
4. Set RESEND_API_KEY in environment

See docs/RESEND_SETUP.md for detailed setup instructions.
"""

import logging
from typing import Optional
from datetime import datetime

from src.config import get_resend_config

logger = logging.getLogger(__name__)


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
    config = get_resend_config()
    
    # Log configuration status
    api_key_preview = config.api_key[:20] + "..." if config.api_key and len(config.api_key) > 20 else (config.api_key or "NOT SET")
    logger.info(f"📧 Email send attempt - Config check:")
    logger.info(f"   API Key: {api_key_preview}")
    logger.info(f"   API Key length: {len(config.api_key) if config.api_key else 0}")
    logger.info(f"   API Key configured: {config.is_configured}")
    logger.info(f"   From email: {config.from_email}")
    logger.info(f"   To email: {to}")
    
    if not config.is_configured:
        # Simulate email for demo
        logger.warning("⚠️ Resend not configured - simulating email")
        logger.warning(f"   API Key: {config.api_key[:20] if config.api_key else 'NOT SET'}...")
        logger.info(f"📧 [SIMULATED] Email to: {to}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Content preview: {html_content[:100]}...")
        return {
            "success": True,
            "simulated": True,
            "to": to,
            "subject": subject,
            "message": "Email simulated (Resend not configured)"
        }
    
    try:
        import requests
        
        # Use Resend REST API directly
        api_url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": from_email or config.from_email,
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
            "html": html_content
        }
        
        # Log request details for debugging
        logger.info(f"📧 Sending email via Resend API")
        logger.info(f"   URL: {api_url}")
        logger.info(f"   Method: POST")
        logger.info(f"   From: {from_email or config.from_email}")
        logger.info(f"   To: {to}")
        logger.info(f"   Subject: {subject}")
        
        # Make POST request explicitly
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=30,
            allow_redirects=False  # Prevent redirects that might change method
        )
        
        # Log response details
        logger.info(f"   Response Status: {response.status_code}")
        logger.info(f"   Response Method: {response.request.method if hasattr(response, 'request') else 'N/A'}")
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get("id", "N/A")
            logger.info(f"✅ Email sent successfully to: {to}")
            logger.info(f"   Message ID: {message_id}")
            
            return {
                "success": True,
                "simulated": False,
                "message_id": message_id,
                "to": to,
                "subject": subject,
                "from": from_email or config.from_email
            }
        else:
            # Try to parse error response
            try:
                error_data = response.json() if response.content else {}
            except:
                error_data = {"raw_response": response.text}
            
            error_msg = error_data.get("message", f"HTTP {response.status_code}")
            error_name = error_data.get("name", "unknown_error")
            
            logger.error(f"❌ Failed to send email to {to}")
            logger.error(f"   Status Code: {response.status_code}")
            logger.error(f"   Error Name: {error_name}")
            logger.error(f"   Error Message: {error_msg}")
            logger.error(f"   Full Response: {response.text}")
            logger.error(f"   Request Method Used: {response.request.method if hasattr(response, 'request') else 'N/A'}")
            
            # Special handling for restricted API key
            if error_name == "restricted_api_key":
                logger.error("   ⚠️ API key is restricted. Create a new one at https://resend.com/api-keys")
            
            return {
                "success": False,
                "error": error_msg,
                "error_name": error_name,
                "error_details": error_data,
                "status_code": response.status_code,
                "to": to,
                "subject": subject
            }
        
    except ImportError:
        logger.error("❌ Requests package not installed. Run: pip install requests")
        return {
            "success": False,
            "error": "Requests package not installed",
            "to": to,
            "subject": subject
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error sending email to {to}: {e}")
        logger.exception("Full traceback:")
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "to": to,
            "subject": subject
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email to {to}: {e}")
        logger.exception("Full traceback:")
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
    enriched: Optional[dict] = None,
    recipient_email: Optional[str] = None
) -> dict:
    """
    Send alert email for high-value leads (score >= 60%).
    
    Args:
        lead: Lead data from Salesforce
        score: Qualification score (0.0 - 1.0)
        reasoning: AI reasoning for the score
        routing: Routing decision (owner_type, priority)
        recipient_email: Override recipient (defaults to notification_email from config)
    """
    config = get_resend_config()
    to_email = recipient_email or config.notification_email or config.from_email
    
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
    
    # Format lead name
    lead_name = f"{lead.get('FirstName', '')} {lead.get('LastName', '')}".strip() or lead.get('Name', 'N/A')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1F2937; background: #F3F4F6; }}
            .email-wrapper {{ max-width: 700px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, {priority_color} 0%, #1E3A5F 100%); color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px; }}
            .header p {{ font-size: 16px; opacity: 0.95; }}
            .score-hero {{ background: white; margin: -30px 30px 0; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; }}
            .score-number {{ font-size: 72px; font-weight: 800; color: {priority_color}; line-height: 1; margin-bottom: 10px; }}
            .score-label {{ font-size: 14px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
            .content {{ padding: 40px 30px; background: #F9FAFB; }}
            .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 5px solid {priority_color}; }}
            .section-title {{ font-size: 13px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 12px; margin-top: 15px; }}
            .info-label {{ font-size: 13px; color: #6B7280; font-weight: 600; }}
            .info-value {{ font-size: 15px; color: #1F2937; font-weight: 500; }}
            .highlight-box {{ background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #3B82F6; }}
            .ai-box {{ background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #F59E0B; }}
            .ai-title {{ font-size: 15px; font-weight: 700; color: #92400E; margin-bottom: 12px; }}
            .ai-content {{ font-size: 14px; color: #78350F; line-height: 1.8; white-space: pre-wrap; }}
            .next-steps {{ background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #10B981; }}
            .next-steps ul {{ margin: 15px 0 0 20px; }}
            .next-steps li {{ margin-bottom: 12px; font-size: 14px; color: #065F46; line-height: 1.7; }}
            .cta-button {{ display: inline-block; background: {priority_color}; color: white; padding: 16px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px; margin: 20px 0; transition: transform 0.2s; }}
            .cta-button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
            .footer {{ background: #1E3A5F; color: white; padding: 30px; text-align: center; }}
            .footer p {{ margin: 5px 0; font-size: 13px; opacity: 0.9; }}
            .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; margin: 5px 5px 5px 0; }}
            .badge-primary {{ background: {priority_color}; color: white; }}
            .badge-secondary {{ background: #E5E7EB; color: #374151; }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>{priority_label}</h1>
                <p>New High-Value Lead Requires Immediate Attention</p>
            </div>
            
            <div class="score-hero">
                <div class="score-number">{score:.0%}</div>
                <div class="score-label">Qualification Score</div>
            </div>
            
            <div class="content">
                <!-- Company & Contact Section -->
                <div class="section">
                    <div class="section-title">🏢 Company Information</div>
                    <div style="font-size: 26px; font-weight: 700; color: #1E3A5F; margin-bottom: 20px;">{lead.get('Company', 'N/A')}</div>
                    <div class="info-grid">
                        <div class="info-label">Contact Name:</div>
                        <div class="info-value" style="font-size: 18px; font-weight: 600;">{lead_name}</div>
                        <div class="info-label">Job Title:</div>
                        <div class="info-value">{lead.get('Title', 'N/A')}</div>
                        <div class="info-label">Email:</div>
                        <div class="info-value"><a href="mailto:{lead.get('Email', '')}" style="color: #3B82F6; text-decoration: none;">{lead.get('Email', 'N/A')}</a></div>
                        <div class="info-label">Phone:</div>
                        <div class="info-value"><a href="tel:{lead.get('Phone', '')}" style="color: #3B82F6; text-decoration: none;">{lead.get('Phone', 'N/A')}</a></div>
                    </div>
                </div>
                
                <!-- Lead Details Section -->
                <div class="section">
                    <div class="section-title">📊 Lead Details</div>
                    <div class="info-grid">
                        <div class="info-label">Industry:</div>
                        <div class="info-value"><span class="badge badge-secondary">{lead.get('Industry', 'N/A')}</span></div>
                        <div class="info-label">Rating:</div>
                        <div class="info-value"><span class="badge badge-primary">{lead.get('Rating', 'N/A')}</span></div>
                        <div class="info-label">Annual Revenue:</div>
                        <div class="info-value" style="font-size: 18px; font-weight: 700; color: #10B981;">${lead.get('AnnualRevenue', 0):,.0f}</div>
                        <div class="info-label">Employees:</div>
                        <div class="info-value">{lead.get('NumberOfEmployees', 'N/A'):,} employees</div>
                        <div class="info-label">Lead Source:</div>
                        <div class="info-value">{lead.get('LeadSource', 'N/A')}</div>
                        <div class="info-label">Lead ID:</div>
                        <div class="info-value" style="font-family: monospace; font-size: 13px;">{lead.get('Id', 'N/A')}</div>
                    </div>
                </div>
                
                <!-- Routing Decision -->
                <div class="section">
                    <div class="section-title">🎯 Routing Decision</div>
                    <div style="margin-top: 15px;">
                        <div style="font-size: 18px; font-weight: 700; color: #1E3A5F; margin-bottom: 10px;">
                            Assigned to: <span style="color: {priority_color};">{routing.get('owner_type', 'N/A')}</span> 
                            <span class="badge badge-primary">{routing.get('priority', 'N/A')}</span>
                        </div>
                        <div style="font-size: 14px; color: #6B7280; line-height: 1.7; margin-top: 10px; padding: 15px; background: #F9FAFB; border-radius: 8px;">
                            {routing.get('reason', 'N/A')}
                        </div>
                    </div>
                </div>
                
                {f'''
                <!-- SAP Business Context -->
                <div class="section" style="border-left-color: #10B981; background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);">
                    <div class="section-title">📊 SAP Business Context</div>
                    <div class="info-grid" style="margin-top: 15px;">
                        <div class="info-label">Business Partner ID:</div>
                        <div class="info-value" style="font-family: monospace; font-size: 13px;">{enriched.get('business_partner_id', 'N/A')}</div>
                        <div class="info-label">Total Orders:</div>
                        <div class="info-value" style="font-size: 18px; font-weight: 700; color: #10B981;">{enriched.get('total_orders', 0):,}</div>
                        <div class="info-label">Lifetime Revenue:</div>
                        <div class="info-value" style="font-size: 18px; font-weight: 700; color: #10B981;">${enriched.get('total_revenue', 0):,.2f}</div>
                        <div class="info-label">Credit Rating:</div>
                        <div class="info-value"><span class="badge badge-primary">{enriched.get('credit_rating', 'N/A')}</span></div>
                        <div class="info-label">Last Order Date:</div>
                        <div class="info-value">{enriched.get('last_order_date', 'N/A')}</div>
                    </div>
                    <div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px; border: 1px solid #10B981;">
                        <div style="font-size: 13px; color: #065F46; font-weight: 600;">✅ Existing Customer</div>
                        <div style="font-size: 12px; color: #047857; margin-top: 5px;">This company has an established relationship with Belden through SAP</div>
                    </div>
                </div>
                ''' if enriched and enriched.get('business_partner_id') else ''}
                
                <!-- Lead Description -->
                {f'''
                <div class="section">
                    <div class="section-title">📝 Lead Description</div>
                    <div style="white-space: pre-wrap; font-size: 15px; line-height: 1.8; color: #374151; padding: 15px; background: #F9FAFB; border-radius: 8px; margin-top: 15px;">{lead.get("Description", "N/A")}</div>
                </div>
                ''' if lead.get("Description") else ''}
                
                <!-- AI Analysis -->
                <div class="ai-box">
                    <div class="ai-title">🤖 AI Analysis & Reasoning</div>
                    <div class="ai-content">{reasoning}</div>
                </div>
                
                <!-- Next Steps -->
                <div class="next-steps">
                    <div class="section-title" style="color: #065F46; margin-bottom: 15px;">🎯 Recommended Next Steps</div>
                    <ul>
                        <li><strong>Immediate Action:</strong> Review complete lead information and opportunity details above</li>
                        <li><strong>Within 24 Hours:</strong> Contact {lead_name} at <a href="mailto:{lead.get('Email', '')}" style="color: #059669; font-weight: 600;">{lead.get('Email', 'provided email')}</a> or <a href="tel:{lead.get('Phone', '')}" style="color: #059669; font-weight: 600;">{lead.get('Phone', 'provided phone')}</a></li>
                        <li><strong>Follow-up Strategy:</strong> Use AI recommendations above to tailor your approach and messaging</li>
                        <li><strong>Salesforce Update:</strong> Record all interactions and update opportunity status after contact</li>
                    </ul>
                </div>
                
                <!-- CTA Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://your-salesforce-instance.com/{lead.get('Id', '')}" class="cta-button">View Full Lead in Salesforce →</a>
                </div>
            </div>
            
            <div class="footer">
                <p style="margin: 5px 0; font-size: 14px;">🤖 Generated by <strong>Belden AI Sales Agent</strong></p>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">Powered by LangGraph + GPT-4o-mini + Vertex AI Agent Engine</p>
                <p style="margin: 10px 0 0 0; font-size: 11px; opacity: 0.7;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
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
    config = get_resend_config()
    
    # Get product owner email
    to_email = recipient_email or config.get_product_owner_email(product_category.lower())
    
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
    config = get_resend_config()
    it_url = config.it_support_url
    return {
        "action": "redirect_to_it",
        "url": it_url,
        "message": f"Este ticket ha sido identificado como un tema de IT/Soporte técnico. Por favor visite: {it_url}",
        "instructions": [
            "1. Visite el portal de IT Support",
            "2. Inicie sesión con sus credenciales corporativas",
            "3. Abra un nuevo ticket en la categoría correspondiente",
            "4. Incluya el número de referencia original del caso"
        ]
    }


def send_ticket_analysis_email(
    ticket: dict,
    classification: dict,
    recipient_email: Optional[str] = None
) -> dict:
    """
    Send email with AI ticket analysis for ALL tickets.
    
    Args:
        ticket: Ticket/case data
        classification: AI classification results
        recipient_email: Override recipient (defaults to notification_email from config)
    """
    config = get_resend_config()
    to_email = recipient_email or config.notification_email or config.from_email
    
    if not to_email:
        logger.warning("⚠️ No notification email configured")
        return {"success": False, "error": "No recipient email configured"}
    
    # Determine ticket type and styling
    is_product = classification.get("is_product_complaint", False)
    is_it = classification.get("is_it_support", False)
    sentiment = classification.get("sentiment", "neutral")
    urgency = classification.get("urgency", "medium")
    product_category = classification.get("product_category", "none")
    
    # Get IT support URL from config
    it_url = config.it_support_url
    
    # Type configuration
    if is_product:
        type_emoji = "📦"
        type_label = "PRODUCT COMPLAINT"
        type_color = "#EF4444"  # Red
        type_detail = f"Product: {product_category.upper()}"
    elif is_it:
        type_emoji = "💻"
        type_label = "IT SUPPORT REQUEST"
        type_color = "#3B82F6"  # Blue
        type_detail = f"Redirect: {it_url}"
    else:
        type_emoji = "📋"
        type_label = "GENERAL INQUIRY"
        type_color = "#6B7280"  # Gray
        type_detail = "Requires manual review"
    
    # Urgency colors
    urgency_colors = {
        "critical": "#DC2626",
        "high": "#F59E0B",
        "medium": "#3B82F6",
        "low": "#10B981"
    }
    urgency_color = urgency_colors.get(urgency, "#6B7280")
    
    # Sentiment emojis
    sentiment_emojis = {
        "angry": "😠",
        "frustrated": "😤",
        "neutral": "😐",
        "positive": "😊"
    }
    sentiment_emoji = sentiment_emojis.get(sentiment, "😐")
    
    subject = f"{type_emoji} {type_label}: {ticket.get('Subject', 'No Subject')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1F2937; background: #F3F4F6; }}
            .email-wrapper {{ max-width: 700px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, {type_color} 0%, #1E3A5F 100%); color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px; }}
            .header p {{ font-size: 16px; opacity: 0.95; }}
            .type-badge {{ display: inline-block; background: rgba(255,255,255,0.25); padding: 10px 20px; border-radius: 25px; font-weight: 700; margin-top: 15px; font-size: 14px; }}
            .content {{ padding: 40px 30px; background: #F9FAFB; }}
            .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }}
            .metric {{ background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            .metric-label {{ font-size: 11px; color: #6B7280; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }}
            .metric-value {{ font-size: 32px; margin-top: 8px; font-weight: 800; }}
            .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 5px solid {type_color}; }}
            .section-title {{ font-size: 13px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 12px; margin-top: 15px; }}
            .info-label {{ font-size: 13px; color: #6B7280; font-weight: 600; }}
            .info-value {{ font-size: 15px; color: #1F2937; font-weight: 500; }}
            .ai-box {{ background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #F59E0B; }}
            .ai-title {{ font-size: 15px; font-weight: 700; color: #92400E; margin-bottom: 12px; }}
            .ai-content {{ font-size: 14px; color: #78350F; line-height: 1.8; white-space: pre-wrap; }}
            .response-box {{ background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #10B981; }}
            .response-title {{ font-size: 15px; font-weight: 700; color: #065F46; margin-bottom: 12px; }}
            .response-content {{ font-size: 14px; color: #047857; line-height: 1.8; white-space: pre-wrap; }}
            .footer {{ background: #1E3A5F; color: white; padding: 30px; text-align: center; }}
            .footer p {{ margin: 5px 0; font-size: 13px; opacity: 0.9; }}
            .urgency-badge {{ display: inline-block; background: {urgency_color}; color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>{type_emoji} AI Ticket Analysis</h1>
                <p>The AI agent has analyzed this ticket</p>
                <div class="type-badge">{type_label}</div>
            </div>
            
            <div class="content">
                <!-- Metrics Row -->
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Type</div>
                        <div class="metric-value">{type_emoji}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Sentiment</div>
                        <div class="metric-value">{sentiment_emoji}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Urgency</div>
                        <div class="metric-value"><span class="urgency-badge">{urgency.upper()}</span></div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value" style="color: {type_color}; font-size: 24px;">{classification.get('confidence', 0):.0%}</div>
                    </div>
                </div>
                
                <!-- Ticket Info -->
                <div class="section">
                    <div class="section-title">📋 Ticket Information</div>
                    <div class="info-grid">
                        <div class="info-label">Case #:</div>
                        <div class="info-value" style="font-weight: 700; font-family: monospace;">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</div>
                        <div class="info-label">Subject:</div>
                        <div class="info-value">{ticket.get('Subject', 'N/A')}</div>
                        <div class="info-label">Priority:</div>
                        <div class="info-value">{ticket.get('Priority', 'N/A')}</div>
                        <div class="info-label">Origin:</div>
                        <div class="info-value">{ticket.get('Origin', 'N/A')}</div>
                        <div class="info-label">Classification:</div>
                        <div class="info-value" style="font-weight: 700; color: {type_color};">{type_detail}</div>
                    </div>
                </div>
                
                <!-- Description -->
                <div class="section">
                    <div class="section-title">📝 Customer Description</div>
                    <div style="white-space: pre-wrap; color: #374151; font-size: 15px; line-height: 1.8; padding: 15px; background: #F9FAFB; border-radius: 8px; margin-top: 15px;">{ticket.get('Description', 'No description provided')}</div>
                </div>
                
                <!-- AI Reasoning -->
                <div class="ai-box">
                    <div class="ai-title">🤖 AI Agent Analysis</div>
                    <div class="ai-content">{classification.get('reasoning', 'Analysis not available')}</div>
                </div>
                
                <!-- Summary -->
                <div class="section">
                    <div class="section-title">📊 Summary</div>
                    <div style="font-size: 16px; color: #374151; line-height: 1.7; margin-top: 10px;">{classification.get('complaint_summary', ticket.get('Subject', 'N/A'))}</div>
                </div>
                
                {f'''
                <!-- Suggested Response -->
                <div class="response-box">
                    <div class="response-title">💬 AI Suggested Response</div>
                    <div class="response-content">{classification.get('suggested_response', '')}</div>
                </div>
                ''' if classification.get('suggested_response') else ''}
                
                {f'''
                <!-- Product Info (if product complaint) -->
                <div class="section" style="border-left-color: #EF4444; background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);">
                    <div class="section-title">📦 Product Information</div>
                    <div class="info-grid" style="margin-top: 15px;">
                        <div class="info-label">Category:</div>
                        <div class="info-value" style="font-weight: 700; font-size: 18px; color: #B91C1C;">{product_category.upper()}</div>
                        <div class="info-label">Product Name:</div>
                        <div class="info-value" style="font-weight: 600;">{classification.get('product_name') or 'Not specified'}</div>
                    </div>
                </div>
                ''' if is_product else ''}
                
                {f'''
                <!-- IT Support Redirect -->
                <div class="section" style="border-left-color: #3B82F6; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);">
                    <div class="section-title">💻 IT Support Portal</div>
                    <p style="margin: 15px 0 10px 0; font-size: 15px; color: #1E40AF;">This ticket has been classified as an IT/Technical Support request.</p>
                    <p style="margin: 10px 0;"><strong>Portal URL:</strong> <a href="{it_url}" style="color: #1E40AF; text-decoration: none; font-weight: 600;">{it_url}</a></p>
                </div>
                ''' if is_it else ''}
            </div>
            
            <div class="footer">
                <p>🤖 Generated by <strong>Belden AI Sales Agent</strong></p>
                <p>Powered by LangGraph + GPT-4o-mini + Vertex AI Agent Engine</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 11px; margin-top: 15px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)


def send_product_expert_email(
    ticket: dict,
    classification: dict,
    recipient_email: Optional[str] = None
) -> dict:
    """
    Send email to Product Expert for product-related complaints.
    
    Args:
        ticket: Ticket/case data
        classification: AI classification results
        recipient_email: Override recipient (defaults to product_expert_email from config)
    """
    config = get_resend_config()
    to_email = recipient_email or config.product_expert_email or config.notification_email
    
    if not to_email:
        logger.warning("⚠️ No product expert email configured")
        return {"success": False, "error": "No recipient email configured"}
    
    product_category = classification.get("product_category", "general")
    product_name = classification.get("product_name", "")
    sentiment = classification.get("sentiment", "neutral")
    urgency = classification.get("urgency", "medium")
    
    # Urgency colors
    urgency_colors = {
        "critical": "#DC2626",
        "high": "#F59E0B",
        "medium": "#3B82F6",
        "low": "#10B981"
    }
    urgency_color = urgency_colors.get(urgency, "#6B7280")
    
    subject = f"📦 Product Complaint: {product_name or product_category.upper()} - {ticket.get('Subject', 'No Subject')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1F2937; background: #F3F4F6; }}
            .email-wrapper {{ max-width: 700px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%); color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px; }}
            .header p {{ font-size: 16px; opacity: 0.95; }}
            .content {{ padding: 40px 30px; background: #F9FAFB; }}
            .product-hero {{ background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); padding: 30px; border-radius: 16px; margin: -30px 30px 30px; text-align: center; border: 3px solid #EF4444; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
            .product-category {{ font-size: 12px; color: #92400E; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }}
            .product-name {{ font-size: 36px; font-weight: 800; color: #B91C1C; margin: 15px 0; }}
            .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 5px solid #EF4444; }}
            .section-title {{ font-size: 13px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 12px; margin-top: 15px; }}
            .info-label {{ font-size: 13px; color: #6B7280; font-weight: 600; }}
            .info-value {{ font-size: 15px; color: #1F2937; font-weight: 500; }}
            .ai-box {{ background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #F59E0B; }}
            .ai-title {{ font-size: 15px; font-weight: 700; color: #92400E; margin-bottom: 12px; }}
            .ai-content {{ font-size: 14px; color: #78350F; line-height: 1.8; white-space: pre-wrap; }}
            .response-box {{ background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #10B981; }}
            .response-title {{ font-size: 15px; font-weight: 700; color: #065F46; margin-bottom: 12px; }}
            .response-content {{ font-size: 14px; color: #047857; line-height: 1.8; white-space: pre-wrap; }}
            .next-steps {{ background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #3B82F6; }}
            .next-steps ul {{ margin: 15px 0 0 20px; }}
            .next-steps li {{ margin-bottom: 12px; font-size: 14px; color: #1E40AF; line-height: 1.7; }}
            .urgency-badge {{ display: inline-block; background: {urgency_color}; color: white; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 700; margin-top: 15px; }}
            .footer {{ background: #1E3A5F; color: white; padding: 30px; text-align: center; }}
            .footer p {{ margin: 5px 0; font-size: 13px; opacity: 0.9; }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>📦 Product Complaint - Action Required</h1>
                <p>Product Expert</p>
            </div>
            
            <div class="product-hero">
                <div class="product-category">Category</div>
                <div class="product-name">{product_category.upper()}</div>
                {f'<div style="font-size: 18px; color: #374151; margin-top: 15px; font-weight: 600;">Product: {product_name}</div>' if product_name else ''}
                <div>
                    <span class="urgency-badge">Urgency: {urgency.upper()}</span>
                </div>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">📋 Ticket Information</div>
                    <div class="info-grid">
                        <div class="info-label">Case #:</div>
                        <div class="info-value" style="font-weight: 700; font-family: monospace;">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</div>
                        <div class="info-label">Subject:</div>
                        <div class="info-value">{ticket.get('Subject', 'N/A')}</div>
                        <div class="info-label">Priority:</div>
                        <div class="info-value">{ticket.get('Priority', 'N/A')}</div>
                        <div class="info-label">Sentiment:</div>
                        <div class="info-value">{sentiment.capitalize()}</div>
                        <div class="info-label">Confidence:</div>
                        <div class="info-value" style="color: #EF4444; font-weight: 700; font-size: 18px;">{classification.get('confidence', 0):.0%}</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📝 Customer Description</div>
                    <div style="white-space: pre-wrap; color: #374151; font-size: 15px; line-height: 1.8; padding: 15px; background: #F9FAFB; border-radius: 8px; margin-top: 15px;">{ticket.get('Description', 'No description provided')}</div>
                </div>
                
                <div class="ai-box">
                    <div class="ai-title">🤖 AI Agent Analysis</div>
                    <div class="ai-content">{classification.get('reasoning', 'Analysis not available')}</div>
                </div>
                
                {f'''
                <div class="response-box">
                    <div class="response-title">💬 AI Suggested Response</div>
                    <div class="response-content">{classification.get('suggested_response', '')}</div>
                </div>
                ''' if classification.get('suggested_response') else ''}
                
                <div class="next-steps">
                    <div class="section-title" style="color: #1E40AF; margin-bottom: 15px;">🎯 Required Actions</div>
                    <ul>
                        <li><strong>Review:</strong> Examine the product complaint details above</li>
                        <li><strong>Contact:</strong> Reach out to the customer based on urgency level</li>
                        <li><strong>Investigate:</strong> Research the reported issue thoroughly</li>
                        <li><strong>Resolve:</strong> Provide solution or follow-up plan</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>📦 Sent to <strong>Product Expert</strong></p>
                <p>🤖 Generated by Belden AI Sales Agent</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 11px; margin-top: 15px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)


def send_services_agent_email(
    ticket: dict,
    classification: dict,
    redirect_url: str = "",
    recipient_email: Optional[str] = None
) -> dict:
    """
    Send email to Services Agent for page/service/IT-related tickets.
    
    Args:
        ticket: Ticket/case data
        classification: AI classification results
        redirect_url: IT support portal URL (if applicable)
        recipient_email: Override recipient (defaults to services_agent_email from config)
    """
    config = get_resend_config()
    to_email = recipient_email or config.services_agent_email or config.notification_email
    
    if not to_email:
        logger.warning("⚠️ No services agent email configured")
        return {"success": False, "error": "No recipient email configured"}
    
    sentiment = classification.get("sentiment", "neutral")
    urgency = classification.get("urgency", "medium")
    
    # Urgency colors
    urgency_colors = {
        "critical": "#DC2626",
        "high": "#F59E0B",
        "medium": "#3B82F6",
        "low": "#10B981"
    }
    urgency_color = urgency_colors.get(urgency, "#6B7280")
    
    subject = f"🌐 Services/Page Request: {ticket.get('Subject', 'No Subject')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1F2937; background: #F3F4F6; }}
            .email-wrapper {{ max-width: 700px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%); color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px; }}
            .header p {{ font-size: 16px; opacity: 0.95; }}
            .content {{ padding: 40px 30px; background: #F9FAFB; }}
            .services-hero {{ background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 30px; border-radius: 16px; margin: -30px 30px 30px; text-align: center; border: 3px solid #3B82F6; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
            .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 5px solid #3B82F6; }}
            .section-title {{ font-size: 13px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 12px; margin-top: 15px; }}
            .info-label {{ font-size: 13px; color: #6B7280; font-weight: 600; }}
            .info-value {{ font-size: 15px; color: #1F2937; font-weight: 500; }}
            .ai-box {{ background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #F59E0B; }}
            .ai-title {{ font-size: 15px; font-weight: 700; color: #92400E; margin-bottom: 12px; }}
            .ai-content {{ font-size: 14px; color: #78350F; line-height: 1.8; white-space: pre-wrap; }}
            .response-box {{ background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #10B981; }}
            .response-title {{ font-size: 15px; font-weight: 700; color: #065F46; margin-bottom: 12px; }}
            .response-content {{ font-size: 14px; color: #047857; line-height: 1.8; white-space: pre-wrap; }}
            .redirect-box {{ background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #F59E0B; }}
            .redirect-title {{ font-size: 15px; font-weight: 700; color: #92400E; margin-bottom: 12px; }}
            .redirect-content {{ font-size: 14px; color: #78350F; line-height: 1.8; }}
            .next-steps {{ background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 25px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #3B82F6; }}
            .next-steps ul {{ margin: 15px 0 0 20px; }}
            .next-steps li {{ margin-bottom: 12px; font-size: 14px; color: #1E40AF; line-height: 1.7; }}
            .urgency-badge {{ display: inline-block; background: {urgency_color}; color: white; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 700; margin-top: 15px; }}
            .footer {{ background: #1E3A5F; color: white; padding: 30px; text-align: center; }}
            .footer p {{ margin: 5px 0; font-size: 13px; opacity: 0.9; }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>🌐 Services/Page Request</h1>
                <p>Services Agent</p>
            </div>
            
            <div class="services-hero">
                <div style="font-size: 48px; margin: 10px 0;">💻</div>
                <div style="font-size: 24px; font-weight: 700; color: #1E40AF; margin: 15px 0;">Services/Page/IT Issue</div>
                <div>
                    <span class="urgency-badge">Urgency: {urgency.upper()}</span>
                </div>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">📋 Ticket Information</div>
                    <div class="info-grid">
                        <div class="info-label">Case #:</div>
                        <div class="info-value" style="font-weight: 700; font-family: monospace;">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</div>
                        <div class="info-label">Subject:</div>
                        <div class="info-value">{ticket.get('Subject', 'N/A')}</div>
                        <div class="info-label">Priority:</div>
                        <div class="info-value">{ticket.get('Priority', 'N/A')}</div>
                        <div class="info-label">Sentiment:</div>
                        <div class="info-value">{sentiment.capitalize()}</div>
                        <div class="info-label">Confidence:</div>
                        <div class="info-value" style="color: #3B82F6; font-weight: 700; font-size: 18px;">{classification.get('confidence', 0):.0%}</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📝 Customer Description</div>
                    <div style="white-space: pre-wrap; color: #374151; font-size: 15px; line-height: 1.8; padding: 15px; background: #F9FAFB; border-radius: 8px; margin-top: 15px;">{ticket.get('Description', 'No description provided')}</div>
                </div>
                
                {f'''
                <div class="redirect-box">
                    <div class="redirect-title">🔗 IT Support Portal</div>
                    <div class="redirect-content">
                        <p style="margin: 10px 0;"><strong>Portal URL:</strong> <a href="{redirect_url}" style="color: #1E40AF; text-decoration: none; font-weight: 600;">{redirect_url}</a></p>
                        <p style="margin: 10px 0;">The customer should be directed to this portal to resolve their request.</p>
                    </div>
                </div>
                ''' if redirect_url else ''}
                
                <div class="ai-box">
                    <div class="ai-title">🤖 AI Agent Analysis</div>
                    <div class="ai-content">{classification.get('reasoning', 'Analysis not available')}</div>
                </div>
                
                {f'''
                <div class="response-box">
                    <div class="response-title">💬 AI Suggested Response</div>
                    <div class="response-content">{classification.get('suggested_response', '')}</div>
                </div>
                ''' if classification.get('suggested_response') else ''}
                
                <div class="next-steps">
                    <div class="section-title" style="color: #1E40AF; margin-bottom: 15px;">🎯 Required Actions</div>
                    <ul>
                        <li><strong>Review:</strong> Examine the customer's request details above</li>
                        <li><strong>Provide Access:</strong> Grant access or provide solution as appropriate</li>
                        <li><strong>Contact:</strong> Reach out to customer if necessary</li>
                        <li><strong>Document:</strong> Record resolution in the system</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>🌐 Sent to <strong>Services Agent</strong></p>
                <p>🤖 Generated by Belden AI Sales Agent</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 11px; margin-top: 15px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)
