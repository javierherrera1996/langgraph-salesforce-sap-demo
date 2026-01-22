# 🚀 Deploy desde Cloud Shell

Guía paso a paso para desplegar el Belden Sales Agent en Vertex AI Agent Engine usando Cloud Shell.

## Pre-requisitos

1. Cuenta de Google Cloud con billing habilitado
2. Proyecto de GCP creado
3. APIs habilitadas (Vertex AI)

---

## Paso 1: Abrir Cloud Shell

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Haz clic en el ícono de **Cloud Shell** (terminal) en la esquina superior derecha
3. Espera a que se inicie el entorno

---

## Paso 2: Configurar el proyecto

```bash
# Establecer tu proyecto
export PROJECT_ID="tu-proyecto-gcp"
gcloud config set project $PROJECT_ID

# Verificar
gcloud config get project
```

---

## Paso 3: Habilitar APIs necesarias

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

---

## Paso 4: Crear bucket de staging

```bash
# Crear bucket para staging de artifacts
export STAGING_BUCKET="gs://${PROJECT_ID}-agent-staging"
gsutil mb -l us-central1 $STAGING_BUCKET

# Verificar
gsutil ls
```

---

## Paso 5: Clonar el repositorio

```bash
# Clonar desde GitHub
git clone https://github.com/TU_USUARIO/langgraph-salesforce-sap-demo.git
cd langgraph-salesforce-sap-demo
```

---

## Paso 6: Crear entorno virtual e instalar dependencias

```bash
# Crear venv
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## Paso 7: Configurar variables de entorno

```bash
# Crear archivo .env
cat > .env << 'EOF'
# === GCP Configuration ===
PROJECT_ID=TU_PROYECTO_ID
LOCATION=us-central1
STAGING_BUCKET=gs://TU_PROYECTO_ID-agent-staging

# === OpenAI (REQUERIDO para LLM) ===
OPENAI_API_KEY=sk-tu-api-key-de-openai

# === LangSmith (opcional pero recomendado) ===
LANGSMITH_API_KEY=lsv2_tu_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=belden-sales-agent

# === Salesforce ===
SALESFORCE_MODE=mock

# === SAP ===
SAP_MODE=mock

# === Routing (IDs de ejemplo) ===
ROUTING_AE_OWNER_ID=005000000000001AAA
ROUTING_SDR_OWNER_ID=005000000000002AAA
ROUTING_NURTURE_OWNER_ID=005000000000003AAA
ROUTING_ESCALATION_OWNER_ID=005000000000004AAA
EOF

# Editar con tus valores reales
nano .env
```

**⚠️ IMPORTANTE**: Reemplaza los valores placeholder con tus credenciales reales.

---

## Paso 8: Desplegar el agente

```bash
# Cargar variables de entorno
export $(grep -v '^#' .env | xargs)

# Desplegar
python deploy_agent.py
```

El deploy tarda aproximadamente **3-5 minutos**.

---

## Paso 9: Verificar el deploy

```bash
# Listar agentes desplegados
python -c "
from vertexai import agent_engines
import vertexai

vertexai.init(project='$PROJECT_ID', location='us-central1')

agents = list(agent_engines.list())
for agent in agents:
    print(f'Agent: {agent.display_name}')
    print(f'  Resource: {agent.name}')
    print()
"
```

---

## Paso 10: Probar el agente

```bash
# Guardar el resource name del agente
export AGENT_RESOURCE="projects/TU_PROYECTO/locations/us-central1/reasoningEngines/AGENT_ID"

# Probar
python -c "
from vertexai import agent_engines
import vertexai

vertexai.init(project='$PROJECT_ID', location='us-central1')

agent = agent_engines.get('$AGENT_RESOURCE')

# Test health
result = agent.query(action='health')
print('Health:', result)

# Test lead qualification
lead = {
    'Id': 'TEST001',
    'Company': 'Acme Corp',
    'Title': 'CTO',
    'Industry': 'Technology',
    'Rating': 'Hot',
    'AnnualRevenue': 5000000,
    'NumberOfEmployees': 500
}
result = agent.qualify_lead(lead_data=lead, use_llm=True)
print('Score:', result['score'])
print('Reasoning:', result['reasoning'][:200])
"
```

---

## 🔧 Comandos útiles

### Re-deploy (actualizar agente existente)
```bash
python deploy_agent.py
```

### Deploy solo Lead Qualification
```bash
python deploy_agent.py --mode lead
```

### Deploy solo Ticket Triage
```bash
python deploy_agent.py --mode ticket
```

### Ver logs del deploy
```bash
gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine" --limit=50
```

---

## ❌ Troubleshooting

### Error: "Permission denied"
```bash
# Verificar que tienes los permisos necesarios
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:$(gcloud config get account)"
```

### Error: "API not enabled"
```bash
gcloud services enable aiplatform.googleapis.com
```

### Error: "Bucket not found"
```bash
gsutil mb -l us-central1 gs://${PROJECT_ID}-agent-staging
```

### Error: "OPENAI_API_KEY not set"
```bash
# Verificar que el .env está cargado
echo $OPENAI_API_KEY
# Si está vacío, cargar:
export $(grep -v '^#' .env | xargs)
```

---

## 🔗 Links útiles

- [Vertex AI Console](https://console.cloud.google.com/vertex-ai/agents)
- [LangSmith Dashboard](https://smith.langchain.com)
- [Documentación Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine)
