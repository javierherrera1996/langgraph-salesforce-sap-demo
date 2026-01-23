# 🚀 Endpoints para Probar los Agentes

Guía completa de endpoints para probar los dos agentes del sistema.

---

## 📋 Endpoints Disponibles

### Base URL
- **Local**: `http://localhost:8000`
- **Vertex AI**: `https://your-vertex-ai-endpoint.com`

---

## 🎯 Agente 1: Lead Qualification

### Endpoint
```
POST /run/lead
```

### Descripción
Califica un lead de Salesforce y envía email a `SALES_AGENT_EMAIL` si el score >= 60%.

### Request Body
```json
{
  "lead_id": "00Q5g00000XXXXX",  // Opcional: ID de Salesforce
  "lead_data": {                  // Opcional: Datos completos del lead
    "Id": "00Q5g00000XXXXX",
    "Company": "Acme Corporation",
    "FirstName": "John",
    "LastName": "Doe",
    "Title": "CTO",
    "Email": "john.doe@acme.com",
    "Phone": "+1-555-0123",
    "Industry": "Technology",
    "Rating": "Hot",
    "AnnualRevenue": 10000000,
    "NumberOfEmployees": 500,
    "LeadSource": "Website",
    "Description": "Looking for industrial network solutions"
  },
  "use_llm": true  // true = LLM scoring, false = rule-based
}
```

### Ejemplos de Prueba

#### 1. Lead de Alto Valor (Score >= 60%) - Envía Email
```bash
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_data": {
      "Id": "test-lead-001",
      "Company": "TechCorp Industries",
      "FirstName": "Jane",
      "LastName": "Smith",
      "Title": "VP of Engineering",
      "Email": "jane.smith@techcorp.com",
      "Phone": "+1-555-0100",
      "Industry": "Technology",
      "Rating": "Hot",
      "AnnualRevenue": 15000000,
      "NumberOfEmployees": 1000,
      "LeadSource": "Website",
      "Description": "We need industrial switches for our new manufacturing facility. Budget approved for Q2."
    },
    "use_llm": true
  }'
```

**Resultado esperado**: 
- Score >= 60%
- Email enviado a `SALES_AGENT_EMAIL`
- Email incluye: Lead info + SAP enriched data + AI analysis

#### 2. Lead de Valor Medio (Score 45-59%) - No Envía Email
```bash
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_data": {
      "Id": "test-lead-002",
      "Company": "Small Business Inc",
      "FirstName": "Bob",
      "LastName": "Johnson",
      "Title": "Owner",
      "Email": "bob@smallbiz.com",
      "Industry": "Retail",
      "Rating": "Warm",
      "AnnualRevenue": 500000,
      "NumberOfEmployees": 10,
      "LeadSource": "Cold Call"
    },
    "use_llm": true
  }'
```

**Resultado esperado**: 
- Score < 60%
- No se envía email
- Lead asignado a SDR o Nurture

#### 3. Usar Lead Existente de Salesforce
```bash
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "00Q5g00000XXXXX",
    "use_llm": true
  }'
```

#### 4. Procesar Lead Más Reciente (Sin parámetros)
```bash
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "use_llm": true
  }'
```

---

## 🎫 Agente 2: Complaint Classification

### Endpoint
```
POST /run/ticket
```

### Descripción
Clasifica un ticket/comentario y envía email al asesor correspondiente:
- **Producto** → `PRODUCT_EXPERT_EMAIL`
- **Servicios/Página/IT** → `SERVICES_AGENT_EMAIL`

### Request Body
```json
{
  "case_id": "5005g00000XXXXX",  // Opcional: ID de Salesforce Case
  "case_data": {                  // Opcional: Datos completos del caso
    "Id": "5005g00000XXXXX",
    "CaseNumber": "00001234",
    "Subject": "Switch not working",
    "Description": "Nuestro switch Hirschmann dejó de funcionar",
    "Priority": "High",
    "Origin": "Web"
  },
  "use_llm": true  // true = LLM classification, false = rule-based
}
```

### Ejemplos de Prueba

#### 1. Queja de Producto - Envía a Product Expert
```bash
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-case-001",
      "CaseNumber": "00001234",
      "Subject": "Switch Hirschmann se reinicia constantemente",
      "Description": "Hemos tenido problemas con nuestro switch industrial Hirschmann. Se reinicia solo cada 2-3 horas. Esto está afectando nuestra producción. Necesitamos ayuda urgente.",
      "Priority": "High",
      "Origin": "Web"
    },
    "use_llm": true
  }'
```

**Resultado esperado**: 
- Clasificación: **Product Complaint** (switches)
- Email enviado a `PRODUCT_EXPERT_EMAIL`
- Email incluye: Producto identificado + Análisis AI + Acciones

#### 2. Problema con Cable - Envía a Product Expert
```bash
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-case-002",
      "CaseNumber": "00001235",
      "Subject": "Cable defectuoso",
      "Description": "El cable de red que compramos se rompió después de 2 semanas de uso. El conector no está bien soldado.",
      "Priority": "Medium",
      "Origin": "Email"
    },
    "use_llm": true
  }'
```

**Resultado esperado**: 
- Clasificación: **Product Complaint** (cables/connectors)
- Email enviado a `PRODUCT_EXPERT_EMAIL`

#### 3. Problema de Página Web - Envía a Services Agent
```bash
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-case-003",
      "CaseNumber": "00001236",
      "Subject": "No puedo acceder a la página web",
      "Description": "He intentado acceder al portal de cliente pero no puedo iniciar sesión. Mi contraseña no funciona y el botón de recuperar contraseña tampoco responde.",
      "Priority": "Medium",
      "Origin": "Web"
    },
    "use_llm": true
  }'
```

**Resultado esperado**: 
- Clasificación: **Services/Page/IT**
- Email enviado a `SERVICES_AGENT_EMAIL`
- Email incluye: Portal IT URL + Análisis AI

#### 4. Problema de Login - Envía a Services Agent
```bash
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-case-004",
      "CaseNumber": "00001237",
      "Subject": "Problema con mi cuenta",
      "Description": "No puedo acceder a mi cuenta en el portal. He olvidado mi contraseña y el sistema de recuperación no me envía el email.",
      "Priority": "Low",
      "Origin": "Phone"
    },
    "use_llm": true
  }'
```

**Resultado esperado**: 
- Clasificación: **Services/Page/IT**
- Email enviado a `SERVICES_AGENT_EMAIL`

#### 5. Usar Case Existente de Salesforce
```bash
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "5005g00000XXXXX",
    "use_llm": true
  }'
```

#### 6. Procesar Case Más Reciente (Sin parámetros)
```bash
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "use_llm": true
  }'
```

---

## 📊 Endpoints Adicionales

### Health Check
```bash
curl http://localhost:8000/health
```

### Config Status
```bash
curl http://localhost:8000/status/config
```

### Demo Leads Disponibles
```bash
curl http://localhost:8000/demo/leads
```

### Demo Cases Disponibles
```bash
curl http://localhost:8000/demo/cases
```

### Graph Info - Lead Qualification
```bash
curl http://localhost:8000/graphs/lead
```

### Graph Info - Complaint Classification
```bash
curl http://localhost:8000/graphs/ticket
```

---

## 🧪 Script de Prueba Completo

Crea un archivo `test_agents.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🧪 Testing Belden AI Agents"
echo "=========================="
echo ""

# Test 1: High-value lead (should send email)
echo "📊 Test 1: High-value Lead (Score >= 60%)"
curl -X POST $BASE_URL/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_data": {
      "Id": "test-lead-001",
      "Company": "TechCorp Industries",
      "FirstName": "Jane",
      "LastName": "Smith",
      "Title": "VP of Engineering",
      "Email": "jane.smith@techcorp.com",
      "Industry": "Technology",
      "Rating": "Hot",
      "AnnualRevenue": 15000000,
      "NumberOfEmployees": 1000,
      "LeadSource": "Website"
    },
    "use_llm": true
  }' | jq '.'
echo ""
echo ""

# Test 2: Product complaint (should send to Product Expert)
echo "📦 Test 2: Product Complaint"
curl -X POST $BASE_URL/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-case-001",
      "Subject": "Switch not working",
      "Description": "Nuestro switch Hirschmann dejó de funcionar",
      "Priority": "High"
    },
    "use_llm": true
  }' | jq '.'
echo ""
echo ""

# Test 3: Services/Page issue (should send to Services Agent)
echo "🌐 Test 3: Services/Page Issue"
curl -X POST $BASE_URL/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-case-002",
      "Subject": "Cannot access website",
      "Description": "No puedo acceder a la página web",
      "Priority": "Medium"
    },
    "use_llm": true
  }' | jq '.'
echo ""
echo ""

echo "✅ Tests completed!"
```

Ejecutar:
```bash
chmod +x test_agents.sh
./test_agents.sh
```

---

## 📧 Verificar Emails Enviados

### Resend Dashboard
1. Ve a [https://resend.com/emails](https://resend.com/emails)
2. Verás todos los emails enviados
3. Puedes ver el estado (sent, delivered, bounced)

### Logs de la Aplicación
Los logs muestran:
```
✅ Email sent successfully to: sales@belden.com
   Message ID: abc123...
```

---

## 🎯 Resumen de Flujos

### Lead Qualification Flow
```
Lead Input → Score Calculation → Routing Decision
                                    ↓
                            If score >= 60%
                                    ↓
                        📧 Email to SALES_AGENT_EMAIL
```

### Complaint Classification Flow
```
Ticket Input → LLM Classification
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
   Product?              Services/Page?
        ↓                       ↓
📧 PRODUCT_EXPERT    📧 SERVICES_AGENT
```

---

## ⚙️ Variables de Entorno Requeridas

Asegúrate de tener configurado en `.env`:

```bash
RESEND_API_KEY=re_tu_api_key
SALES_AGENT_EMAIL=ventas@belden.com
PRODUCT_EXPERT_EMAIL=productos@belden.com
SERVICES_AGENT_EMAIL=servicios@belden.com
NOTIFICATION_EMAIL=notificaciones@belden.com
```

---

## 📚 Referencias

- [Email Configuration Guide](EMAIL_CONFIGURATION.md)
- [Resend Setup Guide](RESEND_SETUP.md)
- [Architecture Overview](ARCHITECTURE_OVERVIEW.md)

---

¡Listo para probar! 🚀
