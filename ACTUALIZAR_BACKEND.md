# 🔄 Actualizar Backend con el Formato Correcto

## ✅ Cambio Realizado

He actualizado `backend_for_lovable/main.py` para enviar el payload correcto al Vertex AI Agent.

**Antes** (❌ Formato incorrecto):
```python
payload = {
    "message": request.message,
    "session_id": request.session_id,
    "lead_data": request.lead_data
}
```

**Ahora** (✅ Formato correcto):
```python
payload = {
    "action": "qualify_lead",  # o "classify_complaint"
    "lead_data": request.lead_data,  # o "case_data"
    "use_llm": True
}
```

---

## 🚀 Pasos para Redesplegar

### En Cloud Shell, ejecuta:

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable

# Verificar que tengas la última versión
cat main.py | grep -A 5 "action ="

# Debería mostrar algo como:
# action = "qualify_lead"
# payload = {
#     "action": action,
#     ...

# Redesplegar a Cloud Run
gcloud run deploy belden-agent-gateway \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# El deployment tomará 2-3 minutos
```

---

## 🧪 Probar que Funcione

```bash
# Test 1: Health check
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health

# Debería devolver: {"status":"healthy",...}

# Test 2: Qualify Lead
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/qualify-lead \
  -H 'Content-Type: application/json' \
  -d '{
    "Name": "John Doe",
    "Company": "Acme Corp",
    "Title": "CTO",
    "Industry": "Manufacturing",
    "Rating": "Hot",
    "AnnualRevenue": 5000000,
    "NumberOfEmployees": 500,
    "LeadSource": "Partner Referral"
  }'

# Debería devolver algo como:
# {
#   "success": true,
#   "response": "Lead qualification complete.\nScore: 85%\nRouting: AE\nReasoning: ...",
#   ...
# }

# Test 3: Classify Ticket
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/classify-ticket \
  -H 'Content-Type: application/json' \
  -d '{
    "Subject": "Cable stopped working",
    "Description": "The Cat6 cable I bought stopped working after 2 months",
    "Priority": "High"
  }'

# Debería devolver algo como:
# {
#   "success": true,
#   "response": "Ticket classified.\nType: Product Complaint\nCategory: cables\n...",
#   ...
# }
```

---

## ✅ Si Todo Funciona

Una vez que los tests pasen, tu backend está listo para usar con Lovable!

Continúa con:
- **LOVABLE_PROMPT_COMPLETO.md** para generar el frontend

---

## 🔧 Si Hay Problemas

### Error: "source not found" al desplegar

```bash
# Asegúrate de estar en el directorio correcto
pwd
# Debería mostrar: .../langgraph-salesforce-sap-demo/backend_for_lovable

# Si no, navega:
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable
```

### Error 400 del agente

```bash
# Ver logs del backend
gcloud run services logs read belden-agent-gateway \
  --region us-central1 \
  --limit 20

# Ver logs del agente
gcloud logging read \
  "resource.type=aiplatform.googleapis.com/ReasoningEngine" \
  --limit 20
```

### Deployment toma mucho tiempo

Es normal. Cloud Run necesita:
1. Construir la imagen Docker
2. Subirla a Artifact Registry
3. Desplegarla

Puede tomar 3-5 minutos.

---

## 📝 Resumen de Cambios

1. **Payload correcto**: Ahora envía `action`, `lead_data`/`case_data`, `use_llm`
2. **Response parsing**: Formatea la respuesta según el tipo de acción
3. **Health check**: Soporta mensajes "health", "ping", "status"
4. **Error handling**: Mensajes claros si falta información

---

## 🎯 Próximo Paso

Después de verificar que los tests funcionen:

1. Abre `LOVABLE_PROMPT_COMPLETO.md`
2. Copia el prompt
3. Pégalo en Lovable
4. Lovable generará todo el código frontend
5. ¡Tu aplicación estará completa!
