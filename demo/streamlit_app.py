"""
🎨 Belden AI Sales Agent - Visual Demo Interface

Una interfaz visual interactiva para demostrar el agente de AI.

Uso:
    streamlit run demo/streamlit_app.py

Requiere:
    pip install streamlit
"""

import streamlit as st
import json
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Belden AI Sales Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #E8F4F8 0%, #D1E8E2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .score-box {
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
    }
    .score-p1 { background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; }
    .score-p2 { background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; }
    .score-p3 { background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); color: white; }
    .reasoning-box {
        background: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .category-outage { background: #FEE2E2; border: 2px solid #EF4444; }
    .category-security { background: #FEE2E2; border: 2px solid #DC2626; }
    .category-billing { background: #FEF3C7; border: 2px solid #F59E0B; }
    .category-howto { background: #D1FAE5; border: 2px solid #10B981; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Agent configuration
AGENT_CONFIG = {
    "project_id": "logical-hallway-485016-r7",
    "location": "us-central1", 
    "agent_id": "180545306838958080"
}

def call_agent(action: str, data: dict, use_llm: bool = True) -> dict:
    """Call the Vertex AI Agent"""
    try:
        from vertexai import agent_engines
        import vertexai
        
        vertexai.init(
            project=AGENT_CONFIG["project_id"],
            location=AGENT_CONFIG["location"]
        )
        
        agent = agent_engines.get(
            f"projects/{AGENT_CONFIG['project_id']}/locations/{AGENT_CONFIG['location']}/reasoningEngines/{AGENT_CONFIG['agent_id']}"
        )
        
        if action == "qualify_lead":
            result = agent.query(action="qualify_lead", lead_data=data, use_llm=use_llm)
        elif action == "triage_ticket":
            result = agent.query(action="triage_ticket", case_data=data, use_llm=use_llm)
        else:
            result = agent.query(action=action)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def render_lead_result(result: dict):
    """Render lead qualification results beautifully"""
    data = result.get("data", result)
    
    score = data.get("score", 0)
    routing = data.get("routing", {})
    reasoning = data.get("reasoning", "")
    confidence = data.get("confidence", 0)
    key_factors = data.get("key_factors", [])
    
    # Determine priority class
    if score >= 0.75:
        priority = "P1"
        priority_class = "score-p1"
        priority_label = "🔥 HOT - Account Executive"
        priority_emoji = "🚀"
    elif score >= 0.45:
        priority = "P2"
        priority_class = "score-p2"
        priority_label = "⚡ WARM - Sales Dev Rep"
        priority_emoji = "📈"
    else:
        priority = "P3"
        priority_class = "score-p3"
        priority_label = "❄️ COLD - Nurture Campaign"
        priority_emoji = "📧"
    
    # Layout
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="score-box {priority_class}">
            {score:.2f}
        </div>
        <p style="text-align: center; font-size: 1.2rem; margin-top: 0.5rem;">
            <strong>{priority}</strong> - Lead Score
        </p>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{priority_emoji} Routing</h3>
            <p style="font-size: 1.1rem;">{priority_label}</p>
            <p style="color: #6B7280;">Owner: {routing.get('owner_type', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 Confidence</h3>
            <p style="font-size: 2rem; font-weight: bold;">{confidence:.0%}</p>
            <p style="color: #6B7280;">AI Certainty</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Key Factors
    if key_factors:
        st.markdown("### 🔑 Key Decision Factors")
        cols = st.columns(len(key_factors[:4]))
        for i, factor in enumerate(key_factors[:4]):
            with cols[i]:
                st.info(f"✓ {factor}")
    
    # AI Reasoning
    st.markdown("### 🤖 AI Reasoning")
    st.markdown(f"""
    <div class="reasoning-box">
        {reasoning.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)


def render_ticket_result(result: dict):
    """Render ticket triage results beautifully"""
    data = result.get("data", result)
    
    category = data.get("category", "other")
    decision = data.get("decision", {})
    reasoning = data.get("reasoning", "")
    sentiment = data.get("sentiment", "neutral")
    urgency = data.get("urgency", "medium")
    confidence = data.get("confidence", 0)
    requires_escalation = data.get("requires_escalation", False)
    suggested_response = data.get("suggested_response", "")
    
    # Category styling
    category_config = {
        "outage": {"emoji": "🚨", "label": "SYSTEM OUTAGE", "color": "#EF4444", "class": "category-outage"},
        "security": {"emoji": "🔒", "label": "SECURITY ALERT", "color": "#DC2626", "class": "category-security"},
        "billing": {"emoji": "💰", "label": "BILLING ISSUE", "color": "#F59E0B", "class": "category-billing"},
        "howto": {"emoji": "❓", "label": "HOW-TO QUESTION", "color": "#10B981", "class": "category-howto"},
        "other": {"emoji": "📋", "label": "GENERAL INQUIRY", "color": "#6B7280", "class": ""}
    }
    
    cat_config = category_config.get(category, category_config["other"])
    
    # Layout
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card {cat_config['class']}" style="padding: 1.5rem;">
            <span style="font-size: 2.5rem;">{cat_config['emoji']}</span>
            <h3 style="margin: 0.5rem 0;">{cat_config['label']}</h3>
            <p style="color: #6B7280;">{category.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sentiment_emoji = {"frustrated": "😤", "angry": "😠", "neutral": "😐", "happy": "😊"}.get(sentiment, "😐")
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 2.5rem;">{sentiment_emoji}</span>
            <h3>Sentiment</h3>
            <p>{sentiment.capitalize()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        urgency_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(urgency, "🟡")
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 2.5rem;">{urgency_emoji}</span>
            <h3>Urgency</h3>
            <p>{urgency.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 2.5rem;">{"🚨" if requires_escalation else "✅"}</span>
            <h3>Escalation</h3>
            <p>{"REQUIRED" if requires_escalation else "Not needed"}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Action taken
    action = decision.get("action", "N/A")
    st.markdown(f"### ⚡ Action: **{action.upper().replace('_', ' ')}**")
    
    # AI Reasoning
    st.markdown("### 🤖 AI Analysis")
    st.markdown(f"""
    <div class="reasoning-box">
        {reasoning.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    # Suggested Response
    if suggested_response:
        st.markdown("### 📝 Suggested Response")
        st.text_area("", suggested_response, height=150, disabled=True)


# =============================================================================
# MAIN APP
# =============================================================================

# Header
st.markdown('<div class="main-header">🤖 Belden AI Sales Agent</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Google_Cloud_logo.svg/200px-Google_Cloud_logo.svg.png", width=150)
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    st.code(f"""
Project: {AGENT_CONFIG['project_id']}
Location: {AGENT_CONFIG['location']}
Agent: {AGENT_CONFIG['agent_id'][:8]}...
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    st.metric("Queries Made", len(st.session_state.history))
    
    use_llm = st.checkbox("Use LLM (GPT-4)", value=True, help="Toggle AI-powered analysis")
    
    st.markdown("---")
    st.markdown("### 🔗 Links")
    st.markdown("[📂 GitHub Repo](https://github.com/javierherrera1996/langgraph-salesforce-sap-demo)")
    st.markdown("[📈 LangSmith Traces](https://smith.langchain.com)")

# Main tabs
tab1, tab2, tab3 = st.tabs(["🎯 Lead Qualification", "🎫 Ticket Triage", "📜 History"])

# =============================================================================
# TAB 1: LEAD QUALIFICATION
# =============================================================================
with tab1:
    st.markdown("## 🎯 Lead Qualification & Routing")
    st.markdown("Enter lead information to get AI-powered qualification and routing recommendation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 Lead Information")
        lead_company = st.text_input("Company Name", "Industrial Manufacturing Corp")
        lead_title = st.selectbox("Job Title", [
            "Chief Technology Officer",
            "Chief Information Officer", 
            "VP of Engineering",
            "Director of IT",
            "IT Manager",
            "Senior Engineer",
            "Developer",
            "Other"
        ])
        lead_industry = st.selectbox("Industry", [
            "Manufacturing",
            "Technology",
            "Healthcare",
            "Financial Services",
            "Logistics",
            "Energy",
            "Retail",
            "Other"
        ])
    
    with col2:
        st.markdown("### 📊 Lead Metrics")
        lead_rating = st.select_slider("Lead Rating", ["Cold", "Warm", "Hot"], value="Warm")
        lead_revenue = st.slider("Annual Revenue ($M)", 0.1, 100.0, 5.0, 0.1)
        lead_employees = st.slider("Number of Employees", 10, 5000, 200, 10)
        lead_source = st.selectbox("Lead Source", [
            "Partner Referral",
            "Website",
            "Trade Show",
            "Cold Call",
            "Advertisement",
            "Other"
        ])
    
    lead_description = st.text_area("Lead Description / Notes", 
        "Looking for industrial network solutions for our manufacturing facilities.",
        height=100)
    
    if st.button("🚀 Qualify Lead", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is analyzing the lead..."):
            lead_data = {
                "Id": f"00Q{datetime.now().strftime('%H%M%S')}",
                "Company": lead_company,
                "Title": lead_title,
                "Industry": lead_industry,
                "Rating": lead_rating,
                "AnnualRevenue": lead_revenue * 1000000,
                "NumberOfEmployees": lead_employees,
                "LeadSource": lead_source,
                "Description": lead_description
            }
            
            start_time = time.time()
            result = call_agent("qualify_lead", lead_data, use_llm)
            elapsed = time.time() - start_time
            
            if result.get("success"):
                st.success(f"✅ Analysis complete in {elapsed:.2f}s")
                st.markdown("---")
                render_lead_result(result)
                
                # Save to history
                st.session_state.history.append({
                    "type": "lead",
                    "input": lead_data,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                st.error(f"❌ Error: {result.get('error')}")

# =============================================================================
# TAB 2: TICKET TRIAGE
# =============================================================================
with tab2:
    st.markdown("## 🎫 Support Ticket Triage")
    st.markdown("Enter ticket information to get AI-powered categorization and action recommendation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Ticket Details")
        ticket_subject = st.text_input("Subject", "Network connectivity issues in production")
        ticket_priority = st.select_slider("Current Priority", ["Low", "Medium", "High"], value="Medium")
        ticket_origin = st.selectbox("Origin", ["Email", "Phone", "Web", "Chat"])
    
    with col2:
        st.markdown("### 📋 Quick Templates")
        template = st.selectbox("Load Template", [
            "-- Select --",
            "🚨 Production Outage",
            "💰 Billing Issue", 
            "❓ How-To Question",
            "🔒 Security Concern"
        ])
        
        if template == "🚨 Production Outage":
            ticket_subject = "URGENT: Complete network failure - Production DOWN"
            ticket_description = "All our Belden switches stopped working. Production line is halted. We're losing $50K/hour. Need immediate assistance!"
        elif template == "💰 Billing Issue":
            ticket_subject = "Invoice discrepancy - PO doesn't match"
            ticket_description = "I received invoice #INV-2024-5678 for $45,000 but our PO was only for $38,000. Please review."
        elif template == "❓ How-To Question":
            ticket_subject = "How to configure VLAN on Hirschmann switch?"
            ticket_description = "I just purchased a Hirschmann RSP switch. Where can I find the VLAN configuration guide?"
        elif template == "🔒 Security Concern":
            ticket_subject = "Unauthorized access attempts detected"
            ticket_description = "We noticed multiple failed login attempts from unknown IP addresses on our network management interface."
        else:
            ticket_description = ""
    
    ticket_description = st.text_area("Description", 
        ticket_description if ticket_description else "Please describe the issue in detail...",
        height=150)
    
    if st.button("🎫 Triage Ticket", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is analyzing the ticket..."):
            case_data = {
                "Id": f"500{datetime.now().strftime('%H%M%S')}",
                "CaseNumber": f"00099{datetime.now().strftime('%H%M')}",
                "Subject": ticket_subject,
                "Description": ticket_description,
                "Priority": ticket_priority,
                "Status": "New",
                "Origin": ticket_origin
            }
            
            start_time = time.time()
            result = call_agent("triage_ticket", case_data, use_llm)
            elapsed = time.time() - start_time
            
            if result.get("success"):
                st.success(f"✅ Analysis complete in {elapsed:.2f}s")
                st.markdown("---")
                render_ticket_result(result)
                
                # Save to history
                st.session_state.history.append({
                    "type": "ticket",
                    "input": case_data,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                st.error(f"❌ Error: {result.get('error')}")

# =============================================================================
# TAB 3: HISTORY
# =============================================================================
with tab3:
    st.markdown("## 📜 Query History")
    
    if not st.session_state.history:
        st.info("No queries yet. Try qualifying a lead or triaging a ticket!")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{'🎯' if item['type'] == 'lead' else '🎫'} {item['input'].get('Company', item['input'].get('Subject', 'Query'))} - {item['timestamp'][:19]}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Input:**")
                    st.json(item['input'])
                with col2:
                    st.markdown("**Result:**")
                    st.json(item['result'].get('data', item['result']))
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.9rem;">
    🤖 Powered by <strong>LangGraph</strong> + <strong>Vertex AI Agent Engine</strong> + <strong>GPT-4o-mini</strong><br>
    Built for Belden Enterprise Sales Operations
</div>
""", unsafe_allow_html=True)
