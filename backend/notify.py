"""
Enhanced Notification Service
Sends SMS (Twilio) and Email (Gmail SMTP / Resend API) flood alerts.
"""
import os
import smtplib
import requests
import asyncio
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

load_dotenv()

# Initialize Twilio (optional)
TWILIO_ENABLED = False
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
        print("[WARN] Twilio not configured (SMS disabled)")
except Exception as e:
    print(f"[WARN] Twilio not available: {e}")

# Email Configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
EMAIL_ENABLED = bool(RESEND_API_KEY or (GMAIL_ADDRESS and GMAIL_PASSWORD))

def format_sms_alert(region_name: str, river_name: str, risk_level: str, water_level: float, threshold: float, action: str) -> str:
    """Format SMS message (max 160 chars for free SMS)"""
    if risk_level == "CRITICAL":
        return f"[CRITICAL] FLOOD at {region_name}, {river_name}! Water {water_level:.2f}m (limit {threshold:.1f}m). EVACUATE NOW!"
    elif risk_level == "HIGH":
        return f"[HIGH] Flood risk at {region_name}, {river_name}. Water {water_level:.2f}m. Evacuate immediately."
    elif risk_level == "MEDIUM":
        return f"[WARNING] Flood warning at {region_name}. Water rising to {water_level:.2f}m. Prepare for evacuation."
    else:
        return f"[INFO] Flood monitor: {region_name} normal. Water {water_level:.2f}m."

def format_email_alert(participant_name: str, region_name: str, river_name: str, risk_level: str, water_level: float, threshold: float, rainfall: float, action: str) -> str:
    """Format HTML email using standard f-string"""
    color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(risk_level, "#6b7280")
    
    # Conditional list items
    actions_list = ""
    if risk_level in ['CRITICAL', 'HIGH']:
        actions_list += "<li>Move to higher ground immediately</li>"
        actions_list += "<li>Do not walk through moving water</li>"
    if risk_level in ['CRITICAL', 'HIGH', 'MEDIUM']:
        actions_list += "<li>Prepare emergency supplies (Medekit, Water, Torch)</li>"
    actions_list += "<li>Stay tuned for official updates</li>"
    actions_list += "<li>Follow local authorities' instructions</li>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; }}
            .header {{ background: {color}; color: white; padding: 25px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background: #ffffff; padding: 25px; border-radius: 0 0 8px 8px; }}
            .alert-box {{ background: #fdf2f2; padding: 20px; margin: 20px 0; border-left: 5px solid {color}; border-radius: 4px; }}
            .data-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }}
            .footer {{ text-align: center; margin-top: 25px; color: #6b7280; font-size: 0.875rem; border-top: 1px solid #e5e7eb; padding-top: 15px; }}
            .btn {{ display: inline-block; background: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">FLOOD ALERT</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px; font-weight: bold;">{risk_level} RISK - {region_name.upper()}</p>
            </div>
            
            <div class="content">
                <p><strong>Dear {participant_name},</strong></p>
                
                <p>This is an automated flood warning from the Rainly Early Detection System.</p>
                
                <div class="alert-box">
                    <h3 style="margin-top: 0; color: {color}; text-transform: uppercase;">Current Status: {risk_level}</h3>
                    <p><strong>Location:</strong> {region_name}, {river_name}</p>
                    <p><strong>Action Required:</strong> <span style="font-weight: bold; font-size: 1.1em;">{action.upper()}</span></p>
                    
                    <hr style="border: 0; border-top: 1px solid #ffcccc; margin: 15px 0;">
                    
                    <div class="data-grid">
                        <div>Water Level:<br><strong>{water_level:.2f}m</strong> <small>(Limit: {threshold:.1f}m)</small></div>
                        <div>Rainfall:<br><strong>{rainfall:.0f}mm</strong></div>
                    </div>
                </div>
                
                <div style="background: #fefce8; padding: 20px; border-radius: 8px; border: 1px solid #fde047; margin-top: 20px;">
                    <strong style="color: #854d0e; display: block; margin-bottom: 10px;">Recommended Safety Actions:</strong>
                    <ul style="margin: 0; padding-left: 20px; color: #713f12;">
                        {actions_list}
                    </ul>
                </div>

                <p style="text-align: center;">
                    <a href="#" class="btn">View Live Dashboard</a>
                </p>
            </div>
            
            <div class="footer">
                <p><strong>Rainly - AI-Powered Flood detection System</strong></p>
                <p>Emergency Contacts: 1078 (NDRF) | 100 (Police) | 108 (Ambulance)</p>
                <p style="font-size: 0.75rem;">This is an automated message generated based on real-time sensor data.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def _sync_send_resend(to_email: str, subject: str, html_body: str) -> dict:
    """Blocking Send via Resend"""
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

def _sync_send_smtp(to_email: str, subject: str, html_body: str) -> dict:
    """Blocking Send via SMTP"""
    if not EMAIL_ENABLED:
        print(f"[INFO] Email disabled. Would send to {to_email}")
        return {"status": "disabled", "message": "Gmail/Resend not configured"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Rainly Alerts <{GMAIL_ADDRESS}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(GMAIL_ADDRESS.strip(), GMAIL_PASSWORD.strip())
                server.send_message(msg)
        except Exception as e1:
            print(f"[WARN] Port 587 failed ({e1}), trying SSL 465...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
                server.login(GMAIL_ADDRESS.strip(), GMAIL_PASSWORD.strip())
                server.send_message(msg)
        
        print(f"[SUCCESS] Email sent to {to_email}")
        return {"status": "sent"}
    except Exception as e:
        print(f"[ERROR] Email failed for {to_email}: {e}")
        return {"status": "failed", "error": str(e)}

def _sync_send_sms(to_phone: str, message: str) -> dict:
    """Blocking Send via Twilio"""
    if not TWILIO_ENABLED:
        return {"status": "disabled", "message": "Twilio not configured"}
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_phone
        )
        print(f"[SUCCESS] SMS sent to {to_phone}")
        return {"status": "sent", "sid": message.sid}
    except Exception as e:
        print(f"[ERROR] SMS failed for {to_phone}: {e}")
        return {"status": "failed", "error": str(e)}

async def send_email(to_email: str, subject: str, html_body: str) -> dict:
    """Async wrapper for email sending"""
    if RESEND_API_KEY:
        return await asyncio.to_thread(_sync_send_resend, to_email, subject, html_body)
    return await asyncio.to_thread(_sync_send_smtp, to_email, subject, html_body)

async def send_sms(to_phone: str, message: str) -> dict:
    """Async wrapper for SMS sending"""
    return await asyncio.to_thread(_sync_send_sms, to_phone, message)

async def send_flood_alert(participant: dict, region: dict, device: dict, prediction: dict, sensor_data: dict) -> dict:
    """
    Send both SMS and Email flood alert.
    Orchestrates the notification process non-blockingly.
    """
    results = {}
    
    # 1. SMS (Fastest)
    sms_message = format_sms_alert(
        region_name=region.get('name', 'Unknown'),
        river_name=region.get('river_name', 'Unknown'),
        risk_level=prediction.get('risk_level', 'UNKNOWN'),
        water_level=sensor_data.get('water_level', 0),
        threshold=device.get('alert_threshold', 0),
        action=prediction.get('warning_type', 'monitor')
    )
    
    if participant.get('phone'):
        results['sms'] = await send_sms(participant['phone'], sms_message)
    else:
        results['sms'] = {"status": "no_phone"}
    
    # 2. Email (Detailed)
    participant_email = participant.get('email')
    if participant_email:
        email_subject = f"[{prediction.get('risk_level', 'INFO')}] Flood Alert - {region.get('name', 'Unknown')}"
        
        # Try to use LLM for detailed email if enabled
        email_content = None
        try:
            if os.getenv("LLM_ENABLED", "false").lower() == "true":
                from llm_service import generate_detailed_warning
                # Run potentially slow LLM generation in thread
                email_content = await asyncio.to_thread(
                    generate_detailed_warning,
                    participant=participant,
                    region=region,
                    device=device,
                    prediction=prediction,
                    sensor_data=sensor_data
                )
        except Exception as e:
            print(f"[WARN] LLM Email generation failed, using standard template: {e}")
        
        # Fallback if LLM failed or disabled
        if not email_content:
            email_content = format_email_alert(
                participant_name=participant.get('name', 'Resident'),
                region_name=region.get('name', 'Unknown'),
                river_name=region.get('river_name', 'Unknown'),
                risk_level=prediction.get('risk_level', 'UNKNOWN'),
                water_level=sensor_data.get('water_level', 0),
                threshold=device.get('alert_threshold', 0),
                rainfall=sensor_data.get('rainfall', 0),
                action=prediction.get('warning_type', 'monitor')
            )
            
        results['email'] = await send_email(participant_email, email_subject, email_content)
    else:
        results['email'] = {"status": "no_email"}
    
    return results

async def send_notification(participant: dict, message: str):
    """Legacy helper for simple messages"""
    phone = participant.get('phone')
    if phone:
        return await send_sms(phone, message)
    return {"status": "no_phone"}
