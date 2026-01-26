# Instrucciones para Lovable - Integración con Belden AI Agent

## 📋 Cómo usar este documento

Copia y pega los prompts de abajo directamente en Lovable. Lovable generará todo el código necesario para conectarse a tu Belden AI Agent.

---

## 🎯 PROMPT 1: Configuración Inicial del API

Copia y pega esto en Lovable:

```
Necesito integrar un API externo de un agente de IA para Belden. Por favor:

1. Crea un archivo `src/config/beldenApi.ts` con esta configuración:

const BELDEN_API_CONFIG = {
  baseUrl: "https://belden-agent-gateway-tahgwtwoha-uc.a.run.app",
  endpoints: {
    chat: "/chat",
    qualifyLead: "/qualify-lead",
    classifyTicket: "/classify-ticket",
    health: "/health"
  }
};

export default BELDEN_API_CONFIG;

2. Crea tipos TypeScript en `src/types/belden.ts`:

export interface ChatRequest {
  message: string;
  session_id?: string;
  lead_data?: Record<string, any>;
  ticket_data?: Record<string, any>;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  session_id?: string;
  error?: string;
}

export interface LeadData {
  Name: string;
  Company: string;
  Email: string;
  Phone?: string;
  Industry?: string;
  AnnualRevenue?: string;
}

export interface TicketData {
  subject: string;
  description: string;
  priority?: string;
}
```

---

## 🎯 PROMPT 2: Cliente del API

Copia y pega esto en Lovable:

```
Crea un cliente para el API de Belden en `src/services/beldenAgent.ts`:

Debe tener:
1. Una clase BeldenAgentClient que maneje la comunicación con el API
2. Método chat(message: string, additionalData?: any): Promise<ChatResponse>
3. Método qualifyLead(leadData: LeadData): Promise<ChatResponse>
4. Método classifyTicket(ticketData: TicketData): Promise<ChatResponse>
5. Método checkHealth(): Promise<any>
6. Manejo automático de session_id usando localStorage
7. Manejo de errores con try/catch
8. Headers correctos: Content-Type: application/json

Usa fetch API y la configuración de BELDEN_API_CONFIG.
Exporta una instancia singleton del cliente.
```

---

## 🎯 PROMPT 3: Interfaz de Chat

Copia y pega esto en Lovable:

```
Crea un componente de chat `src/components/BeldenChat.tsx`:

Requisitos:
1. Interfaz de chat moderna con:
   - Lista de mensajes (usuario y asistente)
   - Input para escribir mensajes
   - Botón de envío
   - Indicador de "escribiendo..." cuando el agente está procesando

2. Funcionalidad:
   - Usar el servicio beldenAgent.chat() para enviar mensajes
   - Mostrar respuestas del agente
   - Mantener historial de conversación en el estado
   - Permitir Enter para enviar
   - Deshabilitar input mientras se espera respuesta
   - Scroll automático al último mensaje

3. Diseño:
   - Estilos modernos con Tailwind CSS
   - Mensajes del usuario alineados a la derecha (bg-blue-500)
   - Mensajes del agente alineados a la izquierda (bg-gray-200)
   - Animaciones suaves
   - Responsive

4. Manejo de errores:
   - Mostrar mensaje de error si falla la llamada al API
   - Permitir reintentar
```

---

## 🎯 PROMPT 4: Formulario de Lead Qualification

Copia y pega esto en Lovable (si necesitas esta funcionalidad):

```
Crea un componente de calificación de leads `src/components/LeadQualification.tsx`:

Requisitos:
1. Formulario con campos:
   - Name (requerido)
   - Company (requerido)
   - Email (requerido, validación de email)
   - Phone (opcional)
   - Industry (dropdown con opciones comunes)
   - Annual Revenue (opcional)

2. Funcionalidad:
   - Usar beldenAgent.qualifyLead() al enviar
   - Validación de campos requeridos
   - Mostrar loading state mientras procesa
   - Mostrar resultado del agente (aprobado/rechazado)
   - Limpiar formulario después de envío exitoso

3. Diseño:
   - Usar Tailwind CSS
   - Formulario limpio y profesional
   - Botón de submit deshabilitado mientras carga
   - Mensajes de éxito/error claros
```

---

## 🎯 PROMPT 5: Formulario de Ticket Classification

Copia y pega esto en Lovable (si necesitas esta funcionalidad):

```
Crea un componente de clasificación de tickets `src/components/TicketClassification.tsx`:

Requisitos:
1. Formulario con campos:
   - Subject (requerido)
   - Description (textarea, requerido)
   - Priority (dropdown: Low, Medium, High)

2. Funcionalidad:
   - Usar beldenAgent.classifyTicket() al enviar
   - Mostrar respuesta del agente con la clasificación
   - Loading state
   - Manejo de errores

3. Diseño:
   - Tailwind CSS
   - Textarea expandible para descripción
   - Resultado mostrado en card bonita
```

---

## 🎯 PROMPT 6: Página Principal de Integración

Copia y pega esto en Lovable:

```
Crea una página principal `src/pages/BeldenAI.tsx` que integre los componentes:

Requisitos:
1. Layout con tabs o secciones para:
   - Chat con el agente
   - Calificación de Leads
   - Clasificación de Tickets

2. Header con:
   - Título "Belden AI Assistant"
   - Indicador de estado del API (health check)
   - Botón para limpiar sesión de chat

3. Funcionalidad:
   - Al cargar, hacer health check del API
   - Mostrar estado: conectado (verde) o desconectado (rojo)
   - Permitir cambiar entre las diferentes funcionalidades

4. Diseño:
   - Moderno y profesional
   - Responsive
   - Tailwind CSS
```

---

## 🎯 PROMPT 7: Hook Personalizado (Opcional pero recomendado)

Copia y pega esto en Lovable:

```
Crea un custom hook `src/hooks/useBeldenAgent.ts`:

Debe proporcionar:
1. Estado para: loading, error, sessionId
2. Funciones: sendMessage, qualifyLead, classifyTicket
3. Auto-manejo de estados de carga y error
4. Integración con el servicio beldenAgent

Esto simplificará el uso del agente en cualquier componente.
```

---

## ⚙️ CONFIGURACIÓN FINAL

Después de que Lovable genere el código, necesitas:

### 1. Actualizar la URL del API

En `src/config/beldenApi.ts`, reemplaza:
```typescript
baseUrl: "https://belden-agent-gateway-xxxxx-uc.a.run.app"
```

Con tu URL real del Cloud Run (la que obtuviste al ejecutar deploy.sh)

### 2. Probar la integración

Abre la aplicación y:
1. Verifica que el health check muestre "conectado"
2. Prueba enviar un mensaje en el chat
3. Prueba calificar un lead
4. Prueba clasificar un ticket

---

## 🔧 TROUBLESHOOTING

Si ves errores de CORS:
- Verifica que la URL del API sea correcta
- Asegúrate de que el backend esté desplegado en Cloud Run
- Revisa la consola del navegador para más detalles

Si no obtienes respuestas:
- Verifica que AGENT_ENDPOINT esté configurado en el backend
- Revisa los logs de Cloud Run: `gcloud run services logs read belden-agent-gateway --region us-central1`
- Prueba el health endpoint directamente en el navegador

Si hay errores de TypeScript:
- Pídele a Lovable que corrija los tipos
- Asegúrate de que todos los tipos estén importados correctamente

---

## 📝 NOTAS IMPORTANTES

1. **Session Management**: El chat mantiene sesión automáticamente usando localStorage
2. **Error Handling**: Todos los componentes deben manejar errores gracefully
3. **Loading States**: Siempre mostrar feedback visual durante llamadas al API
4. **Responsive**: Todos los componentes deben verse bien en móvil y desktop

---

## 🎨 PERSONALIZACIÓN ADICIONAL

Puedes pedirle a Lovable:
- Cambiar colores del tema
- Agregar animaciones
- Mejorar el diseño
- Agregar más funcionalidades
- Integrar con otros componentes de tu app

Ejemplo:
```
"Mejora el componente BeldenChat agregando:
- Avatares para usuario y asistente
- Timestamps en cada mensaje
- Opción para copiar respuestas
- Soporte para markdown en las respuestas del agente"
```
