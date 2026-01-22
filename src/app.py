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
        
        # Import and configure LangSmith
        from src.config import get_settings
        settings = get_settings()
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
        
        from src.config import get_settings
        settings = get_settings()
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


class BeldenSalesAgentApp:
    """
    Combined Belden Sales Agent for Vertex AI Agent Engine.
    
    This class combines both Lead Qualification and Ticket Triage workflows
    into a single deployable agent, following Belden's enterprise sales workflow.
    
    Use Cases:
    1. Lead Qualification: Qualify Salesforce leads with SAP enrichment
    2. Ticket Triage: Categorize and route support tickets
    
    Example usage after deployment:
        agent.query("qualify_lead", lead_data={...})
        agent.query("triage_ticket", case_data={...})
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
        self._ticket_agent = None
        
        logger.info(f"Initializing BeldenSalesAgentApp for project: {project}")
    
    def set_up(self):
        """Set up both sub-agents."""
        logger.info("Setting up Belden Sales Agent (Lead + Ticket workflows)...")
        
        load_dotenv()
        
        from src.config import get_settings
        settings = get_settings()
        settings.configure_langsmith()
        
        # Initialize both agents
        self._lead_agent = LeadQualificationAgentApp(
            project=self.project,
            location=self.location,
            use_llm=self.use_llm
        )
        self._lead_agent.set_up()
        
        self._ticket_agent = TicketTriageAgentApp(
            project=self.project,
            location=self.location,
            use_llm=self.use_llm
        )
        self._ticket_agent.set_up()
        
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
                - "qualify_lead": Run lead qualification workflow
                - "triage_ticket": Run ticket triage workflow
                - "health": Health check
            lead_data: Lead data for qualify_lead action
            case_data: Case data for triage_ticket action
            use_llm: Override LLM usage
            
        Returns:
            dict with action results
        """
        if self._lead_agent is None:
            self.set_up()
        
        action = action.lower().strip()
        
        if action == "qualify_lead":
            return self._lead_agent.qualify_lead(lead_data=lead_data, use_llm=use_llm)
        
        elif action == "triage_ticket":
            return self._ticket_agent.triage_ticket(case_data=case_data, use_llm=use_llm)
        
        elif action == "health":
            return {
                "status": "healthy",
                "project": self.project,
                "location": self.location,
                "workflows": ["lead_qualification", "ticket_triage"],
                "llm_enabled": self.use_llm
            }
        
        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": ["qualify_lead", "triage_ticket", "health"]
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
        """Convenience method for ticket triage."""
        return self.query("triage_ticket", case_data=case_data, use_llm=use_llm)
