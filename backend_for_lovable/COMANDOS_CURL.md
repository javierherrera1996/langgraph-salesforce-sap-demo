# 🧪 Comandos curl para Probar el Backend

## Opción 1: Script Automático (Recomendado)

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable
bash test_backend.sh
```

Este script probará los 3 endpoints automáticamente y te dirá qué hacer si algo falla.

---

## Opción 2: Comandos curl Individuales

### 1️⃣ Health Check

```bash
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "authentication": "ok",
  "agent_endpoint": "https://..."
}
```

---

### 2️⃣ Qualify Lead

```bash
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/qualify-lead \
  -H 'Content-Type: application/json' \
  -d '{
    "Name": "John Doe",
    "Company": "Acme Corporation",
    "Email": "john@acme.com",
    "Title": "CTO",
    "Industry": "Manufacturing",
    "Rating": "Hot",
    "AnnualRevenue": 5000000,
    "NumberOfEmployees": 500,
    "LeadSource": "Partner Referral"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "response": "Lead qualification complete.\nScore: 85%\nRouting: AE\nReasoning: ...",
  "session_id": null,
  "error": null
}
```

---

### 3️⃣ Classify Ticket

```bash
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/classify-ticket \
  -H 'Content-Type: application/json' \
  -d '{
    "Subject": "Cable stopped working",
    "Description": "The Cat6 cable I bought stopped working after 2 months",
    "Priority": "High"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "response": "Ticket classified.\nType: Product Complaint\nCategory: cables\nAction: email_sent\nReasoning: ...",
  "session_id": null,
  "error": null
}
```

---

## ❌ Si obtienes errores

### Error: 404 Not Found

El backend no está desplegado o la URL es incorrecta.

**Solución:**
```bash
# Verificar que el servicio existe
gcloud run services describe belden-agent-gateway \
  --region us-central1 \
  --format="value(status.url)"
```

### Error: 400 Bad Request con "Unknown name \"message\""

El backend tiene el código viejo.

**Solución: Redesplegar**
```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable

gcloud run deploy belden-agent-gateway \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

Espera 2-3 minutos y vuelve a probar.

### Error: 500 Internal Server Error

Problema con el agente de Vertex AI o el AGENT_ENDPOINT.

**Solución: Ver logs**
```bash
gcloud run services logs read belden-agent-gateway \
  --region us-central1 \
  --limit 20
```

Busca líneas con "ERROR" o "Failed".

### Error: "AGENT_ENDPOINT not configured"

El backend no tiene configurado el endpoint del agente.

**Solución: Configurar AGENT_ENDPOINT**
```bash
# Obtener el endpoint del agente
cd ~/langgraph-salesforce-sap-demo
python scripts/list_reasoning_engines.py

# Copiar el AGENT_ENDPOINT del output, luego:
cd backend_for_lovable
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=TU_ENDPOINT_AQUI"
```

---

## ✅ Checklist de Troubleshooting

- [ ] El health check devuelve `{"status":"healthy",...}`
- [ ] El AGENT_ENDPOINT está configurado (aparece en health check)
- [ ] Los endpoints qualify-lead y classify-ticket devuelven `{"success":true,...}`
- [ ] Las respuestas incluyen Score/Routing (lead) o Type/Category (ticket)

Si todos estos checks pasan, ¡el backend está listo para Lovable!

---

## 🔍 Comandos Útiles de Diagnóstico

```bash
# Ver variables de entorno del backend
gcloud run services describe belden-agent-gateway \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Ver logs en tiempo real
gcloud run services logs tail belden-agent-gateway \
  --region us-central1

# Ver última versión desplegada
gcloud run revisions list \
  --service belden-agent-gateway \
  --region us-central1 \
  --limit 1

# Verificar que el código local tiene los cambios
grep -A 3 "action =" ~/langgraph-salesforce-sap-demo/backend_for_lovable/main.py
# Debería mostrar: action = "qualify_lead"
```
