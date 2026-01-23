#!/usr/bin/env python3
"""
Actualizar variables de entorno del agente en Vertex AI Agent Engine.

Uso:
    python update_env_vars.py

Antes de ejecutar:
    1. Edita las variables abajo
    2. Asegúrate de estar autenticado: gcloud auth application-default login
"""

import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Cargar .env local
load_dotenv()

# Configuración del agente
PROJECT_ID = os.getenv("PROJECT_ID", "logical-hallway-485016-r7")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ID = "180545306838958080"
AGENT_RESOURCE = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}"


def get_env_vars_from_file() -> dict:
    """Lee las variables del archivo .env"""
    dotenv_path = Path('.env')
    
    if not dotenv_path.exists():
        print("❌ No se encontró archivo .env")
        return {}
    
    env_dict = dotenv_values(dotenv_path)
    
    # Filtrar solo las variables que queremos pasar al agente
    keys_to_include = [
        # OpenAI
        "OPENAI_API_KEY",
        
        # LangSmith
        "LANGSMITH_API_KEY",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
        
        # Salesforce
        "SALESFORCE_MODE",
        "SALESFORCE_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET",
        "SALESFORCE_USERNAME",
        "SALESFORCE_PASSWORD",
        "SALESFORCE_SECURITY_TOKEN",
        "SALESFORCE_LOGIN_URL",
        "SALESFORCE_API_VERSION",
        
        # SAP
        "SAP_MODE",
        "SAP_BASE_URL",
        "SAP_API_KEY",
        "SAP_USERNAME",
        "SAP_PASSWORD",
        "SAP_CLIENT",
        
        # Routing
        "ROUTING_AE_OWNER_ID",
        "ROUTING_SDR_OWNER_ID",
        "ROUTING_NURTURE_OWNER_ID",
        "ROUTING_ESCALATION_OWNER_ID",
        
        # Resend Email (REQUIRED for email notifications)
        "RESEND_API_KEY",
        "RESEND_FROM_EMAIL",
        
        # Email Recipients (REQUIRED)
        "SALES_AGENT_EMAIL",
        "PRODUCT_EXPERT_EMAIL",
        "SERVICES_AGENT_EMAIL",
        "NOTIFICATION_EMAIL",
        "IT_SUPPORT_URL",
        
        # Product Owners (Optional - for specific product routing)
        "PRODUCT_OWNER_SWITCHES",
        "PRODUCT_OWNER_CABLES",
        "PRODUCT_OWNER_CONNECTORS",
        "PRODUCT_OWNER_SOFTWARE",
        "PRODUCT_OWNER_INFRASTRUCTURE",
        "PRODUCT_OWNER_GENERAL",
    ]
    
    env_vars = {}
    for key in keys_to_include:
        value = env_dict.get(key) or os.getenv(key)
        if value:
            env_vars[key] = value
    
    return env_vars


def update_agent_env_vars(env_vars: dict):
    """Actualiza las variables de entorno del agente"""
    import vertexai
    from vertexai import agent_engines
    
    print(f"🔧 Conectando a Vertex AI...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print(f"   Agent: {AGENT_ID}")
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    print(f"\n📋 Variables a actualizar:")
    for key in env_vars.keys():
        # Ocultar valores sensibles
        if "KEY" in key or "SECRET" in key or "PASSWORD" in key or "TOKEN" in key:
            print(f"   {key}: ***hidden***")
        else:
            print(f"   {key}: {env_vars[key]}")
    
    print(f"\n⏳ Actualizando agente...")
    
    try:
        agent_engines.update(
            resource_name=AGENT_RESOURCE,
            env_vars=env_vars
        )
        print(f"\n✅ Variables de entorno actualizadas exitosamente!")
        print(f"\n🔗 Verifica en: https://console.cloud.google.com/vertex-ai/agents?project={PROJECT_ID}")
        
    except Exception as e:
        print(f"\n❌ Error al actualizar: {e}")
        raise


def main():
    print("=" * 60)
    print("🔄 ACTUALIZAR VARIABLES DE ENTORNO - AGENT ENGINE")
    print("=" * 60)
    
    # Obtener variables del .env
    env_vars = get_env_vars_from_file()
    
    if not env_vars:
        print("❌ No hay variables para actualizar")
        return
    
    print(f"\n📁 Cargadas {len(env_vars)} variables desde .env")
    
    # Confirmar
    response = input("\n¿Deseas continuar con la actualización? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelado")
        return
    
    # Actualizar
    update_agent_env_vars(env_vars)


if __name__ == "__main__":
    main()
