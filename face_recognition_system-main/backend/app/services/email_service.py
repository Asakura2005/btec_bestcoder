# app/services/email_service.py

import requests
import os
from typing import Optional

# Resend configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
RESEND_API_URL = 'https://api.resend.com/emails'
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'Employee System <noreply@resend.dev>')

def send_password_reset_email(email: str, reset_token: str, user_type: str, user_name: str = '') -> bool:
    """
    Gửi email reset password qua Resend
    
    Args:
        email: Email người nhận
        reset_token: JWT token để reset
        user_type: 'admin' hoặc 'employee'
        user_name: Tên người dùng
    
    Returns:
        bool: True nếu gửi thành công
    
    Raises:
        Exception: Nếu có lỗi khi gửi email
    """
    
    if not RESEND_API_KEY:
        raise Exception("RESEND_API_KEY not configured")
    
    # Tạo reset URL
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Email subject
    account_type = "Admin" if user_type == "admin" else "Employee"
    subject = f"Reset Your Password - Employee Management System ({account_type})"
    
    # Email content
    html_content = create_reset_email_html(reset_url, user_type, user_name)
    
    # Resend payload
    payload = {
        'from': FROM_EMAIL,
        'to': [email],
        'subject': subject,
        'html': html_content
    }
    
    # Headers
    headers = {
        'Authorization': f'Bearer {RESEND_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(RESEND_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Reset email sent to {email} - Email ID: {result.get('id')}")
            return True
        else:
            error_data = response.json() if response.content else {}
            print(f"❌ Resend API error: {response.status_code} - {error_data}")
            raise Exception(f"Failed to send email: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error sending email: {str(e)}")
        raise Exception(f"Network error: {str(e)}")


def create_reset_email_html(reset_url: str, user_type: str, user_name: str = '') -> str:
    """Tạo HTML template cho email reset password"""
    
    greeting = f"Hi {user_name}," if user_name else "Hi there,"
    account_type = "Admin" if user_type == "admin" else "Employee"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #1976d2; margin-bottom: 10px; }}
            .reset-btn {{ display: inline-block; background: #1976d2; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 20px 0; color: #856404; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Employee Management System</div>
                <h1 style="color: #1976d2;">Password Reset Request</h1>
            </div>
            
            <p>{greeting}</p>
            
            <p>You requested to reset your password for your <strong>{account_type}</strong> account.</p>
            
            <p>Click the button below to set a new password:</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="reset-btn">Reset My Password</a>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important:</strong>
                <ul>
                    <li>This link expires in <strong>30 minutes</strong></li>
                    <li>You can only use this link <strong>once</strong></li>
                    <li>If you didn't request this, please ignore this email</li>
                </ul>
            </div>
            
            <p>If the button doesn't work, copy and paste this link:</p>
            <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px;">{reset_url}</p>
            
            <div class="footer">
                <p>© 2025 Employee Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
