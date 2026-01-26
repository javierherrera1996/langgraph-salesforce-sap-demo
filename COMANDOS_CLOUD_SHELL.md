# 🚀 Comandos para Cloud Shell (Copia y Pega)

## ⚡ SOLUCIÓN RÁPIDA - Ejecuta estos comandos en orden

### 1️⃣ Ver qué reasoning engines tienes

```bash
cd ~/langgraph-salesforce-sap-demo
python scripts/list_reasoning_engines.py
```

**Si dice "NO REASONING ENGINES FOUND"** → ve al paso 2

**Si muestra un AGENT_ENDPOINT** → copia ese endpoint y ve directo al paso 3

---

### 2️⃣ Desplegar el agente principal (solo si NO tienes uno)

```bash
cd ~/langgraph-salesforce-sap-demo
python deploy_agent.py
```

**IMPORTANTE**: Al final verás algo como:

```
✅ Agent deployed successfully!
Endpoint: https://us-central1-aiplatform.googleapis.com/v1/projects/.../reasoningEngines/123456789:query
```

**COPIA ese endpoint completo** y ve al paso 3.

---

### 3️⃣ Actualizar el backend con el endpoint

Reemplaza `TU_ENDPOINT_AQUI` con el endpoint que copiaste:

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable

gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=TU_ENDPOINT_AQUI"
```

**Ejemplo**:
```bash
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/987654321:query"
```

---

### 4️⃣ Probar que todo funcione

```bash
# Test 1: Health check (debe decir "healthy")
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health

# Test 2: Chat (debe devolver una respuesta del agente)
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello, I need help with a product"}'
```

**Si el Test 2 funciona**: ✅ ¡Listo! Ya puedes integrar con Lovable

**Si falla**: Revisa los logs:
```bash
gcloud run services logs read belden-agent-gateway \
  --region us-central1 \
  --limit 20
```

---

## 🎯 Después de que todo funcione

1. Abre el archivo `backend_for_lovable/LOVABLE_PROMPT_COMPLETO.md`
2. Copia el prompt completo
3. Pégalo en Lovable
4. Lovable generará todo el código frontend
5. ¡Listo! Tu aplicación está conectada al agente

---

## ❓ FAQs

**P: ¿Por qué necesito desplegar el agente primero?**

R: El backend de Cloud Run es solo un intermediario que:
- Recibe peticiones de Lovable
- Genera tokens automáticamente
- Llama a tu agente principal en Vertex AI
- Devuelve la respuesta

El agente REAL (con toda tu lógica de LangGraph, Salesforce, emails) está en Vertex AI Agent Engine.

**P: ¿El backend cambia mi agente?**

R: No, el backend NO toca tu agente. Solo facilita la conexión desde Lovable.

**P: ¿Qué pasa si ya había desplegado el agente antes?**

R: Usa `python scripts/list_reasoning_engines.py` para ver el endpoint y ve directo al paso 3.

---

## 📝 Checklist

- [ ] Ejecuté `list_reasoning_engines.py` y obtuve el endpoint
- [ ] O ejecuté `deploy_agent.py` y copié el endpoint del output
- [ ] Actualicé el backend con `gcloud run services update...`
- [ ] El health check devuelve `{"status":"healthy",...}`
- [ ] El chat devuelve una respuesta del agente
- [ ] Copié el prompt de Lovable y lo pegué en la aplicación

---

## 🆘 Si algo sale mal

### Error en deploy_agent.py

```bash
# Verificar autenticación
gcloud auth application-default login
gcloud auth application-default set-quota-project logical-hallway-485016-r7

# Verificar que .env NO tenga GOOGLE_APPLICATION_CREDENTIALS
grep GOOGLE_APPLICATION_CREDENTIALS ~/langgraph-salesforce-sap-demo/.env
# Si aparece algo, coméntalo con #
```

### El chat no responde o da 404

```bash
# Ver qué AGENT_ENDPOINT está configurado
gcloud run services describe belden-agent-gateway \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Si está mal, actualízalo de nuevo
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=EL_ENDPOINT_CORRECTO"
```

### Health check da error de autenticación

El backend en Cloud Run usa Application Default Credentials automáticamente. No necesitas hacer nada especial.

---

## 📞 URLs Importantes

- **Backend API**: https://belden-agent-gateway-tahgwtwoha-uc.a.run.app
- **Health Check**: https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health
- **Lovable URL**: (la que uses en `baseUrl` del config)

---

## ✅ Próximo Paso

Una vez que el step 4 funcione correctamente, continúa con:

**→ `LOVABLE_PROMPT_COMPLETO.md`** para integrar con Lovable
