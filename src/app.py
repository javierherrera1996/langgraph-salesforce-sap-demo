"""
Agent Application for Vertex AI Agent Engine.

This module wraps the LangGraph workflows into a class format compatible with
Google Cloud's Vertex AI Agent Engine deployment.

References:
- https://docs.cloud.google.com/agent-builder/agent-engine/deploy
- https://docs.cloud.google.com/agent-builder/agent-engine/use/langgraph
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LeadQualificationAgentApp:
    """
    Lead Qualification Agent for Vertex AI Agent Engine.
    
    This class wraps the LangGraph lead qualification workflow for deployment
    on Vertex AI Agent Engine.
    
    Attributes:
        project: GCP project ID
        location: GCP region
        use_llm: Whether to use LLM for scoring (default: True)
    """
    
    def __init__(
        self,
        project: str,
        location: str = "us-central1",
        use_llm: bool = True
    ):
        """
        Initialize the Lead Qualification Agent.
        
        Args:
            project: GCP project ID
            location: GCP region (default: us-central1)
            use_llm: Whether to use LLM for intelligent scoring
        """
        self.project = project
        self.location = location
        self.use_llm = use_llm
        self._graph = None
        
        logger.info(f"Initializing LeadQualificationAgentApp for project: {project}")
    
    def set_up(self):
        """
        Set up the agent (called once when agent is deployed).

        This method is called by Vertex AI Agent Engine during initialization.
        Import heavy dependencies here to avoid cold start delays.
        """
        logger.info("Setting up Lead Qualification Agent...")

        # Load environment variables
        load_dotenv()

        # Clear and reload settings to ensure env vars are picked up
        from src.config import get_settings, clear_settings_cache
        clear_settings_cache()
        settings = get_settings()

        # Log Salesforce config for debugging
        logger.info(f"Salesforce config - mode: {settings.salesforce.is_mock}, auth_type: {settings.salesforce.auth_type}")

        settings.configure_langsmith()
        
        # Import graph builder (heavy import)
        from src.graphs.lead_graph import build_lead_graph
        
        # Build and cache the graph
        self._graph = build_lead_graph()
        
        logger.info("Lead Qualification Agent set up complete!")
    
    def qualify_lead(
        self,
        lead_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """
        Qualify a Salesforce lead through the LangGraph workflow.
        
        This is the main entry point called by Vertex AI Agent Engine.
        
        Args:
            lead_data: Optional Salesforce lead data. If None, fetches newest lead.
                Expected fields: Id, Company, Title, Industry, Rating, 
                                 AnnualRevenue, NumberOfEmployees, LeadSource, etc.
            use_llm: Override for LLM usage. If None, uses instance default.
            
        Returns:
            dict with:
                - score: Lead qualification score (0.0 - 1.0)
                - routing: Owner assignment and priority
                - reasoning: AI reasoning for the decision (if LLM used)
                - actions_executed: List of actions taken
                - lead: Original lead data
                - enriched: SAP enrichment data
        """
        if self._graph is None:
            self.set_up()
        
        # Determine LLM usage
        should_use_llm = use_llm if use_llm is not None else self.use_llm
        
        logger.info(f"Qualifying lead with mode: {'LLM' if should_use_llm else 'Rules'}")
        
        # Import state creator
        from src.models.state import create_initial_lead_state
        from src.tools import salesforce
        
        # Authenticate with Salesforce
        salesforce.authenticate()
        
        # Create initial state
        initial_state = create_initial_lead_state(lead_data or {}, use_llm=should_use_llm)
        
        # Configure run for tracing
        lead_company = lead_data.get("Company", "Auto") if lead_data else "Auto"
        config = {
            "run_name": f"🎯 Lead: {lead_company} ({'LLM' if should_use_llm else 'Rules'})",
            "tags": ["lead-qualification", f"mode:{'llm' if should_use_llm else 'rules'}", "vertex-ai"],
            "metadata": {
                "workflow": "lead_qualification",
                "use_llm": should_use_llm,
                "project": self.project,
                "location": self.location
            }
        }
        
        # Execute graph
        final_state = self._graph.invoke(initial_state, config=config)
        
        # Format response
        llm_analysis = final_state.get("llm_analysis", {})
        route = final_state.get("route", {})
        
        result = {
            "score": final_state.get("score", 0.0),
            "routing": {
                "owner_type": route.get("owner_type", ""),
                "owner_id": route.get("owner_id", ""),
                "priority": route.get("priority", ""),
                "reason": route.get("reason", "")
            },
            "reasoning": llm_analysis.get("reasoning", "Rule-based scoring"),
            "confidence": llm_analysis.get("confidence", 1.0),
            "key_factors": llm_analysis.get("key_factors", []),
            "recommended_action": llm_analysis.get("recommended_action", ""),
            "model_used": llm_analysis.get("model_used", "rule-based"),
            "actions_executed": final_state.get("actions_done", []),
            "lead": final_state.get("lead", {}),
            "enriched": final_state.get("enriched", {})
        }
        
        logger.info(f"Lead qualification complete. Score: {result['score']:.2f}")
        return result


class TicketTriageAgentApp:
    """
    Ticket Triage Agent for Vertex AI Agent Engine.
    
    This class wraps the LangGraph ticket triage workflow for deployment
    on Vertex AI Agent Engine.
    """
    
    def __init__(
        self,
        project: str,
        location: str = "us-central1",
        use_llm: bool = True
    ):
        """
        Initialize the Ticket Triage Agent.
        
        Args:
            project: GCP project ID
            location: GCP region (default: us-central1)
            use_llm: Whether to use LLM for categorization
        """
        self.project = project
        self.location = location
        self.use_llm = use_llm
        self._graph = None
        
        logger.info(f"Initializing TicketTriageAgentApp for project: {project}")
    
    def set_up(self):
        """Set up the agent (called once when agent is deployed)."""
        logger.info("Setting up Ticket Triage Agent...")

        load_dotenv()

        # Clear and reload settings to ensure env vars are picked up
        from src.config import get_settings, clear_settings_cache
        clear_settings_cache()
        settings = get_settings()

        # Log Salesforce config for debugging
        logger.info(f"Salesforce config - mode: {settings.salesforce.is_mock}, auth_type: {settings.salesforce.auth_type}")

        settings.configure_langsmith()

        from src.graphs.ticket_graph import build_ticket_graph
        self._graph = build_ticket_graph()

        logger.info("Ticket Triage Agent set up complete!")
    
    def triage_ticket(
        self,
        case_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """
        Triage a Salesforce support case through the LangGraph workflow.
        
        Args:
            case_data: Optional Salesforce case data. If None, fetches newest case.
                Expected fields: Id, Subject, Description, Priority, AccountId, etc.
            use_llm: Override for LLM usage. If None, uses instance default.
            
        Returns:
            dict with:
                - category: Ticket category (howto, billing, outage, security, other)
                - decision: Action taken and response
                - reasoning: AI reasoning (if LLM used)
                - sentiment: Customer sentiment (if LLM used)
                - urgency: Urgency level
                - actions_executed: List of actions taken
        """
        if self._graph is None:
            self.set_up()
        
        should_use_llm = use_llm if use_llm is not None else self.use_llm
        
        logger.info(f"Triaging ticket with mode: {'LLM' if should_use_llm else 'Rules'}")
        
        from src.models.state import create_initial_ticket_state
        from src.tools import salesforce
        
        salesforce.authenticate()
        
        initial_state = create_initial_ticket_state(case_data or {}, use_llm=should_use_llm)
        
        case_subject = case_data.get("Subject", "Auto")[:50] if case_data else "Auto"
        config = {
            "run_name": f"🎫 Ticket: {case_subject} ({'LLM' if should_use_llm else 'Rules'})",
            "tags": ["ticket-triage", f"mode:{'llm' if should_use_llm else 'rules'}", "vertex-ai"],
            "metadata": {
                "workflow": "ticket_triage",
                "use_llm": should_use_llm,
                "project": self.project,
                "location": self.location
            }
        }
        
        final_state = self._graph.invoke(initial_state, config=config)
        
        llm_analysis = final_state.get("llm_analysis", {})
        decision = final_state.get("decision", {})
        
        result = {
            "category": final_state.get("category", "other"),
            "decision": {
                "action": decision.get("action", ""),
                "response": decision.get("response_template", ""),
                "escalation_reason": decision.get("escalation_reason"),
                "priority_change": decision.get("priority_change")
            },
            "reasoning": llm_analysis.get("reasoning", "Rule-based categorization"),
            "confidence": llm_analysis.get("confidence", 1.0),
            "sentiment": llm_analysis.get("sentiment", "neutral"),
            "urgency": llm_analysis.get("urgency", "medium"),
            "requires_escalation": llm_analysis.get("requires_escalation", False),
            "suggested_response": llm_analysis.get("suggested_response", ""),
            "model_used": llm_analysis.get("model_used", "rule-based"),
            "actions_executed": final_state.get("actions_done", []),
            "case": final_state.get("case", {}),
            "kb_suggestions": final_state.get("kb_suggestions", [])
        }
        
        logger.info(f"Ticket triage complete. Category: {result['category']}")
        return result


class ComplaintClassificationAgentApp:
    """
    Complaint Classification Agent for Vertex AI Agent Engine.
    
    Classifies customer complaints:
    - Product complaints → Email to product owner
    - IT Support → Redirect to IT portal
    """
    
    def __init__(
        self,
        project: str,
        location: str = "us-central1",
        use_llm: bool = True
    ):
        self.project = project
        self.location = location
        self.use_llm = use_llm
        self._graph = None
        
        logger.info(f"Initializing ComplaintClassificationAgentApp for project: {project}")
    
    def set_up(self):
        """Set up the agent."""
        logger.info("Setting up Complaint Classification Agent...")
        load_dotenv()

        # Clear and reload settings to ensure env vars are picked up
        from src.config import get_settings, clear_settings_cache
        clear_settings_cache()
        settings = get_settings()

        # Log Salesforce config for debugging
        logger.info(f"Salesforce config - mode: {settings.salesforce.is_mock}, auth_type: {settings.salesforce.auth_type}")

        settings.configure_langsmith()

        from src.graphs.complaint_graph import build_complaint_graph
        self._graph = build_complaint_graph()

        logger.info("Complaint Classification Agent set up complete!")
    
    def classify_complaint(
        self,
        case_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """
        Classify a complaint as Product-related or IT Support.

        Args:
            case_data: Salesforce case data
            use_llm: Override LLM usage

        Returns:
            Classification results with action taken
        """
        # DEBUG: Log what we received
        logger.info("=" * 60)
        logger.info("🔍 DEBUG: classify_complaint called")
        logger.info(f"   case_data type: {type(case_data)}")
        logger.info(f"   case_data: {case_data}")
        logger.info(f"   use_llm: {use_llm}")
        logger.info("=" * 60)

        if self._graph is None:
            self.set_up()

        should_use_llm = use_llm if use_llm is not None else self.use_llm

        from src.graphs.complaint_graph import create_initial_complaint_state
        from src.tools import salesforce

        salesforce.authenticate()

        # Ensure case_data is a dict with content
        if case_data is None:
            case_data = {}
            logger.warning("⚠️ case_data is None, using empty dict")

        logger.info(f"🔍 DEBUG: Creating initial state with case_data keys: {list(case_data.keys()) if case_data else 'empty'}")
        initial_state = create_initial_complaint_state(case_data or {}, use_llm=should_use_llm)
        
        config = {
            "run_name": f"📦 Complaint: {(case_data or {}).get('Subject', 'Auto')[:30]}",
            "tags": ["complaint-classification", "vertex-ai"],
            "metadata": {
                "workflow": "complaint_classification",
                "use_llm": should_use_llm,
                "project": self.project
            }
        }
        
        final_state = self._graph.invoke(initial_state, config=config)
        
        classification = final_state.get("classification", {})
        decision = final_state.get("decision", {})
        
        return {
            "is_product_complaint": classification.get("is_product_complaint", False),
            "is_it_support": classification.get("is_it_support", False),
            "product_category": classification.get("product_category", "none"),
            "product_name": classification.get("product_name", ""),
            "action_taken": decision.get("action", ""),
            "email_sent": decision.get("email_sent", False),
            "redirect_url": decision.get("redirect_url", ""),
            "reasoning": classification.get("reasoning", ""),
            "sentiment": classification.get("sentiment", "neutral"),
            "urgency": classification.get("urgency", "medium"),
            "confidence": classification.get("confidence", 0),
            "suggested_response": classification.get("suggested_response", ""),
            "actions_executed": final_state.get("actions_done", [])
        }


class BeldenSalesAgentApp:
    """
    Combined Belden Sales Agent for Vertex AI Agent Engine.
    
    This class combines Lead Qualification, Ticket Triage, and Complaint Classification
    workflows into a single deployable agent.
    
    Use Cases:
    1. Lead Qualification: Qualify Salesforce leads with SAP enrichment
    2. Ticket Triage: Categorize and route support tickets
    3. Complaint Classification: Classify Product complaints vs IT Support
    
    Example usage after deployment:
        agent.query("qualify_lead", lead_data={...})
        agent.query("triage_ticket", case_data={...})
        agent.query("classify_complaint", case_data={...})
    """
    
    def __init__(
        self,
        project: str,
        location: str = "us-central1",
        use_llm: bool = True
    ):
        """
        Initialize the Belden Sales Agent.
        
        Args:
            project: GCP project ID
            location: GCP region
            use_llm: Default LLM usage for all workflows
        """
        self.project = project
        self.location = location
        self.use_llm = use_llm
        
        self._lead_agent = None
        self._complaint_agent = None  # Replaces old ticket triage
        
        logger.info(f"Initializing BeldenSalesAgentApp for project: {project}")
    
    def set_up(self):
        """Set up all sub-agents."""
        logger.info("Setting up Belden Sales Agent (Lead Qualification + Complaint Classification)...")

        load_dotenv()

        # Clear and reload settings to ensure env vars are picked up
        from src.config import get_settings, clear_settings_cache
        clear_settings_cache()
        settings = get_settings()

        # Log Salesforce config for debugging
        logger.info(f"Salesforce config - mode: {settings.salesforce.is_mock}, auth_type: {settings.salesforce.auth_type}")

        settings.configure_langsmith()

        # Initialize Lead Qualification agent
        self._lead_agent = LeadQualificationAgentApp(
            project=self.project,
            location=self.location,
            use_llm=self.use_llm
        )
        self._lead_agent.set_up()
        
        # Initialize Complaint Classification agent (replaces old ticket triage)
        self._complaint_agent = ComplaintClassificationAgentApp(
            project=self.project,
            location=self.location,
            use_llm=self.use_llm
        )
        self._complaint_agent.set_up()
        
        logger.info("Belden Sales Agent set up complete!")
    
    def query(
        self,
        action: str,
        lead_data: Optional[dict] = None,
        case_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """
        Main query method for Agent Engine.

        Args:
            action: The action to perform:
                - "qualify_lead": Qualify a Salesforce lead (sends email if score >= 60%)
                - "classify_complaint" or "triage_ticket": Classify ticket as Product/IT
                  (ALWAYS sends AI analysis email)
                - "health": Health check
            lead_data: Lead data for qualify_lead action
            case_data: Case data for classify_complaint action
            use_llm: Override LLM usage

        Returns:
            dict with action results
        """
        # DEBUG: Log all incoming parameters
        logger.info("=" * 70)
        logger.info("🚀 AGENT QUERY RECEIVED")
        logger.info("=" * 70)
        logger.info(f"   action: {action}")
        logger.info(f"   lead_data type: {type(lead_data)}, value: {lead_data}")
        logger.info(f"   case_data type: {type(case_data)}, value: {case_data}")
        logger.info(f"   use_llm: {use_llm}")
        logger.info("=" * 70)

        if self._lead_agent is None:
            self.set_up()

        action = action.lower().strip()
        
        if action == "qualify_lead":
            return self._lead_agent.qualify_lead(lead_data=lead_data, use_llm=use_llm)
        
        elif action in ["triage_ticket", "classify_complaint"]:
            # Both actions now use the Complaint Classification workflow
            # which classifies tickets as Product complaint vs IT Support
            # and ALWAYS sends an email with the AI analysis
            return self._complaint_agent.classify_complaint(case_data=case_data, use_llm=use_llm)
        
        elif action == "health":
            return {
                "status": "healthy",
                "project": self.project,
                "location": self.location,
                "workflows": ["lead_qualification", "complaint_classification"],
                "actions": {
                    "qualify_lead": "Qualify Salesforce leads, email if score >= 60%",
                    "classify_complaint": "Classify as Product/IT, ALWAYS email AI analysis",
                    "triage_ticket": "Alias for classify_complaint"
                },
                "llm_enabled": self.use_llm
            }
        
        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": ["qualify_lead", "classify_complaint", "triage_ticket", "health"]
            }
    
    # Convenience methods for direct invocation
    def qualify_lead(
        self,
        lead_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """Convenience method for lead qualification."""
        return self.query("qualify_lead", lead_data=lead_data, use_llm=use_llm)
    
    def triage_ticket(
        self,
        case_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """
        Convenience method for ticket classification.
        
        Now uses Complaint Classification workflow which:
        - Classifies ticket as Product complaint vs IT Support
        - ALWAYS sends email with full AI analysis
        """
        return self.query("classify_complaint", case_data=case_data, use_llm=use_llm)
    
    def classify_complaint(
        self,
        case_data: Optional[dict] = None,
        use_llm: Optional[bool] = None
    ) -> dict:
        """
        Convenience method for complaint classification.
        
        Classifies if a ticket is a Product complaint or IT Support request.
        
        Key Actions:
        - ALWAYS sends email with full AI analysis (reasoning, sentiment, urgency)
        - Product complaint → Includes product details in email
        - IT Support → Includes IT portal redirect URL in email
        """
        return self.query("classify_complaint", case_data=case_data, use_llm=use_llm)
