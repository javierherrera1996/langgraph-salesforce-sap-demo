# 🚀 Guía de Despliegue a Vertex AI Agent Engine

Esta guía te ayudará a desplegar tu código a Vertex AI Agent Engine paso a paso.

## 📋 Pre-requisitos

1. **Cuenta de Google Cloud** con billing habilitado
2. **Proyecto de GCP** creado
3. **Python 3.11+** instalado
4. **Dependencias** instaladas (`pip install -r requirements.txt`)

---

## 🔧 Opción 1: Con gcloud CLI (Recomendado)

### Paso 1: Instalar gcloud CLI

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**O descarga desde:**
https://cloud.google.com/sdk/docs/install

### Paso 2: Autenticarse

```bash
gcloud auth application-default login
```

Esto abrirá tu navegador para autenticarte.

### Paso 3: Configurar proyecto

```bash
gcloud config set project TU_PROYECTO_ID
```

### Paso 4: Habilitar APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### Paso 5: Crear bucket de staging

```bash
export PROJECT_ID="tu-proyecto-id"
export STAGING_BUCKET="gs://${PROJECT_ID}-agent-staging"
gsutil mb -l us-central1 $STAGING_BUCKET
```

---

## 🔑 Opción 2: Con Service Account (Sin gcloud CLI)

Si no puedes instalar gcloud CLI, puedes usar una cuenta de servicio.

### Paso 1: Crear Service Account en GCP Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Navega a **IAM & Admin** → **Service Accounts**
3. Clic en **Create Service Account**
4. Nombre: `agent-engine-deployer`
5. Roles necesarios:
   - `Vertex AI User`
   - `Storage Admin` (para crear buckets)
   - `Service Usage Admin` (para habilitar APIs)

### Paso 2: Crear y descargar clave JSON

1. En la cuenta de servicio creada, ve a **Keys**
2. Clic en **Add Key** → **Create new key**
3. Selecciona **JSON**
4. Descarga el archivo (ej: `agent-engine-deployer-key.json`)

### Paso 3: Configurar variable de entorno

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/completa/a/agent-engine-deployer-key.json"
```

O agrega al archivo `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=/ruta/completa/a/agent-engine-deployer-key.json
```

### Paso 4: Habilitar APIs (desde Console)

1. Ve a [APIs & Services](https://console.cloud.google.com/apis/library)
2. Busca y habilita:
   - **Vertex AI API**
   - **Cloud Storage API**

### Paso 5: Crear bucket (desde Console)

1. Ve a [Cloud Storage](https://console.cloud.google.com/storage)
2. Clic en **Create Bucket**
3. Nombre: `tu-proyecto-id-agent-staging`
4. Ubicación: `us-central1` (o tu región preferida)

---

## ⚙️ Configurar Variables de Entorno

### Paso 1: Copiar archivo de ejemplo

```bash
cp env.gcp.example .env
```

### Paso 2: Editar .env

Abre `.env` y configura:

```env
# === GCP Configuration (REQUERIDO) ===
PROJECT_ID=tu-proyecto-gcp-id
LOCATION=us-central1
STAGING_BUCKET=gs://tu-proyecto-id-agent-staging

# === OpenAI (REQUERIDO) ===
OPENAI_API_KEY=sk-tu-api-key-de-openai

# === LangSmith (Opcional pero recomendado) ===
LANGSMITH_API_KEY=lsv2_tu_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=belden-sales-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# === Salesforce (Mock para demo) ===
SALESFORCE_MODE=mock

# === SAP (Mock para demo) ===
SAP_MODE=mock

# === Routing (IDs de ejemplo) ===
ROUTING_AE_OWNER_ID=005000000000001AAA
ROUTING_SDR_OWNER_ID=005000000000002AAA
ROUTING_NURTURE_OWNER_ID=005000000000003AAA
ROUTING_ESCALATION_OWNER_ID=005000000000004AAA

# === Email (Opcional) ===
RESEND_API_KEY=re_tu_resend_api_key
RESEND_FROM_EMAIL=onboarding@resend.dev
NOTIFICATION_EMAIL=tu-email@company.com
```

**⚠️ IMPORTANTE:** Reemplaza todos los valores placeholder con tus credenciales reales.

---

## ✅ Verificar Configuración

Ejecuta el script de preparación:

```bash
python prepare_deployment.py
```

Este script verificará:
- ✅ gcloud CLI (si usas Opción 1)
- ✅ Autenticación con GCP
- ✅ Variables de entorno configuradas
- ✅ APIs habilitadas
- ✅ Bucket de staging creado

---

## 🚀 Desplegar

Una vez que todo esté configurado:

### Desplegar agente completo (Lead + Ticket)

```bash
python deploy_agent.py
```

### Desplegar solo Lead Qualification

```bash
python deploy_agent.py --mode lead
```

### Desplegar solo Ticket Triage

```bash
python deploy_agent.py --mode ticket
```

El despliegue tarda aproximadamente **3-5 minutos**.

---

## 🧪 Probar el Agente Desplegado

### Obtener Resource Name

Después del despliegue, el script mostrará el `resource_name` del agente, algo como:
```
projects/tu-proyecto/locations/us-central1/reasoningEngines/123456789
```

### Probar con Python

```python
from vertexai import agent_engines
import vertexai

# Inicializar
vertexai.init(project="tu-proyecto", location="us-central1")

# Obtener agente
agent = agent_engines.get("projects/tu-proyecto/locations/us-central1/reasoningEngines/123456789")

# Test health
result = agent.query(action="health")
print(result)

# Test lead qualification
lead = {
    "Id": "TEST001",
    "Company": "Acme Corp",
    "Title": "CTO",
    "Industry": "Technology",
    "Rating": "Hot",
    "AnnualRevenue": 5000000,
    "NumberOfEmployees": 500
}
result = agent.qualify_lead(lead_data=lead, use_llm=True)
print(f"Score: {result['score']}")
print(f"Reasoning: {result['reasoning'][:200]}")
```

### Probar desde script

```bash
python deploy_agent.py --mode test --resource-name "projects/tu-proyecto/locations/us-central1/reasoningEngines/123456789"
```

---

## 🔄 Actualizar Agente Existente

Para actualizar un agente ya desplegado, simplemente ejecuta:

```bash
python deploy_agent.py
```

El script detectará automáticamente si el agente existe y lo actualizará.

---

## ❌ Troubleshooting

### Error: "Permission denied"

**Solución:**
- Verifica que tu cuenta/usuario tenga los roles necesarios
- Si usas Service Account, verifica que tenga los roles:
  - `Vertex AI User`
  - `Storage Admin`
  - `Service Usage Admin`

### Error: "API not enabled"

**Solución:**
```bash
# Con gcloud CLI
gcloud services enable aiplatform.googleapis.com --project TU_PROYECTO

# O desde Console: https://console.cloud.google.com/apis/library
```

### Error: "Bucket not found"

**Solución:**
```bash
# Con gcloud CLI
gsutil mb -l us-central1 gs://tu-proyecto-agent-staging

# O desde Console: https://console.cloud.google.com/storage
```

### Error: "OPENAI_API_KEY not set"

**Solución:**
```bash
# Verificar que está en .env
cat .env | grep OPENAI_API_KEY

# Cargar manualmente
export $(grep -v '^#' .env | xargs)
```

### Error: "gcloud not found"

**Solución:**
- Instala gcloud CLI (ver Opción 1)
- O usa Service Account (ver Opción 2)

### Error: "service account info is missing 'email' field"

**Solución:**
- Verifica que NO estés llamando `vertexai.init()` dentro del código del agente
- Solo debe estar en `deploy_agent.py`
- Ver: [docs/TROUBLESHOOTING_VERTEX_AI.md](docs/TROUBLESHOOTING_VERTEX_AI.md)

---

## 🔗 Links Útiles

- [Vertex AI Console](https://console.cloud.google.com/vertex-ai/agents)
- [Cloud Storage Console](https://console.cloud.google.com/storage)
- [APIs & Services](https://console.cloud.google.com/apis/library)
- [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
- [Documentación Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine)
- [LangSmith Dashboard](https://smith.langchain.com)

---

## 📝 Resumen Rápido

```bash
# 1. Instalar gcloud (o usar Service Account)
brew install --cask google-cloud-sdk

# 2. Autenticarse
gcloud auth application-default login

# 3. Configurar proyecto
gcloud config set project TU_PROYECTO

# 4. Habilitar APIs
gcloud services enable aiplatform.googleapis.com

# 5. Crear bucket
gsutil mb -l us-central1 gs://TU_PROYECTO-agent-staging

# 6. Configurar .env
cp env.gcp.example .env
# Editar .env con tus valores

# 7. Verificar
python prepare_deployment.py

# 8. Desplegar
python deploy_agent.py
```

¡Listo! 🎉
