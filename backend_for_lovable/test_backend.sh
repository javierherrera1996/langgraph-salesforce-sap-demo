#!/bin/bash
# Script para probar el backend de Belden AI

BACKEND_URL="https://belden-agent-gateway-tahgwtwoha-uc.a.run.app"

echo "======================================================================="
echo "🧪 PROBANDO BELDEN AI BACKEND"
echo "======================================================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo ""

# Test 1: Health Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Llamando: GET $BACKEND_URL/health"
echo ""

HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
echo "Respuesta:"
echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"
echo ""

# Verificar si el health check funcionó
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check EXITOSO"
else
    echo "❌ Health check FALLÓ"
    echo ""
    echo "El backend puede no estar corriendo o tener problemas."
    echo "Verifica los logs con:"
    echo "  gcloud run services logs read belden-agent-gateway --region us-central1 --limit 20"
    exit 1
fi

echo ""

# Test 2: Qualify Lead
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Qualify Lead"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Llamando: POST $BACKEND_URL/qualify-lead"
echo ""
echo "Body:"
cat << 'EOF'
{
  "Name": "John Doe",
  "Company": "Acme Corporation",
  "Email": "john@acme.com",
  "Title": "CTO",
  "Industry": "Manufacturing",
  "Rating": "Hot",
  "AnnualRevenue": 5000000,
  "NumberOfEmployees": 500,
  "LeadSource": "Partner Referral"
}
EOF
echo ""
echo ""

LEAD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/qualify-lead" \
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
  }')

echo "Respuesta:"
echo "$LEAD_RESPONSE" | jq '.' 2>/dev/null || echo "$LEAD_RESPONSE"
echo ""

if echo "$LEAD_RESPONSE" | grep -q "success"; then
    if echo "$LEAD_RESPONSE" | grep -q '"success":true'; then
        echo "✅ Lead qualification EXITOSO"
    else
        echo "⚠️  Lead qualification devolvió success:false"
        echo ""
        echo "Error:"
        echo "$LEAD_RESPONSE" | jq -r '.error' 2>/dev/null || echo "Unknown error"
    fi
else
    echo "❌ Lead qualification FALLÓ"
    echo ""
    echo "Esto puede indicar que el backend aún tiene el código viejo."
    echo "Necesitas redesplegar:"
    echo "  cd ~/langgraph-salesforce-sap-demo/backend_for_lovable"
    echo "  gcloud run deploy belden-agent-gateway --source . --platform managed --region us-central1 --allow-unauthenticated"
fi

echo ""

# Test 3: Classify Ticket
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Classify Ticket"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Llamando: POST $BACKEND_URL/classify-ticket"
echo ""
echo "Body:"
cat << 'EOF'
{
  "Subject": "Cable stopped working",
  "Description": "The Cat6 cable I bought stopped working after 2 months",
  "Priority": "High"
}
EOF
echo ""
echo ""

TICKET_RESPONSE=$(curl -s -X POST "$BACKEND_URL/classify-ticket" \
  -H 'Content-Type: application/json' \
  -d '{
    "Subject": "Cable stopped working",
    "Description": "The Cat6 cable I bought stopped working after 2 months",
    "Priority": "High"
  }')

echo "Respuesta:"
echo "$TICKET_RESPONSE" | jq '.' 2>/dev/null || echo "$TICKET_RESPONSE"
echo ""

if echo "$TICKET_RESPONSE" | grep -q "success"; then
    if echo "$TICKET_RESPONSE" | grep -q '"success":true'; then
        echo "✅ Ticket classification EXITOSO"
    else
        echo "⚠️  Ticket classification devolvió success:false"
        echo ""
        echo "Error:"
        echo "$TICKET_RESPONSE" | jq -r '.error' 2>/dev/null || echo "Unknown error"
    fi
else
    echo "❌ Ticket classification FALLÓ"
fi

echo ""
echo "======================================================================="
echo "📊 RESUMEN"
echo "======================================================================="
echo ""

# Contar tests exitosos
TESTS_PASSED=0
echo "$HEALTH_RESPONSE" | grep -q "healthy" && ((TESTS_PASSED++))
echo "$LEAD_RESPONSE" | grep -q '"success":true' && ((TESTS_PASSED++))
echo "$TICKET_RESPONSE" | grep -q '"success":true' && ((TESTS_PASSED++))

echo "Tests pasados: $TESTS_PASSED/3"
echo ""

if [ $TESTS_PASSED -eq 3 ]; then
    echo "✅ ¡TODOS LOS TESTS PASARON!"
    echo ""
    echo "El backend está funcionando correctamente."
    echo "Ya puedes usar PARA_LOVABLE.md para integrar con Lovable."
elif [ $TESTS_PASSED -eq 1 ]; then
    echo "⚠️  Solo el health check funciona"
    echo ""
    echo "El backend está corriendo pero tiene el código viejo."
    echo ""
    echo "🔧 SOLUCIÓN: Redesplegar el backend"
    echo ""
    echo "En Cloud Shell, ejecuta:"
    echo "  cd ~/langgraph-salesforce-sap-demo/backend_for_lovable"
    echo "  gcloud run deploy belden-agent-gateway \\"
    echo "    --source . \\"
    echo "    --platform managed \\"
    echo "    --region us-central1 \\"
    echo "    --allow-unauthenticated"
else
    echo "❌ El backend tiene problemas"
    echo ""
    echo "Revisa los logs:"
    echo "  gcloud run services logs read belden-agent-gateway --region us-central1 --limit 20"
fi

echo ""
