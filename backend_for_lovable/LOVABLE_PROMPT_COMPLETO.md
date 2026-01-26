# 🚀 Prompt Completo para Lovable (Todo en Uno)

Si prefieres que Lovable genere todo de una vez, copia y pega este prompt completo:

---

## 📋 PROMPT ÚNICO - COPIAR Y PEGAR EN LOVABLE

```
Necesito integrar un agente de IA de Belden que está desplegado en Google Cloud Run. El agente maneja chat, calificación de leads y clasificación de tickets de soporte.

CONFIGURACIÓN DEL API:
- URL Base: https://belden-agent-gateway-tahgwtwoha-uc.a.run.app
- Endpoints disponibles:
  * POST /chat - Para chat general
  * POST /qualify-lead - Para calificar leads
  * POST /classify-ticket - Para clasificar tickets
  * GET /health - Para verificar estado

ESTRUCTURA QUE NECESITO:

1. CONFIGURACIÓN (src/config/beldenApi.ts):
   - Objeto de configuración con baseUrl y endpoints
   - Exportar configuración

2. TIPOS TYPESCRIPT (src/types/belden.ts):
   - ChatRequest: { message: string, session_id?: string, lead_data?: any, ticket_data?: any }
   - ChatResponse: { success: boolean, response: string, session_id?: string, error?: string }
   - LeadData: { Name, Company, Email, Phone?, Industry?, AnnualRevenue? }
   - TicketData: { subject, description, priority? }

3. SERVICIO API (src/services/beldenAgent.ts):
   - Clase BeldenAgentClient con métodos:
     * chat(message, additionalData?): envía mensaje y recibe respuesta
     * qualifyLead(leadData): califica un lead
     * classifyTicket(ticketData): clasifica un ticket
     * checkHealth(): verifica estado del API
   - Manejar session_id automáticamente con localStorage (key: 'belden_session_id')
   - Usar fetch API
   - Manejo de errores con try/catch
   - Exportar instancia singleton

4. COMPONENTE DE CHAT (src/components/BeldenChat.tsx):
   - Interfaz de chat moderna con Tailwind CSS
   - Lista de mensajes (usuario: azul derecha, agente: gris izquierda)
   - Input de texto + botón enviar
   - Soporte para Enter
   - Loading state ("Agent is thinking...")
   - Auto-scroll al último mensaje
   - Manejo de errores visible

5. FORMULARIO DE LEADS (src/components/LeadQualification.tsx):
   - Campos: Name*, Company*, Email*, Phone, Industry (dropdown), AnnualRevenue
   - Validación de campos requeridos
   - Botón submit con loading state
   - Mostrar respuesta del agente
   - Limpiar form después de éxito
   - Tailwind CSS

6. FORMULARIO DE TICKETS (src/components/TicketClassification.tsx):
   - Campos: Subject*, Description* (textarea), Priority (dropdown: Low/Medium/High)
   - Loading state
   - Mostrar clasificación del agente
   - Tailwind CSS

7. PÁGINA PRINCIPAL (src/pages/BeldenAI.tsx):
   - Tabs o secciones para: Chat, Lead Qualification, Ticket Classification
   - Header con título "Belden AI Assistant"
   - Indicador de estado del API (verde=conectado, rojo=error)
   - Health check al cargar
   - Botón "Clear Session"
   - Diseño responsive y moderno

8. CUSTOM HOOK (src/hooks/useBeldenAgent.ts):
   - Estado: loading, error, sessionId
   - Funciones: sendMessage, qualifyLead, classifyTicket
   - Simplificar uso del agente en componentes

REQUISITOS TÉCNICOS:
- Usar TypeScript
- Tailwind CSS para estilos
- Responsive design
- Manejo de errores en todos los componentes
- Loading states visibles
- Animaciones suaves
- Headers correctos: Content-Type: application/json

COMPORTAMIENTO ESPERADO:
- El chat mantiene contexto de conversación mediante session_id
- Cada componente muestra feedback inmediato al usuario
- Errores se muestran de forma clara y amigable
- La aplicación verifica conectividad con el API al iniciar

Por favor genera todos estos archivos con código completo, funcional y bien comentado.
```

---

## 🎯 DESPUÉS DE QUE LOVABLE GENERE EL CÓDIGO

### Paso 1: Actualizar URL del API

Ve a `src/config/beldenApi.ts` y verifica que tenga:
```typescript
baseUrl: "https://belden-agent-gateway-tahgwtwoha-uc.a.run.app"
```

Esta es la URL de tu backend desplegado en Cloud Run

### Paso 2: Verificar que el backend esté corriendo

Antes de probar en Lovable, asegúrate de haber desplegado el backend:

```bash
cd backend_for_lovable
export AGENT_ENDPOINT="https://us-central1-aiplatform.googleapis.com/v1/projects/logical-hallway-485016-r7/locations/us-central1/reasoningEngines/180545306838958080"
bash deploy.sh
```

### Paso 3: Probar la integración

1. Abre tu app de Lovable
2. Ve a la página Belden AI
3. Verifica que el indicador de estado muestre "conectado" (verde)
4. Prueba enviar un mensaje de chat
5. Prueba calificar un lead
6. Prueba clasificar un ticket

---

## 🔧 SI ALGO NO FUNCIONA

### El indicador muestra "desconectado"
```bash
# Verifica que el backend esté corriendo
curl https://belden-agent-gateway-tahgwtwoha-uc.a.run.app/health

# Revisa los logs
gcloud run services logs read belden-agent-gateway --region us-central1 --limit 20
```

### Error de CORS
- Verifica que la URL en beldenApi.ts sea exactamente la misma que te dio Cloud Run
- No agregues "/" al final de la URL

### No recibo respuestas del agente
```bash
# Verifica que AGENT_ENDPOINT esté configurado
gcloud run services describe belden-agent-gateway \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### Errores de TypeScript en Lovable
Pídele a Lovable que corrija:
```
"Hay errores de TypeScript en [nombre del archivo]. Por favor corrígelos manteniendo la funcionalidad."
```

---

## 🎨 MEJORAS OPCIONALES

Después de que todo funcione, puedes pedirle a Lovable:

```
"Mejora el componente BeldenChat con:
- Avatares para usuario y agente
- Timestamps en mensajes
- Botón para copiar respuestas
- Soporte para renderizar markdown en las respuestas"
```

```
"Agrega un dashboard que muestre:
- Estadísticas de leads calificados hoy
- Tickets clasificados por prioridad
- Gráficas de actividad"
```

```
"Agrega notificaciones toast cuando:
- Se califica un lead exitosamente
- Hay un error de conexión
- Se limpia la sesión"
```
