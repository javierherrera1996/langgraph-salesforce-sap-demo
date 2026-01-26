"""
Script para ver trazas recientes del agente en LangSmith.

Usage:
    python scripts/view_traces.py --limit 10
    python scripts/view_traces.py --project belden-sales-agent-prod
    python scripts/view_traces.py --workflow lead_qualification
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

try:
    from langsmith import Client
except ImportError:
    print("❌ langsmith no está instalado. Instala con: pip install langsmith")
    sys.exit(1)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            mins = diff.seconds // 60
            return f"{mins}m ago"
        else:
            return "just now"
    except:
        return timestamp


def print_trace_summary(trace: dict, index: int):
    """Print a formatted summary of a trace."""
    run_id = trace.get("id", "unknown")
    name = trace.get("name", "Unknown")
    status = trace.get("status", "unknown")
    start_time = trace.get("start_time", "")
    end_time = trace.get("end_time", "")
    
    # Calculate duration
    duration = "N/A"
    if start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration = format_duration((end - start).total_seconds())
        except:
            pass
    
    # Get metadata
    metadata = trace.get("metadata", {})
    workflow = metadata.get("workflow", "unknown")
    use_llm = metadata.get("use_llm", False)
    mode = "🤖 LLM" if use_llm else "📊 Rules"
    
    # Get tags
    tags = trace.get("tags", [])
    tag_str = ", ".join(tags[:3]) if tags else "no tags"
    
    # Status emoji
    status_emoji = {
        "success": "✅",
        "error": "❌",
        "pending": "⏳",
        "cancelled": "🚫"
    }.get(status.lower(), "❓")
    
    print(f"\n{'='*80}")
    print(f"#{index} {status_emoji} {name}")
    print(f"{'─'*80}")
    print(f"  Run ID:     {run_id}")
    print(f"  Workflow:   {workflow}")
    print(f"  Mode:       {mode}")
    print(f"  Status:     {status}")
    print(f"  Duration:   {duration}")
    print(f"  Time:       {format_timestamp(start_time)}")
    print(f"  Tags:       {tag_str}")
    
    # Print errors if any
    if status.lower() == "error":
        error = trace.get("error", "Unknown error")
        print(f"  ❌ Error:    {error}")
    
    # Print LangSmith URL
    project = trace.get("project_name", "default")
    print(f"  🔗 View:     https://smith.langchain.com/o/default/projects/p/{project}/r/{run_id}")


def main():
    parser = argparse.ArgumentParser(
        description="View recent traces from LangSmith",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View last 10 traces
  python scripts/view_traces.py --limit 10
  
  # View traces from specific project
  python scripts/view_traces.py --project belden-sales-agent-prod
  
  # View traces for specific workflow
  python scripts/view_traces.py --workflow lead_qualification
  
  # View traces from last 24 hours
  python scripts/view_traces.py --hours 24
        """
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of traces to show (default: 10)"
    )
    
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="LangSmith project name (default: from LANGCHAIN_PROJECT env var)"
    )
    
    parser.add_argument(
        "--workflow",
        type=str,
        default=None,
        help="Filter by workflow name (lead_qualification, complaint_classification)"
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        default=None,
        help="Only show traces from last N hours"
    )
    
    parser.add_argument(
        "--status",
        type=str,
        choices=["success", "error", "pending"],
        default=None,
        help="Filter by status"
    )
    
    args = parser.parse_args()
    
    # Get LangSmith API key
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("❌ LANGSMITH_API_KEY is not configured in .env")
        print("   Add: LANGSMITH_API_KEY=lsv2_your-api-key")
        sys.exit(1)

    # Get project
    project = args.project or os.getenv("LANGCHAIN_PROJECT", "default")

    print("🔍 Connecting to LangSmith...")
    print(f"   Project: {project}")

    try:
        client = Client(api_key=api_key)
    except Exception as e:
        print(f"❌ Error connecting to LangSmith: {e}")
        sys.exit(1)
    
    # Build filters
    filters = {}
    
    if args.workflow:
        filters["metadata"] = {"workflow": args.workflow}
    
    if args.status:
        filters["status"] = args.status
    
    # Calculate time range
    start_time = None
    if args.hours:
        start_time = datetime.utcnow() - timedelta(hours=args.hours)
    
    print(f"\n📊 Buscando trazas...")
    if start_time:
        print(f"   Desde: {start_time.isoformat()}")
    if args.workflow:
        print(f"   Workflow: {args.workflow}")
    if args.status:
        print(f"   Status: {args.status}")
    
    try:
        # List runs
        runs = client.list_runs(
            project_name=project,
            limit=args.limit,
            start_time=start_time,
            **filters
        )
        
        traces = list(runs)
        
        if not traces:
            print("\n⚠️  No se encontraron trazas con los filtros especificados")
            print("\n💡 Sugerencias:")
            print("   - Verifica que el proyecto sea correcto")
            print("   - Intenta sin filtros: python scripts/view_traces.py")
            print("   - Verifica que el agente esté enviando trazas")
            return
        
        print(f"\n✅ Encontradas {len(traces)} trazas\n")
        
        # Print summaries
        for i, trace in enumerate(traces, 1):
            print_trace_summary(trace, i)
        
        print(f"\n{'='*80}")
        print(f"📊 Total: {len(traces)} trazas")
        print(f"🔗 Dashboard: https://smith.langchain.com/o/default/projects/p/{project}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error obteniendo trazas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
