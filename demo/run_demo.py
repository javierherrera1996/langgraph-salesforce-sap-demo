#!/usr/bin/env python3
"""
🎬 Belden AI Sales Agent - Interactive Demo Script

Este script facilita ejecutar la demo mostrando los resultados
de manera visual e impactante.

Uso:
    python demo/run_demo.py --mode local    # Prueba local (FastAPI)
    python demo/run_demo.py --mode cloud    # Vertex AI Agent Engine
"""

import json
import argparse
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.ENDC}\n")

def print_section(text):
    print(f"\n{Colors.CYAN}{'-'*60}")
    print(f"  {text}")
    print(f"{'-'*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_result(label, value, color=Colors.CYAN):
    print(f"   {Colors.BOLD}{label}:{Colors.ENDC} {color}{value}{Colors.ENDC}")

def print_reasoning(reasoning):
    """Pretty print AI reasoning"""
    print(f"\n{Colors.YELLOW}🤖 AI REASONING:{Colors.ENDC}")
    print(f"{Colors.YELLOW}{'-'*50}{Colors.ENDC}")
    lines = reasoning.split('\n') if reasoning else ["No reasoning provided"]
    for line in lines[:10]:  # Limit to 10 lines
        print(f"   {line}")
    if len(lines) > 10:
        print(f"   ... ({len(lines)-10} more lines)")
    print(f"{Colors.YELLOW}{'-'*50}{Colors.ENDC}")


def load_scenarios():
    """Load demo scenarios from JSON"""
    script_dir = Path(__file__).parent
    scenarios_file = script_dir / "demo_scenarios.json"
    
    with open(scenarios_file, 'r') as f:
        return json.load(f)


def call_local_api(endpoint, payload):
    """Call local FastAPI server"""
    import requests
    
    url = f"http://localhost:8000{endpoint}"
    response = requests.post(url, json=payload, timeout=120)
    return response.json()


def call_cloud_agent(payload):
    """Call Vertex AI Agent Engine"""
    try:
        from vertexai import agent_engines
        import vertexai
        
        vertexai.init(
            project="logical-hallway-485016-r7",
            location="us-central1"
        )
        
        agent = agent_engines.get(
            "projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/180545306838958080"
        )
        
        return agent.query(**payload)
        
    except Exception as e:
        return {"error": str(e)}


def run_lead_demo(lead_scenario, mode="local"):
    """Run a single lead qualification demo"""
    print_section(f"🎯 {lead_scenario['name']}")
    print_info(lead_scenario['description'])
    print()
    
    # Show input
    lead_data = lead_scenario['input']['lead_data']
    print(f"   📋 Lead: {lead_data.get('FirstName', '')} {lead_data.get('LastName', '')} - {lead_data.get('Title', '')}")
    print(f"   🏢 Company: {lead_data.get('Company', '')} ({lead_data.get('Industry', '')})")
    print(f"   💰 Revenue: ${lead_data.get('AnnualRevenue', 0):,.0f} | Employees: {lead_data.get('NumberOfEmployees', 0)}")
    print(f"   🌡️  Rating: {lead_data.get('Rating', '')} | Source: {lead_data.get('LeadSource', '')}")
    print()
    
    # Show expected result
    print_info(f"Expected: {lead_scenario['expected_result']}")
    print()
    
    # Call API
    print("   ⏳ Processing...")
    start_time = time.time()
    
    if mode == "local":
        result = call_local_api("/run/lead", {
            "lead": lead_data,
            "use_llm": True
        })
    else:
        result = call_cloud_agent(lead_scenario['input'])
    
    elapsed = time.time() - start_time
    print(f"   ⏱️  Completed in {elapsed:.2f}s\n")
    
    # Show results
    if "error" in result:
        print(f"{Colors.RED}❌ Error: {result['error']}{Colors.ENDC}")
        return
    
    # Extract score and routing
    score = result.get('score', result.get('summary', {}).get('score', 0))
    routing = result.get('routing', result.get('summary', {}).get('routing', {}))
    reasoning = result.get('reasoning', '')
    
    # Determine color based on score
    if score >= 0.75:
        score_color = Colors.GREEN
        priority = "P1 🔥"
    elif score >= 0.45:
        score_color = Colors.YELLOW
        priority = "P2 ⚡"
    else:
        score_color = Colors.RED
        priority = "P3 ❄️"
    
    print_result("Score", f"{score:.2f}", score_color)
    print_result("Priority", priority, score_color)
    print_result("Owner Type", routing.get('owner_type', 'N/A'))
    print_result("Model", result.get('model_used', 'N/A'))
    
    # Show reasoning
    if reasoning:
        print_reasoning(reasoning)
    
    # Talking points
    print(f"\n{Colors.CYAN}💡 Talking Points:{Colors.ENDC}")
    for point in lead_scenario.get('talking_points', [])[:3]:
        print(f"   • {point}")
    
    return result


def run_ticket_demo(ticket_scenario, mode="local"):
    """Run a single ticket triage demo"""
    print_section(f"🎫 {ticket_scenario['name']}")
    print_info(ticket_scenario['description'])
    print()
    
    # Show input
    case_data = ticket_scenario['input']['case_data']
    print(f"   📋 Case: {case_data.get('CaseNumber', '')}")
    print(f"   📝 Subject: {case_data.get('Subject', '')[:60]}...")
    print(f"   🔴 Priority: {case_data.get('Priority', '')} | Origin: {case_data.get('Origin', '')}")
    print()
    
    # Show expected result
    print_info(f"Expected: {ticket_scenario['expected_result']}")
    print()
    
    # Call API
    print("   ⏳ Processing...")
    start_time = time.time()
    
    if mode == "local":
        result = call_local_api("/run/ticket", {
            "case": case_data,
            "use_llm": True
        })
    else:
        result = call_cloud_agent(ticket_scenario['input'])
    
    elapsed = time.time() - start_time
    print(f"   ⏱️  Completed in {elapsed:.2f}s\n")
    
    # Show results
    if "error" in result:
        print(f"{Colors.RED}❌ Error: {result['error']}{Colors.ENDC}")
        return
    
    category = result.get('category', result.get('summary', {}).get('category', 'N/A'))
    decision = result.get('decision', {})
    reasoning = result.get('reasoning', '')
    sentiment = result.get('sentiment', 'N/A')
    urgency = result.get('urgency', 'N/A')
    
    # Category colors
    category_colors = {
        'outage': Colors.RED,
        'security': Colors.RED,
        'billing': Colors.YELLOW,
        'howto': Colors.GREEN,
        'other': Colors.CYAN
    }
    cat_color = category_colors.get(category, Colors.CYAN)
    
    print_result("Category", category.upper(), cat_color)
    print_result("Action", decision.get('action', 'N/A'))
    print_result("Sentiment", sentiment)
    print_result("Urgency", urgency, Colors.RED if urgency in ['critical', 'high'] else Colors.YELLOW)
    
    if result.get('requires_escalation'):
        print(f"   {Colors.RED}🚨 ESCALATION REQUIRED{Colors.ENDC}")
    
    # Show reasoning
    if reasoning:
        print_reasoning(reasoning)
    
    # Suggested response preview
    suggested = result.get('suggested_response', '')
    if suggested:
        print(f"\n{Colors.GREEN}📝 Suggested Response Preview:{Colors.ENDC}")
        print(f"   {suggested[:150]}...")
    
    # Talking points
    print(f"\n{Colors.CYAN}💡 Talking Points:{Colors.ENDC}")
    for point in ticket_scenario.get('talking_points', [])[:3]:
        print(f"   • {point}")
    
    return result


def run_full_demo(mode="local"):
    """Run the complete demo sequence"""
    scenarios = load_scenarios()
    
    print_header("🎬 BELDEN AI SALES AGENT - DEMO")
    print(f"   Mode: {'☁️  Vertex AI Cloud' if mode == 'cloud' else '💻 Local FastAPI'}")
    print(f"   Scenarios: {len(scenarios['scenarios']['lead_qualification']['demo_leads'])} Leads, "
          f"{len(scenarios['scenarios']['ticket_triage']['demo_tickets'])} Tickets")
    
    input(f"\n{Colors.YELLOW}Press ENTER to start the demo...{Colors.ENDC}")
    
    # Lead Qualification Demos
    print_header("PARTE 1: LEAD QUALIFICATION & ROUTING")
    print("   🎯 El AI analiza leads y decide automáticamente la prioridad y asignación\n")
    
    leads = scenarios['scenarios']['lead_qualification']['demo_leads']
    for i, lead in enumerate(leads):
        input(f"\n{Colors.YELLOW}Press ENTER for Lead Demo {i+1}/{len(leads)}...{Colors.ENDC}")
        run_lead_demo(lead, mode)
    
    # Ticket Triage Demos
    print_header("PARTE 2: TICKET TRIAGE & ROUTING")
    print("   🎫 El AI categoriza tickets y toma acciones automáticas\n")
    
    tickets = scenarios['scenarios']['ticket_triage']['demo_tickets']
    for i, ticket in enumerate(tickets):
        input(f"\n{Colors.YELLOW}Press ENTER for Ticket Demo {i+1}/{len(tickets)}...{Colors.ENDC}")
        run_ticket_demo(ticket, mode)
    
    # Summary
    print_header("📊 DEMO COMPLETE - KEY MESSAGES")
    for msg in scenarios['key_messages']:
        print(f"   {msg}")
    
    print(f"\n{Colors.GREEN}{'='*70}")
    print("   🎉 ¡Demo completada exitosamente!")
    print(f"{'='*70}{Colors.ENDC}\n")


def run_single_scenario(scenario_type, scenario_index, mode="local"):
    """Run a single specific scenario"""
    scenarios = load_scenarios()
    
    if scenario_type == "lead":
        leads = scenarios['scenarios']['lead_qualification']['demo_leads']
        if scenario_index < len(leads):
            run_lead_demo(leads[scenario_index], mode)
        else:
            print(f"Lead index {scenario_index} not found. Available: 0-{len(leads)-1}")
    
    elif scenario_type == "ticket":
        tickets = scenarios['scenarios']['ticket_triage']['demo_tickets']
        if scenario_index < len(tickets):
            run_ticket_demo(tickets[scenario_index], mode)
        else:
            print(f"Ticket index {scenario_index} not found. Available: 0-{len(tickets)-1}")


def main():
    parser = argparse.ArgumentParser(description="Belden AI Agent Demo Runner")
    parser.add_argument("--mode", choices=["local", "cloud"], default="cloud",
                        help="Run mode: local (FastAPI) or cloud (Vertex AI)")
    parser.add_argument("--scenario", type=str, help="Run single scenario: lead:0, ticket:1, etc.")
    parser.add_argument("--list", action="store_true", help="List all available scenarios")
    
    args = parser.parse_args()
    
    if args.list:
        scenarios = load_scenarios()
        print_header("Available Demo Scenarios")
        
        print("\n🎯 LEADS:")
        for i, lead in enumerate(scenarios['scenarios']['lead_qualification']['demo_leads']):
            print(f"   lead:{i} - {lead['name']}")
        
        print("\n🎫 TICKETS:")
        for i, ticket in enumerate(scenarios['scenarios']['ticket_triage']['demo_tickets']):
            print(f"   ticket:{i} - {ticket['name']}")
        
        print(f"\nUsage: python demo/run_demo.py --scenario lead:0 --mode cloud")
        return
    
    if args.scenario:
        parts = args.scenario.split(":")
        if len(parts) == 2:
            run_single_scenario(parts[0], int(parts[1]), args.mode)
        else:
            print("Invalid scenario format. Use: lead:0, ticket:1, etc.")
        return
    
    run_full_demo(args.mode)


if __name__ == "__main__":
    main()
