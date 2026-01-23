#!/usr/bin/env python3
"""
Test directo de Resend usando la API key proporcionada.
"""

import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import resend

# Tu API key
API_KEY = "re_JqyccKa7_LhZSx8XcXEXLoNbEBc8iSLKy"
TO_EMAIL = "andreshebe96@gmail.com"

print("🧪 Test Directo de Resend")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...{API_KEY[-4:]}")
print(f"To: {TO_EMAIL}")
print("=" * 60)

try:
    resend.api_key = API_KEY
    
    params = {
        "from": "onboarding@resend.dev",
        "to": [TO_EMAIL],
        "subject": "✅ Test Resend - Belden AI Agent",
        "html": """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #1E3A5F, #3B82F6); color: white; padding: 20px; border-radius: 10px 10px 0 0; }
                .content { background: #F8FAFC; padding: 20px; border-radius: 0 0 10px 10px; }
                .success { background: #D1FAE5; padding: 15px; border-radius: 8px; border: 1px solid #10B981; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">✅ Resend Funcionando!</h1>
                    <p style="margin:5px 0 0 0;">Belden AI Agent - Test Directo</p>
                </div>
                <div class="content">
                    <div class="success">
                        <h2 style="margin:0; color: #065F46;">🎉 ¡Funciona!</h2>
                        <p style="margin:10px 0 0 0; color: #047857;">
                            Si estás viendo este email, Resend está configurado correctamente.
                        </p>
                    </div>
                    <p>El sistema ahora puede enviar emails automáticamente cuando:</p>
                    <ul>
                        <li>📊 Un lead tiene score >= 60%</li>
                        <li>📦 Se detecta una queja de producto</li>
                        <li>🎫 Se clasifica un ticket (siempre envía análisis del AI)</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
    }
    
    print("\n📧 Enviando email...")
    response = resend.Emails.send(params)
    
    print("✅ Email enviado exitosamente!")
    print(f"   Message ID: {response.get('id', 'N/A')}")
    print(f"   To: {TO_EMAIL}")
    print(f"   From: onboarding@resend.dev")
    print("\n💡 Revisa tu bandeja de entrada (y spam) en unos segundos")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
