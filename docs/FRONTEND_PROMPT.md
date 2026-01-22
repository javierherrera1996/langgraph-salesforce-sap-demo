# 🎨 Prompt para Crear Frontend del Belden AI Sales Agent

Copia y pega este prompt completo a un agente experto en frontend (Claude, GPT-4, etc.)

---

## PROMPT COMPLETO

```
Eres un experto en desarrollo frontend con especialización en interfaces de AI/ML. 
Necesito que crees una interfaz web moderna y profesional para un Agente de AI empresarial.

## 📋 CONTEXTO DEL PROYECTO

Hemos desarrollado un **Agente de AI para Belden** (empresa de soluciones de red industrial) 
que automatiza dos procesos de ventas:

1. **Lead Qualification**: Califica leads de Salesforce y los asigna al vendedor correcto
2. **Ticket Triage**: Categoriza tickets de soporte y toma acciones automáticas

El agente está desplegado en **Google Cloud Vertex AI Agent Engine** y expone una API REST.

## 🔌 API BACKEND

### Endpoint
```
POST https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/180545306838958080:query
```

### Headers
```
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
```

### Request - Lead Qualification
```json
{
  "input": {
    "action": "qualify_lead",
    "lead_data": {
      "Id": "00Q000001",
      "Company": "Enterprise Corp",
      "FirstName": "John",
      "LastName": "Smith",
      "Title": "Chief Technology Officer",
      "Industry": "Manufacturing",
      "Rating": "Hot",
      "AnnualRevenue": 5000000,
      "NumberOfEmployees": 500,
      "LeadSource": "Partner Referral",
      "Email": "john@enterprise.com",
      "Description": "Looking for industrial network solutions"
    },
    "use_llm": true
  }
}
```

### Response - Lead Qualification
```json
{
  "output": {
    "score": 0.85,
    "routing": {
      "owner_type": "AE",
      "owner_id": "005000001",
      "priority": "P1",
      "reason": "High-value enterprise lead"
    },
    "reasoning": "[VERDICT: P1] This lead scores 0.85 because:\n1. TITLE: CTO is C-level with decision authority\n2. COMPANY: 500 employees, $5M revenue matches ICP\n3. SIGNALS: Hot rating + Partner Referral = high intent\nCONCLUSION: Immediate AE engagement recommended",
    "confidence": 0.92,
    "key_factors": ["C-level title", "Hot rating", "Partner referral", "High revenue"],
    "recommended_action": "Schedule discovery call within 24 hours",
    "model_used": "gpt-4o-mini",
    "actions_executed": ["fetch_lead", "enrich_lead", "score_lead", "decide_routing", "execute_actions"]
  }
}
```

### Request - Ticket Triage
```json
{
  "input": {
    "action": "triage_ticket",
    "case_data": {
      "Id": "500000001",
      "CaseNumber": "00099001",
      "Subject": "URGENT: Network failure - Production DOWN",
      "Description": "All switches stopped working. Production halted. Losing $50K/hour!",
      "Priority": "High",
      "Status": "New",
      "Origin": "Phone"
    },
    "use_llm": true
  }
}
```

### Response - Ticket Triage
```json
{
  "output": {
    "category": "outage",
    "decision": {
      "action": "escalate",
      "response": "I understand this is critical. I'm escalating immediately to our incident team.",
      "escalation_reason": "Production impact with significant financial loss",
      "priority_change": "Critical"
    },
    "reasoning": "This ticket indicates a critical production outage with significant business impact ($50K/hour loss). Keywords 'DOWN', 'URGENT', 'stopped working' indicate immediate escalation is required.",
    "confidence": 0.95,
    "sentiment": "frustrated",
    "urgency": "critical",
    "requires_escalation": true,
    "suggested_response": "I sincerely apologize for this critical situation. I've immediately escalated this to our Priority Incident Team who will contact you within 15 minutes. Your case has been marked as Critical priority. Reference: 00099001",
    "model_used": "gpt-4o-mini"
  }
}
```

### Request - Health Check
```json
{
  "input": {
    "action": "health"
  }
}
```

## 🎯 REQUERIMIENTOS DE LA INTERFAZ

### Pantallas Principales

1. **Dashboard Home**
   - Resumen de métricas (leads procesados, tickets triageados)
   - Acceso rápido a Lead Qualification y Ticket Triage
   - Últimas actividades

2. **Lead Qualification**
   - Formulario para ingresar datos del lead
   - Campos: Company, Title (dropdown), Industry (dropdown), Rating (slider: Cold/Warm/Hot), 
     Revenue (slider), Employees (slider), Source (dropdown), Description (textarea)
   - Botón "Qualify Lead"
   - Resultados visuales:
     - Score grande con color (verde ≥0.75, amarillo 0.45-0.74, rojo <0.45)
     - Badge de prioridad (P1 🔥, P2 ⚡, P3 ❄️)
     - Routing destination (Account Executive, SDR, Nurture)
     - Confidence meter
     - Key factors como tags/chips
     - AI Reasoning en un box destacado (esto es MUY importante mostrar)

3. **Ticket Triage**
   - Formulario para ticket
   - Campos: Subject, Description (textarea grande), Priority (dropdown), Origin (dropdown)
   - Templates pre-cargados para demo:
     - "🚨 Production Outage"
     - "💰 Billing Issue"
     - "❓ How-To Question"
     - "🔒 Security Alert"
   - Resultados visuales:
     - Categoría con icono y color
     - Sentiment con emoji (😤 frustrated, 😐 neutral, 😊 happy)
     - Urgency level con color
     - Escalation badge si aplica
     - Suggested response en textarea editable
     - AI Reasoning destacado

4. **History/Activity Log**
   - Lista de todas las consultas hechas
   - Filtros por tipo (lead/ticket)
   - Expandir para ver detalles

### Componentes de UI Importantes

1. **Score Display Component**
   ```
   ┌─────────────────────┐
   │       0.85          │  ← Número grande
   │    ━━━━━━━━━●━━     │  ← Progress bar con color
   │      P1 - Hot       │  ← Label
   └─────────────────────┘
   ```

2. **AI Reasoning Box** (CRÍTICO - debe verse prominente)
   ```
   ┌─ 🤖 AI Reasoning ─────────────────────────────────┐
   │                                                    │
   │  [VERDICT: P1] This lead scores 0.85 because:     │
   │                                                    │
   │  1. TITLE: CTO is C-level with decision authority │
   │  2. COMPANY: 500 employees matches enterprise ICP │
   │  3. SIGNALS: Hot + Partner Referral = high intent │
   │                                                    │
   │  CONCLUSION: Immediate AE engagement recommended  │
   │                                                    │
   └───────────────────────────────────────────────────┘
   ```

3. **Category Cards** (para tickets)
   ```
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ 🚨       │ │ 💰       │ │ ❓       │ │ 🔒       │
   │ OUTAGE   │ │ BILLING  │ │ HOW-TO   │ │ SECURITY │
   │ Critical │ │ Medium   │ │ Low      │ │ High     │
   └──────────┘ └──────────┘ └──────────┘ └──────────┘
   ```

### Estilo Visual

- **Paleta de colores**:
  - Primary: #1E3A5F (azul corporativo oscuro)
  - Success/P1: #10B981 (verde)
  - Warning/P2: #F59E0B (amarillo/naranja)
  - Danger/P3: #EF4444 (rojo)
  - Background: #F8FAFC (gris muy claro)
  - Cards: #FFFFFF con sombra suave

- **Tipografía**: 
  - Headlines: Inter o SF Pro Display (bold)
  - Body: Inter o system-ui
  - Monospace para JSON/código: JetBrains Mono

- **Estilo general**:
  - Moderno, limpio, profesional
  - Bordes redondeados (8-12px)
  - Sombras sutiles
  - Animaciones suaves en transiciones
  - Responsive (desktop first, pero mobile-friendly)

### Tecnologías Sugeridas

Elige UNA de estas opciones:

**Opción A: React + Tailwind (Recomendado)**
- React 18+ con TypeScript
- Tailwind CSS
- Shadcn/ui o Radix para componentes
- React Query para API calls
- Framer Motion para animaciones

**Opción B: Next.js**
- Next.js 14+ con App Router
- Tailwind CSS
- Server Actions para API calls

**Opción C: Vue + Nuxt**
- Nuxt 3
- Tailwind CSS
- Pinia para estado

**Opción D: Vanilla HTML/CSS/JS** (más simple)
- HTML5 semántico
- CSS con variables y Flexbox/Grid
- Fetch API para llamadas

## 🔐 AUTENTICACIÓN

Para desarrollo/demo, el token se obtiene con:
```bash
gcloud auth print-access-token
```

Para producción, necesitarás:
1. Service Account de GCP
2. Generar JWT token programáticamente
3. O usar un backend proxy que maneje la auth

Para la demo inicial, puedes:
- Tener un input donde pegar el token
- O hardcodearlo temporalmente
- O crear un endpoint proxy en tu backend

## 📁 ESTRUCTURA DE ARCHIVOS SUGERIDA

```
frontend/
├── src/
│   ├── components/
│   │   ├── LeadForm.tsx
│   │   ├── LeadResult.tsx
│   │   ├── TicketForm.tsx
│   │   ├── TicketResult.tsx
│   │   ├── ScoreDisplay.tsx
│   │   ├── ReasoningBox.tsx
│   │   ├── CategoryCard.tsx
│   │   └── SentimentBadge.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── LeadQualification.tsx
│   │   ├── TicketTriage.tsx
│   │   └── History.tsx
│   ├── services/
│   │   └── agentApi.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
├── public/
└── package.json
```

## 📝 DATOS DE EJEMPLO PARA TESTING

### Lead P1 (debe dar score alto ~0.85)
```json
{
  "Company": "Industrial Manufacturing Corp",
  "Title": "Chief Technology Officer",
  "Industry": "Manufacturing",
  "Rating": "Hot",
  "AnnualRevenue": 50000000,
  "NumberOfEmployees": 2500,
  "LeadSource": "Partner Referral",
  "Description": "Need to upgrade network infrastructure across 5 plants"
}
```

### Lead P3 (debe dar score bajo ~0.25)
```json
{
  "Company": "Small Startup Inc",
  "Title": "Junior Developer",
  "Industry": "Technology",
  "Rating": "Cold",
  "AnnualRevenue": 100000,
  "NumberOfEmployees": 8,
  "LeadSource": "Cold Call",
  "Description": "Just browsing"
}
```

### Ticket Outage (debe categorizar como "outage", escalate)
```json
{
  "Subject": "URGENT: Complete network failure",
  "Description": "Production is DOWN. All switches failed. Losing $50K/hour!",
  "Priority": "High",
  "Origin": "Phone"
}
```

### Ticket How-To (debe categorizar como "howto", auto-reply)
```json
{
  "Subject": "How to configure VLAN?",
  "Description": "I need help setting up VLANs on my new switch. Where's the documentation?",
  "Priority": "Low",
  "Origin": "Web"
}
```

## ✅ ENTREGABLES ESPERADOS

1. Código fuente completo y funcional
2. README con instrucciones de instalación
3. Configuración de variables de entorno
4. Screenshots o GIFs de la interfaz

## 🎯 PRIORIDADES

1. **CRÍTICO**: Mostrar el AI Reasoning de forma prominente - esto es lo más importante para la demo
2. **ALTO**: Visualización clara del score y prioridad con colores
3. **ALTO**: Formularios intuitivos con validación
4. **MEDIO**: Animaciones y transiciones suaves
5. **MEDIO**: Responsive design
6. **BAJO**: Dark mode (nice to have)

## 🚀 COMENZAR

Empieza creando la estructura del proyecto y el componente de LeadQualification primero, 
ya que es el caso de uso principal. Luego agrega TicketTriage y finalmente el Dashboard.

¿Tienes alguna pregunta antes de comenzar?
```

---

## 📋 Notas Adicionales para el Agente Frontend

- El endpoint está en producción y funcionando
- Los tokens de GCP expiran en 1 hora
- Para desarrollo, puede usar un token hardcodeado temporalmente
- La respuesta del API viene envuelta en `{"output": {...}}`
- El campo `reasoning` es texto plano con saltos de línea `\n`
- Los campos `key_factors` y `actions_executed` son arrays de strings

---

## 🔗 Recursos

- **GitHub Repo**: https://github.com/javierherrera1996/langgraph-salesforce-sap-demo
- **API Docs**: Ver `docs/ARCHITECTURE_OVERVIEW.md`
- **Postman Collection**: `demo/postman_collection.json`
