#!/bin/bash
# Script para iniciar LangGraph Studio

set -e

echo "🎨 Iniciando LangGraph Studio..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "langgraph.json" ]; then
    echo "❌ Error: langgraph.json no encontrado"
    echo "   Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Advertencia: .env no encontrado"
    echo "   Creando .env desde .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ .env creado. Por favor, configura las variables necesarias."
    else
        echo "   ❌ .env.example no encontrado"
        exit 1
    fi
fi

# Verificar que langgraph-cli está instalado
if ! command -v langgraph &> /dev/null; then
    echo "📦 Instalando langgraph-cli..."
    pip install langgraph-cli[inmem]
fi

# Verificar variables de entorno críticas
if ! grep -q "OPENAI_API_KEY" .env || grep -q "OPENAI_API_KEY=your_" .env; then
    echo "⚠️  Advertencia: OPENAI_API_KEY no configurado en .env"
    echo "   El LLM no funcionará sin esta clave"
fi

echo "✅ Configuración verificada"
echo ""
echo "🚀 Iniciando LangGraph Studio..."
echo ""
echo "📝 URLs disponibles:"
echo "   - LangGraph Studio UI: http://localhost:8123"
echo "   - API Server:          http://localhost:8124"
echo ""
echo "💡 Presiona Ctrl+C para detener"
echo ""

# Iniciar LangGraph Studio
langgraph dev
