# Integración Lovable con Belden AI Backend

## 📋 COPIAR Y PEGAR ESTO EN LOVABLE:

```
Necesito integrar mi aplicación con un backend de IA que ya está desplegado.

BACKEND URL: https://belden-agent-gateway-tahgwtwoha-uc.a.run.app

ENDPOINTS DISPONIBLES:

1. Health Check
GET /health
Respuesta: { "status": "healthy", "authentication": "ok", "agent_endpoint": "..." }

2. Calificar Lead
POST /qualify-lead
Body: {
  "Name": "John Doe",
  "Company": "Acme Corp",
  "Email": "john@acme.com",
  "Title": "CTO",
  "Industry": "Manufacturing",
  "Rating": "Hot",
  "AnnualRevenue": 5000000,
  "NumberOfEmployees": 500,
  "LeadSource": "Partner Referral"
}
Respuesta: {
  "success": true,
  "response": "Lead qualification complete.\nScore: 85%\nRouting: AE\nReasoning: ...",
  "session_id": null,
  "error": null
}

3. Clasificar Ticket/Queja
POST /classify-ticket
Body: {
  "Subject": "Cable stopped working",
  "Description": "The Cat6 cable I bought stopped working after 2 months",
  "Priority": "High"
}
Respuesta: {
  "success": true,
  "response": "Ticket classified.\nType: Product Complaint\nCategory: cables\nAction: email_sent\nReasoning: ...",
  "session_id": null,
  "error": null
}

REQUISITOS:
- Usa fetch API nativo de JavaScript
- Content-Type: application/json
- No necesitas autenticación (el backend maneja tokens automáticamente)
- Maneja errores con try/catch

Por favor crea:
1. Un archivo de configuración src/config/api.ts con la URL del backend
2. Un servicio src/services/beldenApi.ts con funciones para llamar cada endpoint
3. Componentes React para:
   - Formulario de Lead Qualification
   - Formulario de Ticket Classification
   - Mostrar las respuestas del backend

Usa TypeScript y Tailwind CSS.
```

---

## ✅ Eso es todo

Lovable generará:
- La configuración del API
- Los servicios para llamar el backend
- Los componentes UI
- El manejo de errores

El backend ya está listo en: `https://belden-agent-gateway-tahgwtwoha-uc.a.run.app`
