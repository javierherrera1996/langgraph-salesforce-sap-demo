#!/usr/bin/env python3
"""
Test script to verify that Resend is configured correctly.

Usage:
    python scripts/test_resend.py
    python scripts/test_resend.py --to your-email@example.com
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
    print("🔍 Checking Resend configuration...")
    print("=" * 60)

    config = get_resend_config()

    # Check API key
    if not config.api_key:
        print("❌ RESEND_API_KEY is not configured")
        return False

    if config.api_key.startswith("re_YOUR") or config.api_key.startswith("your_"):
        print("❌ RESEND_API_KEY appears to be a placeholder")
        print(f"   Current value: {config.api_key[:20]}...")
        return False
    
    print(f"✅ RESEND_API_KEY configured: {config.api_key[:10]}...{config.api_key[-4:]}")

    # Check from email
    print(f"✅ RESEND_FROM_EMAIL: {config.from_email}")

    # Check notification email
    if config.notification_email:
        print(f"✅ NOTIFICATION_EMAIL: {config.notification_email}")
    else:
        print("⚠️  NOTIFICATION_EMAIL not configured (will use RESEND_FROM_EMAIL)")

    # Check IT support URL
    print(f"✅ IT_SUPPORT_URL: {config.it_support_url}")

    print("=" * 60)
    return True


def test_send_email(to_email: str):
    """Test sending an email."""
    print(f"\n📧 Sending test email to: {to_email}")
    print("=" * 60)

    subject = "🧪 Resend Test - Belden AI Agent"
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
                <h1 style="margin:0;">✅ Resend Configured Correctly</h1>
                <p style="margin:5px 0 0 0;">Belden AI Agent - Email Test</p>
            </div>

            <div class="content">
                <div class="success">
                    <h2 style="margin:0; color: #065F46;">🎉 It Works!</h2>
                    <p style="margin:10px 0 0 0; color: #047857;">
                        If you're seeing this email, it means Resend is configured correctly
                        and the system can send emails automatically.
                    </p>
                </div>

                <h3>📋 Configuration Verified:</h3>
                <ul>
                    <li>✅ API Key configured</li>
                    <li>✅ Sender email: {from_email}</li>
                    <li>✅ Notification system active</li>
                </ul>

                <h3>🚀 Next Steps:</h3>
                <p>The system can now send emails automatically when:</p>
                <ul>
                    <li>📊 A lead has score >= 60%</li>
                    <li>📦 A product complaint is detected</li>
                    <li>🎫 A ticket is classified (always sends AI analysis)</li>
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
                print("⚠️  Email SIMULATED (Resend is not fully configured)")
                print("   This means the email was not actually sent")
            else:
                print("✅ Email sent successfully!")
                print(f"   Message ID: {result.get('message_id', 'N/A')}")
                print(f"   To: {result.get('to')}")
                print(f"   From: {result.get('from', get_resend_config().from_email)}")
                print("\n💡 Check your inbox (and spam) in a few seconds")
        else:
            print(f"❌ Error sending email: {result.get('error', 'Unknown error')}")
            return False
        
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
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
  python scripts/test_resend.py --to your-email@example.com
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

    print("🧪 Resend Configuration Test")
    print("=" * 60)
    print()

    # Test configuration
    if not test_resend_config():
        print("\n❌ Incorrect configuration. Please check your .env")
        sys.exit(1)

    if args.config_only:
        print("\n✅ Configuration verified successfully")
        sys.exit(0)

    # Determine recipient
    config = get_resend_config()
    to_email = args.to or config.notification_email or config.from_email

    if not to_email:
        print("\n❌ Cannot determine recipient email")
        print("   Configure NOTIFICATION_EMAIL in .env or use --to")
        sys.exit(1)

    # Test sending email
    if test_send_email(to_email):
        print("\n✅ Test completed successfully!")
        print("\n💡 If you received the email, Resend is working correctly")
        print("   If you didn't receive it, check:")
        print("   - Spam folder")
        print("   - Resend logs at https://resend.com/emails")
        print("   - That the recipient email is valid")
    else:
        print("\n❌ Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
