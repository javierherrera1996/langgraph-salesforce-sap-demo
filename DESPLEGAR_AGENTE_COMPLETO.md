# 🚀 Guía Completa de Despliegue - Belden AI Agent

## ❌ Error Actual

Estás recibiendo este error:
```
404 - The requested URL /v1/projects/.../reasoningEngines/180545306838958080 was not found
```

**Causa**: El agente principal aún no ha sido desplegado a Vertex AI Agent Engine.

## ✅ Solución: Desplegar el Agente Principal

### PASO 1: Verificar Reasoning Engines Existentes

En Cloud Shell, ejecuta:

```bash
cd ~/langgraph-salesforce-sap-demo

# Ver si hay reasoning engines desplegados
python scripts/list_reasoning_engines.py
```

**Resultado esperado**:
- Si dice "NO REASONING ENGINES FOUND" → necesitas desplegar (ve al PASO 2, Opción A)
- Si muestra un engine con su AGENT_ENDPOINT → copia ese endpoint (ve al PASO 3)

---

### PASO 2: Desplegar el Agente Principal

#### Opción A: Si NO hay engine desplegado

```bash
cd ~/langgraph-salesforce-sap-demo

# Asegúrate de que .env esté configurado correctamente
# (NO debe tener GOOGLE_APPLICATION_CREDENTIALS en Cloud Shell)

# Desplegar el agente
python deploy_agent.py
```

**IMPORTANTE**: Guarda el output completo. Al final verás algo como:

```
✅ Agent deployed successfully!
Agent ID: 987654321012345678
Endpoint: https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/987654321012345678:query
```

#### Opción B: Si YA hay un engine desplegado

Si el script `list_reasoning_engines.py` mostró un engine, ya tienes el AGENT_ENDPOINT impreso.

Simplemente cópialo del output que se ve así:

```
🎯 AGENT_ENDPOINT:
https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/123456789:query
```

Copia esa URL completa y ve directo al PASO 3.

---

### PASO 3: Actualizar el Backend con el Endpoint Correcto

Usa el endpoint que obtuviste en el paso anterior:

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable

# Actualizar Cloud Run con el endpoint correcto
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=TU_ENDPOINT_AQUI"

# Ejemplo:
# gcloud run services update belden-agent-gateway \
#   --region us-central1 \
#   --set-env-vars "AGENT_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/987654321012345678:query"
```

---

### PASO 4: Probar la Conexión

```bash
# Probar el health endpoint
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health

# Deberías ver:
# {"status":"healthy","authentication":"ok","agent_endpoint":"https://..."}

# Probar el chat
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello, I need help with a product"}'

# Deberías recibir una respuesta del agente
```

---

## 🔍 Troubleshooting

### Si `deploy_agent.py` falla

**Error común**: "Application Default Credentials not found"

**Solución**:
```bash
# En Cloud Shell
gcloud auth application-default login
gcloud auth application-default set-quota-project logical-hallway-485016-r7

# Verificar que .env NO tenga GOOGLE_APPLICATION_CREDENTIALS
# (o que esté comentado con #)
grep GOOGLE_APPLICATION_CREDENTIALS .env
```

### Si el deployment toma mucho tiempo

Es normal. El primer deployment puede tomar 5-10 minutos porque:
- Sube el código al staging bucket
- Construye el entorno
- Despliega a Vertex AI
- Inicializa el reasoning engine

### Si ves errores de permisos

```bash
# Verificar que tienes los roles necesarios
gcloud projects get-iam-policy logical-hallway-485016-r7 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

Necesitas al menos:
- `roles/aiplatform.user`
- `roles/storage.objectAdmin`

---

## 📝 Checklist Completo

- [ ] Verificar reasoning engines existentes
- [ ] Desplegar agente principal con `python deploy_agent.py`
- [ ] Guardar el AGENT_ENDPOINT del output
- [ ] Actualizar Cloud Run con el endpoint correcto
- [ ] Probar /health endpoint → debe mostrar "healthy"
- [ ] Probar /chat endpoint → debe recibir respuesta del agente
- [ ] Actualizar Lovable con la URL: `https://belden-agent-gateway-tahgwtwoha-uc.a.run.app`

---

## 🎯 Comandos Rápidos (Copia y Pega)

```bash
# 1. Ver engines existentes
cd ~/langgraph-salesforce-sap-demo
python scripts/list_reasoning_engines.py

# 2. Si NO hay engines, desplegar agente:
python deploy_agent.py

# 3. Copiar el AGENT_ENDPOINT del output, luego actualizar backend:
cd backend_for_lovable
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=PEGAR_AQUI_TU_ENDPOINT"

# 4. Probar que todo funcione
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hi"}'
```

---

## 📞 Siguiente Paso

Una vez que el chat funcione correctamente, puedes integrar con Lovable usando los archivos:
- `LOVABLE_INSTRUCTIONS.md` - Paso a paso
- `LOVABLE_PROMPT_COMPLETO.md` - Prompt único

La URL que usarás en Lovable es:
```
https://belden-agent-gateway-tahgwtwoha-uc.a.run.app
```
