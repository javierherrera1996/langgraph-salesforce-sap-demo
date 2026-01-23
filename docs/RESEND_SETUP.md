# 📧 Configuración de Resend para Envío de Emails

Esta guía explica cómo configurar **Resend** para que el sistema pueda enviar emails automáticamente.

---

## 🎯 ¿Qué hace Resend?

Resend envía emails automáticamente cuando:
- ✅ Un lead tiene score >= 60% (alerta de lead calificado)
- ✅ Se clasifica un ticket como queja de producto (email al encargado)
- ✅ Se clasifica un ticket (SIEMPRE envía análisis del AI)

---

## 📋 Paso 1: Crear Cuenta en Resend

1. Ve a [https://resend.com](https://resend.com)
2. Crea una cuenta (gratis para empezar)
3. Verifica tu email

---

## 🔑 Paso 2: Obtener API Key

1. Una vez dentro del dashboard, ve a **API Keys**
2. Haz clic en **Create API Key**
3. Dale un nombre (ej: "Belden AI Agent")
4. Copia la API key (empieza con `re_...`)

⚠️ **Importante**: Guarda la API key de forma segura. Solo se muestra una vez.

---

## ⚙️ Paso 3: Configurar Variables de Entorno

### Opción A: Desarrollo Local (`.env`)

Edita tu archivo `.env`:

```bash
# Resend Email Configuration
RESEND_API_KEY=re_tu_api_key_aqui
RESEND_FROM_EMAIL=onboarding@resend.dev
NOTIFICATION_EMAIL=tu-email@ejemplo.com
IT_SUPPORT_URL=https://support.belden.com/it

# Product Owners (opcional - para quejas de producto)
PRODUCT_OWNER_SWITCHES=switches-owner@belden.com
PRODUCT_OWNER_CABLES=cables-owner@belden.com
PRODUCT_OWNER_CONNECTORS=connectors-owner@belden.com
PRODUCT_OWNER_SOFTWARE=software-owner@belden.com
PRODUCT_OWNER_INFRASTRUCTURE=infra-owner@belden.com
```

### Opción B: Vertex AI Agent Engine

Si el agente está desplegado en Vertex AI:

```bash
# Actualizar variables de entorno
python update_env_vars.py
```

O manualmente desde Cloud Console:
1. Ve a **Vertex AI → Agent Engine**
2. Selecciona tu agente
3. Edita **Environment Variables**
4. Agrega:
   - `RESEND_API_KEY=re_tu_api_key`
   - `RESEND_FROM_EMAIL=onboarding@resend.dev`
   - `NOTIFICATION_EMAIL=tu-email@ejemplo.com`
   - `IT_SUPPORT_URL=https://support.belden.com/it`

---

## 📧 Paso 4: Configurar Email Remitente

### Para Testing (Recomendado al inicio)

Usa el email de prueba de Resend:
```bash
RESEND_FROM_EMAIL=onboarding@resend.dev
```

Este email funciona inmediatamente sin configuración adicional.

### Para Producción

1. En el dashboard de Resend, ve a **Domains**
2. Haz clic en **Add Domain**
3. Ingresa tu dominio (ej: `belden.com`)
4. Agrega los registros DNS que Resend te proporciona:
   - **SPF Record**
   - **DKIM Records**
   - **DMARC Record** (opcional pero recomendado)
5. Espera a que se verifique (puede tardar unos minutos)
6. Una vez verificado, usa:
   ```bash
   RESEND_FROM_EMAIL=noreply@belden.com
   ```

---

## ✅ Paso 5: Verificar Configuración

### Test Local

```bash
# Ejecutar test de email
python -c "
from src.tools.email import send_email
result = send_email(
    to='tu-email@ejemplo.com',
    subject='Test desde Belden AI',
    html_content='<h1>✅ Resend configurado correctamente!</h1>'
)
print(result)
"
```

### Test desde API

```bash
# Probar endpoint de lead (debe enviar email si score >= 60%)
curl -X POST http://localhost:8000/run/lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_data": {
      "Company": "Test Corp",
      "Title": "CTO",
      "Industry": "Technology",
      "Rating": "Hot",
      "AnnualRevenue": 10000000,
      "NumberOfEmployees": 500
    },
    "use_llm": true
  }'
```

### Test de Clasificación de Tickets

```bash
# Probar clasificación (SIEMPRE envía email con análisis)
curl -X POST http://localhost:8000/run/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "case_data": {
      "Id": "test-1",
      "Subject": "Switch not working",
      "Description": "Nuestro switch Hirschmann dejó de funcionar"
    }
  }'
```

---

## 🔍 Troubleshooting

### ❌ Error: "Invalid API Key"

**Causa**: La API key no es válida o no está configurada.

**Solución**:
1. Verifica que `RESEND_API_KEY` esté en `.env`
2. Verifica que la key empiece con `re_`
3. Genera una nueva key si es necesario

### ❌ Error: "Domain not verified"

**Causa**: Estás usando un dominio no verificado.

**Solución**:
- Para testing: usa `onboarding@resend.dev`
- Para producción: verifica tu dominio en Resend

### ❌ No se envían emails

**Causa**: Resend no está configurado correctamente.

**Solución**:
1. Verifica logs: `📧 [SIMULATED]` significa que está en modo simulación
2. Verifica que `RESEND_API_KEY` esté configurado
3. Verifica que el paquete esté instalado: `pip install resend`
4. Revisa el dashboard de Resend para ver si hay errores

### ⚠️ Emails van a Spam

**Causa**: Dominio no verificado o falta configuración SPF/DKIM.

**Solución**:
1. Verifica tu dominio en Resend
2. Configura SPF y DKIM records
3. Usa un dominio verificado en producción

---

## 📊 Monitoreo

### Ver Emails Enviados

1. Ve a [Resend Dashboard](https://resend.com/emails)
2. Verás todos los emails enviados
3. Puedes ver:
   - Estado (sent, delivered, bounced)
   - Timestamp
   - Destinatario
   - Subject

### Ver Logs en la Aplicación

Los logs muestran:
```
✅ Email sent successfully to: user@example.com
   Message ID: abc123...
```

O si no está configurado:
```
⚠️ Resend not configured - simulating email
📧 [SIMULATED] Email to: user@example.com
```

---

## 💰 Límites y Precios

### Plan Gratuito
- ✅ 3,000 emails/mes
- ✅ 100 emails/día
- ✅ API access
- ✅ Email tracking

### Planes de Pago
- Ver [Resend Pricing](https://resend.com/pricing) para más detalles

---

## 🔐 Seguridad

### ✅ Mejores Prácticas

1. **Nunca commitees la API key** a Git
2. **Usa variables de entorno** para almacenar la key
3. **Rota las keys** periódicamente
4. **Usa dominios verificados** en producción
5. **Configura SPF/DKIM** para mejor deliverability

### 🚫 No Hacer

- ❌ Hardcodear la API key en el código
- ❌ Compartir la API key públicamente
- ❌ Usar la misma key en múltiples proyectos sin restricciones

---

## 📝 Variables de Entorno Completas

```bash
# ============================================================================
# Resend Email Configuration
# ============================================================================

# API Key (REQUERIDO)
RESEND_API_KEY=re_tu_api_key_aqui

# Email remitente (default: onboarding@resend.dev para testing)
RESEND_FROM_EMAIL=onboarding@resend.dev

# Email para recibir notificaciones (REQUERIDO)
NOTIFICATION_EMAIL=tu-email@ejemplo.com

# URL del portal de IT Support
IT_SUPPORT_URL=https://support.belden.com/it

# ============================================================================
# Product Owners (Opcional - para quejas de producto)
# ============================================================================

PRODUCT_OWNER_SWITCHES=switches-owner@belden.com
PRODUCT_OWNER_CABLES=cables-owner@belden.com
PRODUCT_OWNER_CONNECTORS=connectors-owner@belden.com
PRODUCT_OWNER_SOFTWARE=software-owner@belden.com
PRODUCT_OWNER_INFRASTRUCTURE=infra-owner@belden.com
PRODUCT_OWNER_GENERAL=general-owner@belden.com
```

---

## ✅ Checklist de Configuración

- [ ] Cuenta creada en Resend
- [ ] API Key obtenida y guardada
- [ ] `RESEND_API_KEY` configurado en `.env`
- [ ] `RESEND_FROM_EMAIL` configurado
- [ ] `NOTIFICATION_EMAIL` configurado
- [ ] Test de email ejecutado exitosamente
- [ ] Email recibido en bandeja de entrada
- [ ] (Opcional) Dominio verificado para producción
- [ ] (Opcional) Product owners configurados
- [ ] Variables actualizadas en Vertex AI (si está desplegado)

---

## 🎉 ¡Listo!

Una vez configurado, el sistema enviará emails automáticamente:

1. **Lead Alerts**: Cuando un lead tiene score >= 60%
2. **Product Complaints**: Cuando se detecta una queja de producto
3. **Ticket Analysis**: SIEMPRE que se clasifica un ticket (con análisis completo del AI)

---

## 📚 Referencias

- [Resend Documentation](https://resend.com/docs)
- [Resend API Reference](https://resend.com/docs/api-reference)
- [Resend Python SDK](https://github.com/resendlabs/resend-python)

---

¿Problemas? Revisa los logs o contacta al equipo de desarrollo. 🚀
