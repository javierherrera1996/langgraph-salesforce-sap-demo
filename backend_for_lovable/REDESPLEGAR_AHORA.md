# 🚀 REDESPLEGAR BACKEND (VERSIÓN CORREGIDA)

## ✅ Qué se arregló

He actualizado el backend para usar el **SDK de Vertex AI** en lugar de hacer requests HTTP directos.

**Cambios principales:**
- ✅ Usa `vertexai.preview.reasoning_engines` para llamar al agente correctamente
- ✅ Llama a `agent.qualify_lead()` y `agent.classify_complaint()` directamente
- ✅ Agregado `google-cloud-aiplatform` a las dependencias
- ✅ Manejo correcto del AGENT_ENDPOINT

---

## 🔧 PASO 1: Subir archivos a Cloud Shell

Necesitas copiar los archivos actualizados a Cloud Shell.

### Opción A: Desde tu máquina local

Si tienes `gcloud` instalado localmente:

```bash
cd /Users/javierherrera/Documents/programacion/belden-demo/langgraph-salesforce-sap-demo/backend_for_lovable

# Subir archivos a Cloud Shell
gcloud cloud-shell scp main.py cloudshell:~/langgraph-salesforce-sap-demo/backend_for_lovable/main.py
gcloud cloud-shell scp requirements.txt cloudshell:~/langgraph-salesforce-sap-demo/backend_for_lovable/requirements.txt
```

### Opción B: Editar directamente en Cloud Shell

Abre Cloud Shell y ejecuta:

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable

# Editar main.py
nano main.py
```

Luego copia y pega TODO el contenido del archivo `main_v2.py` que está en tu máquina local.

**También actualiza requirements.txt:**

```bash
nano requirements.txt
```

Y agrega esta línea después de `google-auth-oauthlib==1.2.0`:
```
google-cloud-aiplatform==1.38.1
```

---

## 🚀 PASO 2: Redesplegar a Cloud Run

En Cloud Shell:

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable

# Desplegar con el código actualizado
gcloud run deploy belden-agent-gateway \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 120

# El deployment tomará 3-5 minutos
# Espera a que termine...
```

---

## 🧪 PASO 3: Probar que Funcione

Después del deployment:

```bash
# Test 1: Health check
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health

# Debería devolver: {"status":"healthy","agent_status":{...},...}

# Test 2: Qualify Lead
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

# Debería devolver: {"success":true,"response":"Lead qualification complete..."}

# Test 3: Classify Ticket
curl -X POST https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/classify-ticket \
  -H 'Content-Type: application/json' \
  -d '{
    "Subject": "Cable stopped working",
    "Description": "The Cat6 cable I bought stopped working after 2 months",
    "Priority": "High"
  }'

# Debería devolver: {"success":true,"response":"Ticket classified..."}
```

O usa el script automático:

```bash
cd ~/langgraph-salesforce-sap-demo/backend_for_lovable
bash test_backend.sh
```

---

## ✅ Si Todo Funciona

Una vez que los 3 tests pasen (Tests pasados: 3/3), ¡el backend está listo!

Continúa con:
- **PARA_LOVABLE.md** - Prompt para Lovable

---

## 🔧 Si Hay Errores

### Error: "Failed to initialize agent"

Verifica que el AGENT_ENDPOINT esté configurado:

```bash
gcloud run services describe belden-agent-gateway \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Debería mostrar: AGENT_ENDPOINT=https://...
```

Si no está configurado o es incorrecto:

```bash
# Obtener el endpoint correcto
cd ~/langgraph-salesforce-sap-demo
python scripts/list_reasoning_engines.py

# Copiar el AGENT_ENDPOINT del output, luego:
cd backend_for_lovable
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --set-env-vars "AGENT_ENDPOINT=TU_ENDPOINT_AQUI"
```

### Error: "Module not found: vertexai"

El deployment no instaló las dependencias correctamente. Verifica que `requirements.txt` tenga:

```
google-cloud-aiplatform==1.38.1
```

Y vuelve a desplegar.

### Error de memoria

Si ves "Memory limit exceeded", aumenta la memoria:

```bash
gcloud run services update belden-agent-gateway \
  --region us-central1 \
  --memory 2Gi
```

---

## 📝 Resumen de Archivos Actualizados

- ✅ `main.py` - Versión 2.0 con SDK de Vertex AI
- ✅ `requirements.txt` - Agregado `google-cloud-aiplatform`
- 📦 `main_v1_backup.py` - Backup de la versión anterior (por si acaso)

---

## 🎯 Próximos Pasos

1. ✅ Copiar archivos a Cloud Shell (Paso 1)
2. 🚀 Redesplegar (Paso 2)
3. 🧪 Probar (Paso 3)
4. 🎉 Usar **PARA_LOVABLE.md** para integrar con Lovable

¡Buena suerte!
