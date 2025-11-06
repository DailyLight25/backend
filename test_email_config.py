#!/usr/bin/env python
"""
Test script to verify your SMTP email configuration.
Run this after adding your credentials to .env file.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salt_and_light.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_config():
    """Test the email configuration by attempting to send a test email."""
    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    
    # Check if credentials are configured
    if not settings.EMAIL_HOST_USER:
        print("❌ ERROR: EMAIL_HOST_USER is not configured")
        print("\nPlease add the following to your .env file:")
        print("  EMAIL_HOST_USER=your-email@gmail.com")
        print("  EMAIL_HOST_PASSWORD=your-app-password")
        print("  DEFAULT_FROM_EMAIL=your-email@gmail.com")
        return False
    
    if not settings.EMAIL_HOST_PASSWORD:
        print("❌ ERROR: EMAIL_HOST_PASSWORD is not configured")
        print("\nPlease add EMAIL_HOST_PASSWORD to your .env file")
        return False
    
    print(f"✅ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"✅ EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"✅ EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"✅ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"✅ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"✅ EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)}")
    print(f"✅ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Prompt for test email
    test_email = input("Enter your email address to send a test email: ").strip()
    
    if not test_email:
        print("❌ No email address provided")
        return False
    
    print("\nSending test email...")
    try:
        send_mail(
            subject='DayLight Email Verification Test',
            message=f'Hello!\n\nThis is a test email from your DayLight application.\n\nIf you received this, your email configuration is working correctly!\n\nNext steps:\n1. Register a new user on your app\n2. Check your inbox for the verification email\n3. Click the verification link\n\nBest regards,\nDayLight Team',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        print("✅ Test email sent successfully!")
        print(f"Check your inbox at: {test_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        print("\n🔧 Common issues:")
        print("1. Gmail: Must use App Password, NOT your regular password")
        print("   → Get one at: https://myaccount.google.com/apppasswords")
        print("   → Requires 2-Step Verification to be enabled first")
        print("2. Firewall: Check if port 587 is blocked")
        print("3. Credentials: Double-check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
        print("\n📖 See EMAIL_SETUP.md for detailed instructions")
        return False

if __name__ == '__main__':
    success = test_email_config()
    sys.exit(0 if success else 1)

