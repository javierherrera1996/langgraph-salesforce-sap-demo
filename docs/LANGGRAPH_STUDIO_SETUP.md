# 🎨 Visualizar Agente en LangGraph Studio

Esta guía explica cómo visualizar y depurar tu agente usando **LangGraph Studio** (local) y **LangSmith Dashboard** (agente desplegado).

---

## 📋 Opciones Disponibles

### 1. **LangGraph Studio (Local)** 🏠
- ✅ Visualización interactiva de grafos
- ✅ Depuración paso a paso
- ✅ Edición de estado en tiempo real
- ⚠️ Solo funciona con grafos locales (no Vertex AI directamente)

### 2. **LangSmith Dashboard** 🌐
- ✅ Ver trazas del agente desplegado en Vertex AI
- ✅ Monitoreo de ejecuciones en producción
- ✅ Análisis de rendimiento y errores
- ✅ Comparar ejecuciones

---

## 🚀 Opción 1: LangGraph Studio Local

### Paso 1: Instalar LangGraph CLI

```bash
pip install langgraph-cli[inmem]
```

### Paso 2: Verificar Configuración

Asegúrate de que `langgraph.json` esté configurado:

```json
{
  "graphs": {
    "lead_qualification": "./src/graphs/lead_graph.py:build_lead_graph",
    "complaint_classification": "./src/graphs/complaint_graph.py:build_complaint_graph"
  },
  "env": ".env",
  "python_version": "3.11",
  "dependencies": ["."]
}
```

### Paso 3: Configurar Variables de Entorno

Crea/actualiza tu `.env`:

```bash
# OpenAI (requerido para LLM)
OPENAI_API_KEY=sk-tu-api-key

# LangSmith (recomendado para tracing)
LANGSMITH_API_KEY=lsv2_tu-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=belden-sales-agent-local

# Salesforce (mock para desarrollo)
SALESFORCE_MODE=mock

# SAP (mock para desarrollo)
SAP_MODE=mock
```

### Paso 4: Iniciar LangGraph Studio

```bash
# Desde el directorio del proyecto
cd langgraph-salesforce-sap-demo
langgraph dev
```

Esto iniciará:
- **LangGraph Studio UI**: `http://localhost:8123`
- **API Server**: `http://localhost:8124`

### Paso 5: Abrir en el Navegador

1. Abre `http://localhost:8123` en tu navegador
2. Verás los grafos disponibles:
   - `lead_qualification`
   - `complaint_classification`

### Paso 6: Probar un Grafo

1. Selecciona un grafo (ej: `lead_qualification`)
2. Haz clic en "Run" o "Play"
3. Ingresa datos de prueba:

```json
{
  "lead": {
    "Id": "test-001",
    "Company": "Acme Corp",
    "Title": "CTO",
    "Industry": "Technology",
    "Rating": "Hot",
    "AnnualRevenue": 5000000,
    "NumberOfEmployees": 100,
    "LeadSource": "Website"
  },
  "use_llm": true
}
```

4. Observa la ejecución paso a paso en el visualizador

---

## 🌐 Opción 2: LangSmith Dashboard (Agente Desplegado)

### Paso 1: Configurar LangSmith en Vertex AI

Asegúrate de que las variables de entorno en Vertex AI incluyan:

```bash
LANGSMITH_API_KEY=lsv2_tu-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=belden-sales-agent-prod
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**Actualizar variables en Vertex AI:**

```bash
# Usar el script de actualización
python update_env_vars.py
```

O manualmente desde Cloud Console:
1. Ve a Vertex AI → Agent Engine
2. Selecciona tu agente
3. Edita las variables de entorno
4. Agrega las variables de LangSmith

### Paso 2: Ejecutar el Agente Desplegado

Cada vez que ejecutes el agente desplegado, las trazas se enviarán automáticamente a LangSmith:

```python
from google.cloud import aiplatform
from vertexai.preview import reasoning_engines

# Conectar al agente
agent = reasoning_engines.ReasoningEngine.from_path(
    reasoning_engine_id="TU_AGENT_ID",
    project="TU_PROYECTO",
    location="us-central1"
)

# Ejecutar
result = agent.query(
    action="qualify_lead",
    lead_data={
        "Company": "Acme Corp",
        "Title": "CTO",
        "Industry": "Technology"
    }
)
```

### Paso 3: Ver Trazas en LangSmith

1. Ve a [LangSmith Dashboard](https://smith.langchain.com)
2. Selecciona el proyecto: `belden-sales-agent-prod`
3. Verás todas las ejecuciones del agente desplegado
4. Haz clic en una ejecución para ver:
   - **Grafos**: Visualización del flujo
   - **Nodos**: Cada paso del workflow
   - **LLM Calls**: Prompts y respuestas
   - **Tiempos**: Performance de cada nodo
   - **Errores**: Si hay algún problema

### Paso 4: Filtrar Trazas

En LangSmith puedes filtrar por:
- **Tags**: `vertex-ai`, `lead-qualification`, `complaint-classification`
- **Fecha**: Últimas 24h, 7 días, etc.
- **Estado**: Success, Error, etc.
- **Metadata**: `workflow`, `use_llm`, `project`

---

## 🔄 Flujo Recomendado

### Desarrollo Local
1. Usa **LangGraph Studio** para desarrollar y depurar
2. Prueba cambios localmente antes de desplegar
3. Las trazas locales van a `belden-sales-agent-local`

### Producción
1. Despliega a Vertex AI con LangSmith configurado
2. Monitorea ejecuciones en **LangSmith Dashboard**
3. Las trazas de producción van a `belden-sales-agent-prod`

---

## 🛠️ Scripts Útiles

### Ver Trazas Recientes

```bash
# Ver últimas 10 ejecuciones en LangSmith
python scripts/view_traces.py --limit 10
```

### Comparar Ejecuciones

En LangSmith Dashboard:
1. Selecciona 2+ ejecuciones
2. Haz clic en "Compare"
3. Ve diferencias en prompts, respuestas, tiempos

---

## 📊 Ejemplo de Traza en LangSmith

Cuando ejecutas el agente, verás algo como:

```
📦 Complaint Classification Workflow
├── FetchTicket
│   └── ✅ Fetched case: 5005g00000XXXXX
├── ClassifyComplaint
│   ├── 🤖 LLM Call: classify_complaint_with_llm
│   │   ├── Prompt: [Complaint Classification System Prompt]
│   │   ├── Response: {is_product_complaint: true, ...}
│   │   └── Tokens: 450 input, 120 output
│   └── ✅ Classification: PRODUCT COMPLAINT (switches)
├── DecideAction
│   └── ✅ Action: email_product_owner
└── ExecuteActions
    ├── 📧 Email sent: ai_analysis@belden.com
    └── ✅ Comment posted to Salesforce
```

---

## ❓ Troubleshooting

### LangGraph Studio no inicia

```bash
# Verificar que langgraph.json existe
ls -la langgraph.json

# Verificar Python version
python --version  # Debe ser 3.11+

# Reinstalar CLI
pip install --upgrade langgraph-cli[inmem]
```

### No veo trazas en LangSmith

1. Verifica que `LANGSMITH_API_KEY` esté configurado
2. Verifica que `LANGCHAIN_TRACING_V2=true`
3. Revisa los logs del agente en Vertex AI
4. Prueba con un script local primero

### El agente desplegado no envía trazas

1. Actualiza variables de entorno en Vertex AI
2. Reinicia el agente después de actualizar variables
3. Verifica que el código use `@traceable` decorators

---

## 📚 Referencias

- [LangGraph Studio Docs](https://langchain-ai.github.io/langgraph/tutorials/langgraph-studio/)
- [LangSmith Dashboard](https://docs.smith.langchain.com/)
- [Vertex AI Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine)

---

## ✅ Checklist

- [ ] LangGraph CLI instalado
- [ ] `langgraph.json` configurado
- [ ] Variables de entorno en `.env`
- [ ] LangGraph Studio corriendo (`langgraph dev`)
- [ ] LangSmith API key configurado
- [ ] Variables de LangSmith en Vertex AI
- [ ] Agente desplegado enviando trazas

---

¡Listo! Ahora puedes visualizar y depurar tu agente tanto localmente como en producción. 🎉
