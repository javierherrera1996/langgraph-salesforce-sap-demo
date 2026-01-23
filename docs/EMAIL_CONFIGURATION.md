# 📧 Configuración de Emails por Tipo de Agente

Este documento explica cómo configurar los emails para cada tipo de agente y asesor.

---

## 🎯 Resumen del Sistema

### Agente 1: Lead Qualification
- **Cuándo envía email**: Cuando el lead tiene score >= 60%
- **Destinatario**: `SALES_AGENT_EMAIL` (Agente de Ventas)
- **Contenido**: Toda la información de la oportunidad (lead + datos SAP enriquecidos)

### Agente 2: Complaint Classification
- **Producto**: Envía a `PRODUCT_EXPERT_EMAIL` (Asesor Experto en Producto)
- **Servicios/Página/IT**: Envía a `SERVICES_AGENT_EMAIL` (Asesor de Servicios)
- **Contenido**: Análisis completo del AI, clasificación, y acciones sugeridas

---

## ⚙️ Variables de Entorno Requeridas

Agrega estas variables a tu `.env`:

```bash
# ============================================================================
# Resend Configuration (REQUERIDO)
# ============================================================================
RESEND_API_KEY=re_tu_api_key_aqui
RESEND_FROM_EMAIL=onboarding@resend.dev

# ============================================================================
# Email Destinatarios por Tipo
# ============================================================================

# Agente de Ventas (recibe leads con score >= 60%)
SALES_AGENT_EMAIL=ventas@belden.com

# Asesor Experto en Producto (recibe quejas de productos)
PRODUCT_EXPERT_EMAIL=productos@belden.com

# Asesor de Servicios (recibe temas de página/servicios/IT)
SERVICES_AGENT_EMAIL=servicios@belden.com

# Email de notificación general (fallback)
NOTIFICATION_EMAIL=notificaciones@belden.com

# URL del portal de IT Support
IT_SUPPORT_URL=https://support.belden.com/it
```

---

## 📋 Configuración por Agente

### 1. Lead Qualification Agent

**Trigger**: Score >= 60%

**Email enviado a**: `SALES_AGENT_EMAIL`

**Contenido del email**:
- ✅ Información completa del lead (Company, Contact, Industry, Revenue, etc.)
- ✅ Score de calificación y prioridad
- ✅ Datos enriquecidos de SAP (Business Partner, Orders, Revenue, Credit Rating)
- ✅ Razonamiento del AI
- ✅ Routing decision (AE/SDR/Nurture)
- ✅ Próximos pasos sugeridos
- ✅ Link a Salesforce

**Ejemplo de uso**:
```python
# El agente automáticamente envía email cuando score >= 60%
result = run_lead_qualification(lead_data, use_llm=True)
# Si score >= 0.60, email se envía automáticamente a SALES_AGENT_EMAIL
```

---

### 2. Complaint Classification Agent

#### A. Queja de Producto → Product Expert

**Trigger**: Clasificación = "Product Complaint"

**Email enviado a**: `PRODUCT_EXPERT_EMAIL`

**Contenido del email**:
- ✅ Categoría del producto (switches, cables, connectors, etc.)
- ✅ Nombre específico del producto (si se identifica)
- ✅ Información completa del ticket
- ✅ Análisis del AI (reasoning, sentiment, urgency)
- ✅ Respuesta sugerida
- ✅ Acciones requeridas

**Ejemplo**:
```
Ticket: "El switch Hirschmann se reinicia solo"
→ Clasificación: Product Complaint (switches)
→ Email enviado a: PRODUCT_EXPERT_EMAIL
```

#### B. Servicios/Página/IT → Services Agent

**Trigger**: Clasificación = "IT Support" o "Services/Page"

**Email enviado a**: `SERVICES_AGENT_EMAIL`

**Contenido del email**:
- ✅ Tipo de solicitud (servicios/página/IT)
- ✅ Información completa del ticket
- ✅ URL del portal de IT Support (si aplica)
- ✅ Análisis del AI
- ✅ Respuesta sugerida
- ✅ Acciones requeridas

**Ejemplo**:
```
Ticket: "No puedo acceder a la página web"
→ Clasificación: Services/Page/IT
→ Email enviado a: SERVICES_AGENT_EMAIL
```

---

## 🔧 Configuración en Vertex AI

Si el agente está desplegado en Vertex AI:

```bash
# Actualizar variables de entorno
python update_env_vars.py
```

O manualmente en Cloud Console:
1. Ve a **Vertex AI → Agent Engine**
2. Selecciona tu agente
3. Edita **Environment Variables**
4. Agrega todas las variables de email

---

## ✅ Checklist de Configuración

- [ ] `RESEND_API_KEY` configurado
- [ ] `RESEND_FROM_EMAIL` configurado
- [ ] `SALES_AGENT_EMAIL` configurado (para leads)
- [ ] `PRODUCT_EXPERT_EMAIL` configurado (para productos)
- [ ] `SERVICES_AGENT_EMAIL` configurado (para servicios)
- [ ] `NOTIFICATION_EMAIL` configurado (fallback)
- [ ] `IT_SUPPORT_URL` configurado
- [ ] Variables actualizadas en Vertex AI (si está desplegado)

---

## 🧪 Pruebas

### Test Lead Qualification

```bash
# Probar con un lead de alto valor
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_data": {
      "Company": "Acme Corp",
      "Title": "CTO",
      "Industry": "Technology",
      "Rating": "Hot",
      "AnnualRevenue": 10000000,
      "NumberOfEmployees": 500
    },
    "use_llm": true
  }'
```

**Resultado esperado**: Email enviado a `SALES_AGENT_EMAIL` si score >= 60%

### Test Product Complaint

```bash
# Probar con queja de producto
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Subject": "Switch not working",
      "Description": "Nuestro switch Hirschmann dejó de funcionar"
    }
  }'
```

**Resultado esperado**: Email enviado a `PRODUCT_EXPERT_EMAIL`

### Test Services/Page

```bash
# Probar con tema de servicios
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Subject": "Cannot access website",
      "Description": "No puedo acceder a la página web"
    }
  }'
```

**Resultado esperado**: Email enviado a `SERVICES_AGENT_EMAIL`

---

## 📊 Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    Lead Qualification                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Lead calificado                                           │
│ 2. Score calculado (LLM o reglas)                           │
│ 3. Si score >= 60%:                                         │
│    └─> 📧 Email a SALES_AGENT_EMAIL                         │
│        └─> Incluye: Lead + SAP + AI Analysis                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Complaint Classification                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Ticket clasificado (LLM)                                 │
│ 2. Si es PRODUCTO:                                          │
│    └─> 📧 Email a PRODUCT_EXPERT_EMAIL                      │
│        └─> Incluye: Producto + Análisis + Acciones          │
│ 3. Si es SERVICIOS/PÁGINA/IT:                              │
│    └─> 📧 Email a SERVICES_AGENT_EMAIL                      │
│        └─> Incluye: Servicio + Portal IT + Acciones        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Características de los Emails

Todos los emails incluyen:
- ✅ Diseño profesional y responsive
- ✅ Información completa y estructurada
- ✅ Análisis del AI con reasoning
- ✅ Respuestas sugeridas
- ✅ Acciones requeridas claras
- ✅ Links a sistemas (Salesforce, IT Portal)
- ✅ Badges de urgencia y prioridad
- ✅ Timestamps y metadata

---

## 📚 Referencias

- [Resend Setup Guide](RESEND_SETUP.md)
- [Architecture Overview](../ARCHITECTURE_OVERVIEW.md)

---

¿Preguntas? Revisa los logs o contacta al equipo de desarrollo. 🚀
