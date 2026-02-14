"""
Enhanced Notification Service
Sends SMS (Twilio) and Email (Gmail SMTP) flood alerts
"""
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Initialize Twilio (optional)
try:
    from twilio.rest import Client
    
    TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE = os.getenv('TWILIO_PHONE_NUMBER')
    
    if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
        twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
        TWILIO_ENABLED = True
        print("[SUCCESS] Twilio SMS enabled")
    else:
        TWILIO_ENABLED = False
        print("[WARN] Twilio not configured (SMS disabled)")
except Exception as e:
    TWILIO_ENABLED = False
    print(f"[WARN] Twilio not available: {e}")

# Initialize Resend (HTTP API - Best for Render/Vercel)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
import requests

def send_via_resend(to_email: str, subject: str, html_body: str) -> dict:
    """Send email via Resend HTTP API (Bypasses SMTP blocks)"""
    if not RESEND_API_KEY:
        return {"status": "failed", "error": "Missing RESEND_API_KEY"}
    
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Rainly Alert <onboarding@resend.dev>",
                "to": [to_email],
                "subject": subject,
                "html": html_body
            }
        )
        if response.status_code in [200, 201, 202]:
            print(f"[SUCCESS] Resend Email sent to {to_email}")
            return {"status": "sent", "provider": "resend", "id": response.json().get('id')}
        else:
            print(f"[ERROR] Resend failed: {response.text}")
            return {"status": "failed", "error": response.text}
    except Exception as e:
        print(f"[ERROR] Resend exception: {e}")
        return {"status": "failed", "error": str(e)}

async def send_email(to_email: str, subject: str, html_body: str) -> dict:
    """Send email via Resend (Preferred) or Gmail SMTP (Fallback)"""
    
    # 1. Try Resend API first (Works on Render/Vercel)
    if RESEND_API_KEY:
        return send_via_resend(to_email, subject, html_body)
        
    # 2. Try Gmail SMTP (Often blocked on Cloud)
    if not EMAIL_ENABLED:
        print(f"[INFO] Email disabled. Would send to {to_email}")
        return {"status": "disabled", "message": "Gmail/Resend not configured"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Rainly Alerts <{GMAIL_ADDRESS}>"
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Try standard TLS port 587 first
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(GMAIL_ADDRESS.strip(), GMAIL_PASSWORD.strip())
                server.send_message(msg)
        except Exception as e1:
            print(f"[WARN] Port 587 failed ({e1}), trying SSL 465...")
            # Fallback to SSL port 465
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
                server.login(GMAIL_ADDRESS.strip(), GMAIL_PASSWORD.strip())
                server.send_message(msg)
        
        print(f"[SUCCESS] Email sent to {to_email}")
        return {"status": "sent"}
    except Exception as e:
        print(f"[ERROR] Email failed for {to_email}: {e}")
        print("💡 HINT: Cloud providers (Render/Vercel) often block SMTP. Use 'RESEND_API_KEY' instead!")
        return {"status": "failed", "error": str(e)}

async def send_flood_alert(participant: dict, region: dict, device: dict, prediction: dict, sensor_data: dict) -> dict:
    """
    Send both SMS and Email flood alert
    Returns: {
        "sms": {"status": "sent" | "failed" | "disabled"},
        "email": {"status": "sent" | "failed" | "disabled"}
    }
    """
    # Format messages
    sms_message = format_sms_alert(
        region_name=region['name'],
        river_name=region['river_name'],
        risk_level=prediction['risk_level'],
        water_level=sensor_data['water_level'],
        threshold=device['alert_threshold'],
        action=prediction['warning_type']
    )
    
    email_html = format_email_alert(
        participant_name=participant['name'],
        region_name=region['name'],
        river_name=region['river_name'],
        risk_level=prediction['risk_level'],
        water_level=sensor_data['water_level'],
        threshold=device['alert_threshold'],
        rainfall=sensor_data['rainfall'],
        action=prediction['warning_type']
    )
    
    email_subject = f"[{prediction['risk_level']}] Flood Alert - {region['name']}"
    
    # Send both
    results = {}
    
    # Send SMS
    if participant.get('phone'):
        results['sms'] = await send_sms(participant['phone'], sms_message)
    else:
        results['sms'] = {"status": "no_phone"}
    
    # Send Email (construct from phone if no email field)
    participant_email = participant.get('email')
    if not participant_email:
        # Some participants might only have phone
        participant_email = None
    
    if participant_email:
        # Use LLM to generate detailed email content if available
        try:
            from llm_service import LLM_ENABLED, generate_detailed_warning
            if LLM_ENABLED:
                detailed_html = generate_detailed_warning(
                    participant=participant,
                    region=region,
                    device=device,
                    prediction=prediction,
                    sensor_data=sensor_data
                )
                results['email'] = await send_email(participant_email, email_subject, detailed_html)
            else:
                # Fallback to standard email
                results['email'] = await send_email(participant_email, email_subject, email_html)
        except Exception as e:
            print(f"[WARN] LLM email generation failed, using fallback: {e}")
            results['email'] = await send_email(participant_email, email_subject, email_html)
    else:
        results['email'] = {"status": "no_email"}
    
    return results

async def send_notification(participant: dict, message: str):
    """Legacy function for compatibility"""
    phone = participant.get('phone', '')
    if phone:
        return await send_sms(phone, message)
    return {"status": "no_phone"}
