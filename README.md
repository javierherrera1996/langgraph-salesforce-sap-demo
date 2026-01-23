# LangGraph Salesforce SAP Demo

Enterprise-grade AI orchestration demo using **LangGraph** to orchestrate **Salesforce CRM** and **SAP** for intelligent automation.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Overview

This project demonstrates a **production-like AI orchestration system** that:

- **Qualifies and routes leads** using deterministic scoring + SAP enrichment
- **Triages support tickets** with automated categorization and KB suggestions
- **Executes actions** on Salesforce (update records, assign owners, create tasks)
- **Integrates with SAP** for business context (customers, orders, service history)

### Why LangGraph?

LangGraph provides:
- **Explicit state management** - Full visibility into workflow state
- **Deterministic routing** - No hidden LLM decisions; all logic is traceable
- **LangSmith integration** - Complete observability and debugging
- **Production-ready** - Designed for enterprise deployment

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Runtime                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐       ┌─────────────────────┐         │
│  │  Lead Qualification │       │   Ticket Triage     │         │
│  │       Graph         │       │       Graph         │         │
│  ├─────────────────────┤       ├─────────────────────┤         │
│  │ 1. FetchLead        │       │ 1. FetchTicket      │         │
│  │ 2. EnrichLead (SAP) │       │ 2. CategorizeTicket │         │
│  │ 3. ScoreLead        │       │ 3. RetrieveContext  │         │
│  │ 4. DecideRouting    │       │ 4. DecideAction     │         │
│  │ 5. ExecuteActions   │       │ 5. ExecuteActions   │         │
│  └─────────────────────┘       └─────────────────────┘         │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                           Tools Layer                            │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │  Salesforce   │  │     SAP       │  │  Scoring / KB     │   │
│  │    Tools      │  │    Tools      │  │     Tools         │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Setup

```bash
# Clone the repository
cd langgraph-salesforce-sap-demo

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env
```

### Configure Environment

Edit `.env` with your credentials:

```env
# Salesforce (Developer Edition)
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token
SALESFORCE_INSTANCE_URL=https://login.salesforce.com

# SAP (set to "mock" for demo without SAP)
SAP_MODE=mock

# LangSmith (for tracing)
LANGSMITH_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=langgraph-salesforce-sap-demo

# Owner IDs (Salesforce User IDs for routing)
DEFAULT_AE_OWNER_ID=005XXXXXXXXXXXXXXX
DEFAULT_SDR_OWNER_ID=005XXXXXXXXXXXXXXX
DEFAULT_NURTURE_OWNER_ID=005XXXXXXXXXXXXXXX
DEFAULT_ESCALATION_OWNER_ID=005XXXXXXXXXXXXXXX
```

## 🚀 Running the Demo

### Start the Server

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload

# Or production mode
python -m src.main
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎮 Demo Workflows

### Use Case 1: Lead Qualification & Routing

**Scenario**: A new lead is created in Salesforce. The system automatically qualifies, scores, and routes the lead.

```bash
# Process the newest lead
curl -X POST http://localhost:8000/run/lead

# Process a specific lead
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "00Q5g00000MockLd1"}'
```

**What Happens**:
1. **FetchLead**: Retrieves lead from Salesforce
2. **EnrichLead**: Looks up SAP business partner, gets order history
3. **ScoreLead**: Calculates qualification score based on:
   - Company size (employees)
   - Annual revenue
   - Lead rating (Hot/Warm/Cold)
   - Lead source
   - Title seniority
   - SAP enrichment bonus
4. **DecideRouting**: Routes based on score:
   - ≥ 0.75 → Account Executive (P1)
   - 0.45-0.74 → Sales Dev Rep (P2)
   - < 0.45 → Nurture Campaign (P3)
5. **ExecuteActions**:
   - Assigns lead to new owner
   - Updates lead status
   - Creates follow-up task
   - Creates SAP note (if BP exists)

**Example Response**:
```json
{
  "success": true,
  "workflow": "lead_qualification",
  "execution_time_ms": 342.5,
  "summary": {
    "lead_id": "00Q5g00000MockLd1",
    "company": "Acme Corporation",
    "score": 0.8125,
    "routing": {
      "owner_type": "AE",
      "priority": "P1",
      "reason": "High-value lead (score: 0.81) - immediate AE engagement"
    },
    "sap_enriched": true,
    "total_actions": 4
  },
  "actions_executed": [
    "fetch_lead:fetched:00Q5g00000MockLd1",
    "enrich_lead:success:bp=BP1234567:orders=3",
    "score_lead:score=0.8125",
    "decide_routing:AE:P1",
    "sf:assign_owner:005XXXXXXXXXXXXXXX",
    "sf:update_status:Working - Contacted",
    "sf:create_task:00T5g00000MockLd1",
    "sap:create_note:BP1234567"
  ]
}
```

### Use Case 2: Ticket Triage

**Scenario**: A support ticket is submitted. The system categorizes it and takes appropriate action.

```bash
# Process the newest case
curl -X POST http://localhost:8000/run/ticket

# Process a specific case
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{"case_id": "5005g00000MockCs1"}'
```

**What Happens**:
1. **FetchTicket**: Retrieves case from Salesforce
2. **CategorizeTicket**: Classifies into:
   - `howto` - How-to questions
   - `billing` - Billing/payment issues
   - `outage` - System outages
   - `security` - Security concerns
   - `other` - Everything else
3. **RetrieveContext**: Gets SAP order context
4. **DecideAction**: Based on category:
   - `howto` → Auto-reply with KB articles
   - `billing` → Request more information
   - `outage` → Escalate to incident team
   - `security` → Escalate to security team
5. **ExecuteActions**:
   - Posts case comment
   - Updates case status
   - Changes owner (if escalated)
   - Creates SAP note (if relevant)

**Example Response**:
```json
{
  "success": true,
  "workflow": "ticket_triage",
  "execution_time_ms": 287.3,
  "summary": {
    "case_id": "5005g00000MockCs2",
    "case_number": "00001235",
    "subject": "System is down - URGENT",
    "category": "outage",
    "action": "escalate",
    "escalated": true,
    "priority_changed": "High",
    "kb_articles_suggested": 2,
    "total_actions": 3
  }
}
```

## 🔍 LangSmith Tracing

### Enable Tracing

Ensure these environment variables are set:

```env
LANGSMITH_API_KEY=your_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=langgraph-salesforce-sap-demo
```

### View Traces

1. Go to [LangSmith](https://smith.langchain.com)
2. Select your project: `langgraph-salesforce-sap-demo`
3. Click on a trace to see:
   - **Graph visualization** - See node execution order
   - **State snapshots** - Inspect state at each node
   - **Timing** - Identify bottlenecks
   - **Inputs/Outputs** - Debug data flow

### What to Look For

- **Node execution sequence** - Verify flow is correct
- **State changes** - See how data transforms
- **Action logs** - Confirm Salesforce/SAP operations
- **Error traces** - Debug failures

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `POST` | `/run/lead` | Run lead qualification |
| `POST` | `/run/ticket` | Run ticket triage |
| `GET` | `/graphs/lead` | Lead graph info |
| `GET` | `/graphs/ticket` | Ticket graph info |
| `GET` | `/demo/leads` | List demo leads |
| `GET` | `/demo/cases` | List demo cases |

## 🛡️ Guardrails

This system implements several guardrails:

1. **Input Sanitization**: All text inputs are sanitized before Salesforce/SAP operations
2. **No Prompt Injection**: Tool functions are pure - no LLM interpretation of user input
3. **Deterministic Routing**: All decisions are rule-based, not LLM-generated
4. **Action Validation**: Only state-derived actions are executed
5. **Logging**: Full audit trail of all operations

## 📁 Project Structure

```
langgraph-salesforce-sap-demo/
├── README.md                 # This file
├── pyproject.toml            # Python dependencies
├── .env.example              # Environment template
├── langgraph.json            # LangSmith graph configuration
└── src/
    ├── main.py               # FastAPI application
    ├── config.py             # Configuration management
    ├── api/
    │   └── routes.py         # HTTP endpoints
    ├── graphs/
    │   ├── lead_graph.py     # Lead qualification workflow
    │   └── ticket_graph.py   # Ticket triage workflow
    ├── models/
    │   └── state.py          # State schemas (TypedDict)
    └── tools/
        ├── salesforce.py     # Salesforce REST API
        ├── sap.py            # SAP OData API
        ├── scoring.py        # Lead scoring logic
        └── kb.py             # Knowledge base & categorization
```

## 🔧 Customization

### Adding a New Graph

1. Create `src/graphs/your_graph.py`
2. Define state in `src/models/state.py`
3. Implement nodes as pure functions
4. Build graph with `StateGraph`
5. Add to `langgraph.json`
6. Create endpoint in `routes.py`

### Modifying Scoring Logic

Edit `src/tools/scoring.py`:
- Adjust `SCORING_WEIGHTS` for different criteria
- Modify `INDUSTRY_MULTIPLIERS` for vertical adjustments
- Change routing thresholds in `determine_routing()`

### Customizing Ticket Categories

Edit `src/tools/kb.py`:
- Add patterns to `CATEGORY_PATTERNS`
- Add articles to `KB_ARTICLES`
- Modify response templates in `RESPONSE_TEMPLATES`

## 🚢 Deployment

### Option 1: Vertex AI Agent Engine (Recommended)

Deploy to Google Cloud's **Vertex AI Agent Engine** for production-grade scaling.

#### Prerequisites

1. **Google Cloud Project** with Vertex AI API enabled
2. **Service Account** with Agent Engine Admin permissions
3. **GCS Bucket** for staging artifacts

#### Setup

```bash
# Authenticate with GCP
gcloud auth application-default login

# Enable required APIs
gcloud services enable aiplatform.googleapis.com

# Create staging bucket
gsutil mb gs://your-staging-bucket
```

#### Configure Environment

Copy `env.gcp.example` to `.env` and configure:

```env
# GCP Settings (REQUIRED)
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
STAGING_BUCKET=gs://your-staging-bucket

# API Keys
OPENAI_API_KEY=sk-your-openai-key
LANGSMITH_API_KEY=lsv2_your_langsmith_key

# Salesforce (mock or real)
SALESFORCE_MODE=mock
# ... other variables
```

#### Deploy

```bash
# Deploy combined agent (Lead + Ticket workflows)
python deploy_agent.py

# Deploy only lead qualification
python deploy_agent.py --mode lead

# Deploy only ticket triage
python deploy_agent.py --mode ticket

# Test deployed agent
python deploy_agent.py --mode test --resource-name <AGENT_RESOURCE_NAME>
```

#### Using the Deployed Agent

```python
from vertexai import agent_engines

# Get deployed agent
agent = agent_engines.get("projects/PROJECT/locations/LOCATION/reasoningEngines/AGENT_ID")

# Qualify a lead
result = agent.qualify_lead(
    lead_data={
        "Id": "00Q000001",
        "Company": "Acme Corp",
        "Title": "CTO",
        "Industry": "Technology",
        "Rating": "Hot",
        "AnnualRevenue": 5000000
    },
    use_llm=True
)

# Triage a ticket
result = agent.triage_ticket(
    case_data={
        "Id": "500000001",
        "Subject": "Network connectivity issues",
        "Description": "Our Belden switches are dropping packets"
    }
)
```

### Option 2: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 3: Cloud Run

```bash
# Build and deploy to Cloud Run
gcloud run deploy langgraph-salesforce-sap \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment Variables

For production, set:
- `APP_DEBUG=false`
- `LOG_LEVEL=INFO`
- All Salesforce/SAP credentials
- LangSmith API key
- GCP credentials (for Agent Engine)

## 🎨 Visualización y Depuración

### LangGraph Studio (Local)

Visualiza y depura tus grafos localmente con LangGraph Studio:

```bash
# Opción 1: Usar el script helper
./scripts/start_studio.sh

# Opción 2: Manual
langgraph dev
```

Luego abre `http://localhost:8123` en tu navegador.

**Características:**
- ✅ Visualización interactiva de grafos
- ✅ Depuración paso a paso
- ✅ Edición de estado en tiempo real
- ✅ Pruebas con datos de ejemplo

**Ver documentación completa:** [`docs/LANGGRAPH_STUDIO_SETUP.md`](docs/LANGGRAPH_STUDIO_SETUP.md)

### LangSmith Dashboard (Agente Desplegado)

Monitorea el agente desplegado en Vertex AI:

1. **Configurar LangSmith en Vertex AI:**
   ```bash
   # Actualizar variables de entorno
   python update_env_vars.py
   ```
   
   Asegúrate de incluir:
   ```env
   LANGSMITH_API_KEY=lsv2_tu-api-key
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=belden-sales-agent-prod
   ```

2. **Ver trazas recientes:**
   ```bash
   # Ver últimas 10 ejecuciones
   python scripts/view_traces.py --limit 10
   
   # Filtrar por workflow
   python scripts/view_traces.py --workflow lead_qualification
   
   # Ver solo errores
   python scripts/view_traces.py --status error
   ```

3. **Abrir Dashboard:**
   - Ve a [LangSmith Dashboard](https://smith.langchain.com)
   - Selecciona tu proyecto
   - Explora ejecuciones, grafos, y LLM calls

**Ver documentación completa:** [`docs/LANGGRAPH_STUDIO_SETUP.md`](docs/LANGGRAPH_STUDIO_SETUP.md)

### Comparación: Local vs Desplegado

| Característica | LangGraph Studio (Local) | LangSmith (Desplegado) |
|----------------|-------------------------|------------------------|
| Visualización de grafos | ✅ Interactiva | ✅ Con trazas |
| Depuración paso a paso | ✅ Sí | ⚠️ Solo trazas |
| Edición de estado | ✅ Sí | ❌ No |
| Monitoreo producción | ❌ No | ✅ Sí |
| Comparar ejecuciones | ⚠️ Limitado | ✅ Sí |
| Análisis de rendimiento | ⚠️ Básico | ✅ Avanzado |

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

Built with ❤️ using [LangGraph](https://github.com/langchain-ai/langgraph), [FastAPI](https://fastapi.tiangolo.com/), and [LangChain](https://langchain.com/)
