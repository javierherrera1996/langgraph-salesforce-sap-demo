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
    
    if not config.is_configured:
        # Simulate email for demo
        logger.warning("⚠️ Resend not configured - simulating email")
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
        import resend
        
        # Set API key
        resend.api_key = config.api_key
        
        params = {
            "from": from_email or config.from_email,
            "to": [to],
            "subject": subject,
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        
        logger.info(f"✅ Email sent successfully to: {to}")
        logger.info(f"   Message ID: {response.get('id', 'N/A')}")
        
        return {
            "success": True,
            "simulated": False,
            "message_id": response.get("id"),
            "to": to,
            "subject": subject,
            "from": from_email or config.from_email
        }
        
    except ImportError:
        logger.error("❌ Resend package not installed. Run: pip install resend")
        return {
            "success": False,
            "error": "Resend package not installed",
            "to": to,
            "subject": subject
        }
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to}: {e}")
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
                    <div class="value" style="margin-top: 10px; font-size: 14px; color: #6B7280;">{routing.get('reason', 'N/A')[:200]}</div>
                </div>
                
                {f'''
                <div class="section" style="border-left-color: #10B981;">
                    <div class="label">📊 SAP Business Context</div>
                    <table style="width: 100%; margin-top: 10px;">
                        <tr><td class="label">Business Partner ID</td><td class="value">{enriched.get('business_partner_id', 'N/A')}</td></tr>
                        <tr><td class="label">Total Orders</td><td class="value">{enriched.get('total_orders', 0)}</td></tr>
                        <tr><td class="label">Total Revenue</td><td class="value">${enriched.get('total_revenue', 0):,.2f}</td></tr>
                        <tr><td class="label">Credit Rating</td><td class="value">{enriched.get('credit_rating', 'N/A')}</td></tr>
                        <tr><td class="label">Last Order Date</td><td class="value">{enriched.get('last_order_date', 'N/A')}</td></tr>
                    </table>
                </div>
                ''' if enriched and enriched.get('business_partner_id') else ''}
                
                <div class="section">
                    <div class="label">💼 Opportunity Summary</div>
                    <div style="background: #EFF6FF; padding: 15px; border-radius: 8px; margin-top: 10px;">
                        <p style="margin: 0 0 10px 0;"><strong>Company:</strong> {lead.get('Company', 'N/A')}</p>
                        <p style="margin: 0 0 10px 0;"><strong>Contact:</strong> {lead.get('FirstName', '')} {lead.get('LastName', '')} ({lead.get('Title', 'N/A')})</p>
                        <p style="margin: 0 0 10px 0;"><strong>Potential Value:</strong> ${lead.get('AnnualRevenue', 0):,.0f} annual revenue | {lead.get('NumberOfEmployees', 'N/A')} employees</p>
                        <p style="margin: 0 0 10px 0;"><strong>Industry:</strong> {lead.get('Industry', 'N/A')} | <strong>Rating:</strong> {lead.get('Rating', 'N/A')}</p>
                        <p style="margin: 0;"><strong>Lead Source:</strong> {lead.get('LeadSource', 'N/A')}</p>
                    </div>
                </div>
                
                <div class="reasoning">
                    <div class="label">🤖 AI Analysis & Reasoning</div>
                    <div style="white-space: pre-wrap; font-size: 14px; margin-top: 10px;">{reasoning}</div>
                </div>
                
                {f'''
                <div class="section">
                    <div class="label">📝 Lead Description</div>
                    <div class="value" style="white-space: pre-wrap; font-size: 14px;">{lead.get("Description", "N/A")}</div>
                </div>
                ''' if lead.get("Description") else ''}
                
                <div class="section" style="background: #FEF3C7; border-left-color: #F59E0B;">
                    <div class="label">🎯 Next Steps</div>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Review lead details in Salesforce</li>
                        <li>Contact lead within 24 hours</li>
                        <li>Follow up based on AI recommendations</li>
                        <li>Update opportunity status after contact</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="https://your-salesforce-instance.com/{lead.get('Id', '')}" class="cta" style="text-decoration: none;">View Lead in Salesforce →</a>
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
        type_label = "QUEJA DE PRODUCTO"
        type_color = "#EF4444"  # Red
        type_detail = f"Producto: {product_category.upper()}"
    elif is_it:
        type_emoji = "💻"
        type_label = "SOLICITUD IT SOPORTE"
        type_color = "#3B82F6"  # Blue
        type_detail = f"Redirect: {it_url}"
    else:
        type_emoji = "📋"
        type_label = "CONSULTA GENERAL"
        type_color = "#6B7280"  # Gray
        type_detail = "Requiere revisión manual"
    
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
    
    subject = f"{type_emoji} {type_label}: {ticket.get('Subject', 'Sin asunto')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, {type_color}, #1E3A5F); color: white; padding: 25px; border-radius: 12px 12px 0 0; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 8px 0 0 0; opacity: 0.9; }}
            .type-badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: bold; margin-top: 15px; }}
            .content {{ background: #F8FAFC; padding: 25px; }}
            .metrics {{ display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }}
            .metric {{ background: white; padding: 15px; border-radius: 10px; flex: 1; min-width: 120px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-label {{ font-size: 11px; color: #6B7280; text-transform: uppercase; font-weight: bold; }}
            .metric-value {{ font-size: 24px; margin-top: 5px; }}
            .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 4px solid {type_color}; }}
            .section-title {{ font-weight: bold; color: #1E3A5F; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; }}
            .reasoning-box {{ background: #FEF3C7; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #F59E0B; }}
            .reasoning-title {{ font-weight: bold; color: #92400E; margin-bottom: 10px; }}
            .response-box {{ background: #D1FAE5; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #10B981; }}
            .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 12px; border-top: 1px solid #E5E7EB; }}
            .urgency-badge {{ display: inline-block; background: {urgency_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{type_emoji} Análisis de Ticket por AI</h1>
                <p>El agente de inteligencia artificial ha analizado este ticket</p>
                <div class="type-badge">{type_label}</div>
            </div>
            
            <div class="content">
                <!-- Metrics Row -->
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Tipo</div>
                        <div class="metric-value">{type_emoji}</div>
                        <div style="font-size: 11px; color: #6B7280;">{type_label}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Sentimiento</div>
                        <div class="metric-value">{sentiment_emoji}</div>
                        <div style="font-size: 11px; color: #6B7280;">{sentiment.capitalize()}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Urgencia</div>
                        <div class="metric-value"><span class="urgency-badge">{urgency.upper()}</span></div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Confianza</div>
                        <div class="metric-value" style="color: {type_color};">{classification.get('confidence', 0):.0%}</div>
                    </div>
                </div>
                
                <!-- Ticket Info -->
                <div class="section">
                    <div class="section-title">📋 Información del Ticket</div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; color: #6B7280; width: 120px;">Caso #</td><td style="font-weight: bold;">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Asunto</td><td>{ticket.get('Subject', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Prioridad</td><td>{ticket.get('Priority', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Origen</td><td>{ticket.get('Origin', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Clasificación</td><td><strong>{type_detail}</strong></td></tr>
                    </table>
                </div>
                
                <!-- Description -->
                <div class="section">
                    <div class="section-title">📝 Descripción del Cliente</div>
                    <div style="white-space: pre-wrap; color: #374151;">{ticket.get('Description', 'Sin descripción')}</div>
                </div>
                
                <!-- AI Reasoning -->
                <div class="reasoning-box">
                    <div class="reasoning-title">🤖 Análisis del Agente de IA</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{classification.get('reasoning', 'Análisis no disponible')}</div>
                </div>
                
                <!-- Summary -->
                <div class="section">
                    <div class="section-title">📊 Resumen</div>
                    <div style="font-size: 15px; color: #374151;">{classification.get('complaint_summary', ticket.get('Subject', 'N/A'))}</div>
                </div>
                
                {f'''
                <!-- Suggested Response -->
                <div class="response-box">
                    <div style="font-weight: bold; color: #065F46; margin-bottom: 10px;">💬 Respuesta Sugerida por AI</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{classification.get('suggested_response', '')}</div>
                </div>
                ''' if classification.get('suggested_response') else ''}
                
                {f'''
                <!-- Product Info (if product complaint) -->
                <div class="section" style="border-left-color: #EF4444;">
                    <div class="section-title">📦 Información del Producto</div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; color: #6B7280; width: 120px;">Categoría</td><td style="font-weight: bold;">{product_category.upper()}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Producto</td><td>{classification.get('product_name') or 'No especificado'}</td></tr>
                    </table>
                </div>
                ''' if is_product else ''}
                
                {f'''
                <!-- IT Support Redirect -->
                <div class="section" style="border-left-color: #3B82F6; background: #EFF6FF;">
                    <div class="section-title">💻 Redirección a IT Support</div>
                    <p>Este ticket ha sido clasificado como solicitud de IT/Soporte técnico.</p>
                    <p><strong>Portal:</strong> <a href="{it_url}">{it_url}</a></p>
                </div>
                ''' if is_it else ''}
            </div>
            
            <div class="footer">
                <p>🤖 Análisis generado por <strong>Belden AI Sales Agent</strong></p>
                <p>Powered by LangGraph + GPT-4o-mini + Vertex AI Agent Engine</p>
                <p style="color: #9CA3AF; font-size: 11px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
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
    
    subject = f"📦 Queja de Producto: {product_name or product_category.upper()} - {ticket.get('Subject', 'Sin asunto')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #EF4444, #B91C1C); color: white; padding: 25px; border-radius: 12px 12px 0 0; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ background: #F8FAFC; padding: 25px; }}
            .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 4px solid #EF4444; }}
            .section-title {{ font-weight: bold; color: #1E3A5F; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; }}
            .product-highlight {{ background: #FEE2E2; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #EF4444; text-align: center; }}
            .product-name {{ font-size: 28px; font-weight: bold; color: #B91C1C; margin: 10px 0; }}
            .urgency-badge {{ display: inline-block; background: {urgency_color}; color: white; padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
            .reasoning-box {{ background: #FEF3C7; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #F59E0B; }}
            .response-box {{ background: #D1FAE5; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #10B981; }}
            .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 12px; border-top: 1px solid #E5E7EB; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📦 Queja de Producto - Requiere Atención</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">Asesor Experto en Producto</p>
            </div>
            
            <div class="content">
                <div class="product-highlight">
                    <div style="font-size: 12px; color: #92400E; text-transform: uppercase; font-weight: bold;">Categoría</div>
                    <div class="product-name">{product_category.upper()}</div>
                    {f'<div style="font-size: 16px; color: #374151; margin-top: 10px;">Producto: {product_name}</div>' if product_name else ''}
                    <div style="margin-top: 15px;">
                        <span class="urgency-badge">Urgencia: {urgency.upper()}</span>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📋 Información del Ticket</div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; color: #6B7280; width: 120px;">Caso #</td><td style="font-weight: bold;">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Asunto</td><td>{ticket.get('Subject', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Prioridad</td><td>{ticket.get('Priority', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Sentimiento</td><td>{sentiment.capitalize()}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Confianza</td><td style="color: #EF4444; font-weight: bold;">{classification.get('confidence', 0):.0%}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <div class="section-title">📝 Descripción del Cliente</div>
                    <div style="white-space: pre-wrap; color: #374151;">{ticket.get('Description', 'Sin descripción')}</div>
                </div>
                
                <div class="reasoning-box">
                    <div style="font-weight: bold; color: #92400E; margin-bottom: 10px;">🤖 Análisis del Agente de IA</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{classification.get('reasoning', 'Análisis no disponible')}</div>
                </div>
                
                {f'''
                <div class="response-box">
                    <div style="font-weight: bold; color: #065F46; margin-bottom: 10px;">💬 Respuesta Sugerida</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{classification.get('suggested_response', '')}</div>
                </div>
                ''' if classification.get('suggested_response') else ''}
                
                <div class="section" style="background: #EFF6FF; border-left-color: #3B82F6;">
                    <div class="section-title">🎯 Acción Requerida</div>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Revisar la queja del producto identificado</li>
                        <li>Contactar al cliente según urgencia</li>
                        <li>Investigar el problema reportado</li>
                        <li>Proporcionar solución o seguimiento</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>📦 Enviado a <strong>Asesor Experto en Producto</strong></p>
                <p>🤖 Análisis generado por Belden AI Sales Agent</p>
                <p style="color: #9CA3AF; font-size: 11px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
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
    
    subject = f"🌐 Solicitud de Servicios/Página: {ticket.get('Subject', 'Sin asunto')[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3B82F6, #1E40AF); color: white; padding: 25px; border-radius: 12px 12px 0 0; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ background: #F8FAFC; padding: 25px; }}
            .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 4px solid #3B82F6; }}
            .section-title {{ font-weight: bold; color: #1E3A5F; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; }}
            .services-highlight {{ background: #EFF6FF; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #3B82F6; text-align: center; }}
            .urgency-badge {{ display: inline-block; background: {urgency_color}; color: white; padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
            .reasoning-box {{ background: #FEF3C7; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #F59E0B; }}
            .response-box {{ background: #D1FAE5; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #10B981; }}
            .redirect-box {{ background: #FEF3C7; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #F59E0B; }}
            .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 12px; border-top: 1px solid #E5E7EB; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌐 Solicitud de Servicios/Página Web</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">Asesor de Servicios</p>
            </div>
            
            <div class="content">
                <div class="services-highlight">
                    <div style="font-size: 28px; margin: 10px 0;">💻</div>
                    <div style="font-size: 20px; font-weight: bold; color: #1E40AF;">Tema de Servicios/Página/IT</div>
                    <div style="margin-top: 15px;">
                        <span class="urgency-badge">Urgencia: {urgency.upper()}</span>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📋 Información del Ticket</div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; color: #6B7280; width: 120px;">Caso #</td><td style="font-weight: bold;">{ticket.get('CaseNumber', ticket.get('Id', 'N/A'))}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Asunto</td><td>{ticket.get('Subject', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Prioridad</td><td>{ticket.get('Priority', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Sentimiento</td><td>{sentiment.capitalize()}</td></tr>
                        <tr><td style="padding: 8px 0; color: #6B7280;">Confianza</td><td style="color: #3B82F6; font-weight: bold;">{classification.get('confidence', 0):.0%}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <div class="section-title">📝 Descripción del Cliente</div>
                    <div style="white-space: pre-wrap; color: #374151;">{ticket.get('Description', 'Sin descripción')}</div>
                </div>
                
                {f'''
                <div class="redirect-box">
                    <div style="font-weight: bold; color: #92400E; margin-bottom: 10px;">🔗 Portal de IT Support</div>
                    <p style="margin: 10px 0;"><strong>URL:</strong> <a href="{redirect_url}" style="color: #1E40AF; text-decoration: none;">{redirect_url}</a></p>
                    <p style="margin: 10px 0; font-size: 14px;">El cliente debe ser dirigido a este portal para resolver su solicitud.</p>
                </div>
                ''' if redirect_url else ''}
                
                <div class="reasoning-box">
                    <div style="font-weight: bold; color: #92400E; margin-bottom: 10px;">🤖 Análisis del Agente de IA</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{classification.get('reasoning', 'Análisis no disponible')}</div>
                </div>
                
                {f'''
                <div class="response-box">
                    <div style="font-weight: bold; color: #065F46; margin-bottom: 10px;">💬 Respuesta Sugerida</div>
                    <div style="white-space: pre-wrap; font-size: 14px;">{classification.get('suggested_response', '')}</div>
                </div>
                ''' if classification.get('suggested_response') else ''}
                
                <div class="section" style="background: #EFF6FF; border-left-color: #3B82F6;">
                    <div class="section-title">🎯 Acción Requerida</div>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Revisar la solicitud del cliente</li>
                        <li>Proporcionar acceso o solución según el caso</li>
                        <li>Contactar al cliente si es necesario</li>
                        <li>Registrar la resolución en el sistema</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>🌐 Enviado a <strong>Asesor de Servicios</strong></p>
                <p>🤖 Análisis generado por Belden AI Sales Agent</p>
                <p style="color: #9CA3AF; font-size: 11px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)
