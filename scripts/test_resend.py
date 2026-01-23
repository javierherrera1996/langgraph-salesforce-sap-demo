#!/usr/bin/env python3
"""
Script de prueba para verificar que Resend está configurado correctamente.

Usage:
    python scripts/test_resend.py
    python scripts/test_resend.py --to tu-email@ejemplo.com
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables from project root
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

from src.tools.email import send_email
from src.config import get_resend_config


def test_resend_config():
    """Test Resend configuration."""
    print("🔍 Verificando configuración de Resend...")
    print("=" * 60)
    
    config = get_resend_config()
    
    # Check API key
    if not config.api_key:
        print("❌ RESEND_API_KEY no está configurado")
        return False
    
    if config.api_key.startswith("re_YOUR") or config.api_key.startswith("your_"):
        print("❌ RESEND_API_KEY parece ser un placeholder")
        print(f"   Valor actual: {config.api_key[:20]}...")
        return False
    
    print(f"✅ RESEND_API_KEY configurado: {config.api_key[:10]}...{config.api_key[-4:]}")
    
    # Check from email
    print(f"✅ RESEND_FROM_EMAIL: {config.from_email}")
    
    # Check notification email
    if config.notification_email:
        print(f"✅ NOTIFICATION_EMAIL: {config.notification_email}")
    else:
        print("⚠️  NOTIFICATION_EMAIL no configurado (usará RESEND_FROM_EMAIL)")
    
    # Check IT support URL
    print(f"✅ IT_SUPPORT_URL: {config.it_support_url}")
    
    print("=" * 60)
    return True


def test_send_email(to_email: str):
    """Test sending an email."""
    print(f"\n📧 Enviando email de prueba a: {to_email}")
    print("=" * 60)
    
    subject = "🧪 Test de Resend - Belden AI Agent"
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #1E3A5F, #3B82F6); color: white; padding: 20px; border-radius: 10px 10px 0 0; }
            .content { background: #F8FAFC; padding: 20px; border-radius: 0 0 10px 10px; }
            .success { background: #D1FAE5; padding: 15px; border-radius: 8px; border: 1px solid #10B981; margin: 20px 0; }
            .footer { text-align: center; padding: 20px; color: #6B7280; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0;">✅ Resend Configurado Correctamente</h1>
                <p style="margin:5px 0 0 0;">Belden AI Agent - Test de Email</p>
            </div>
            
            <div class="content">
                <div class="success">
                    <h2 style="margin:0; color: #065F46;">🎉 ¡Funciona!</h2>
                    <p style="margin:10px 0 0 0; color: #047857;">
                        Si estás viendo este email, significa que Resend está configurado correctamente
                        y el sistema puede enviar emails automáticamente.
                    </p>
                </div>
                
                <h3>📋 Configuración Verificada:</h3>
                <ul>
                    <li>✅ API Key configurada</li>
                    <li>✅ Email remitente: {from_email}</li>
                    <li>✅ Sistema de notificaciones activo</li>
                </ul>
                
                <h3>🚀 Próximos Pasos:</h3>
                <p>El sistema ahora puede enviar emails automáticamente cuando:</p>
                <ul>
                    <li>📊 Un lead tiene score >= 60%</li>
                    <li>📦 Se detecta una queja de producto</li>
                    <li>🎫 Se clasifica un ticket (siempre envía análisis del AI)</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>Belden AI Sales Agent</p>
                <p>Powered by LangGraph + Resend</p>
            </div>
        </div>
    </body>
    </html>
    """.format(from_email=get_resend_config().from_email)
    
    try:
        result = send_email(
            to=to_email,
            subject=subject,
            html_content=html_content
        )
        
        if result.get("success"):
            if result.get("simulated"):
                print("⚠️  Email SIMULADO (Resend no está completamente configurado)")
                print("   Esto significa que el email no se envió realmente")
            else:
                print("✅ Email enviado exitosamente!")
                print(f"   Message ID: {result.get('message_id', 'N/A')}")
                print(f"   To: {result.get('to')}")
                print(f"   From: {result.get('from', get_resend_config().from_email)}")
                print("\n💡 Revisa tu bandeja de entrada (y spam) en unos segundos")
        else:
            print(f"❌ Error al enviar email: {result.get('error', 'Unknown error')}")
            return False
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test Resend email configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default notification email
  python scripts/test_resend.py
  
  # Test with specific email
  python scripts/test_resend.py --to tu-email@ejemplo.com
        """
    )
    
    parser.add_argument(
        "--to",
        type=str,
        default=None,
        help="Email address to send test email to (default: NOTIFICATION_EMAIL from config)"
    )
    
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Only check configuration, don't send email"
    )
    
    args = parser.parse_args()
    
    print("🧪 Test de Configuración de Resend")
    print("=" * 60)
    print()
    
    # Test configuration
    if not test_resend_config():
        print("\n❌ Configuración incorrecta. Por favor revisa tu .env")
        sys.exit(1)
    
    if args.config_only:
        print("\n✅ Configuración verificada correctamente")
        sys.exit(0)
    
    # Determine recipient
    config = get_resend_config()
    to_email = args.to or config.notification_email or config.from_email
    
    if not to_email:
        print("\n❌ No se puede determinar el email destinatario")
        print("   Configura NOTIFICATION_EMAIL en .env o usa --to")
        sys.exit(1)
    
    # Test sending email
    if test_send_email(to_email):
        print("\n✅ Test completado exitosamente!")
        print("\n💡 Si recibiste el email, Resend está funcionando correctamente")
        print("   Si no lo recibes, revisa:")
        print("   - Bandeja de spam")
        print("   - Logs de Resend en https://resend.com/emails")
        print("   - Que el email destinatario sea válido")
    else:
        print("\n❌ Test falló")
        sys.exit(1)


if __name__ == "__main__":
    main()
