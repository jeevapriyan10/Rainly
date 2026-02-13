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

# Initialize Gmail SMTP (optional)
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

if GMAIL_ADDRESS and GMAIL_PASSWORD:
    EMAIL_ENABLED = True
    print("[SUCCESS] Gmail SMTP enabled")
else:
    EMAIL_ENABLED = False
    print("[WARN] Gmail not configured (Email disabled)")

def format_sms_alert(region_name: str, river_name: str, risk_level: str, water_level: float, threshold: float, action: str) -> str:
    """Format SMS message (max 160 chars for free SMS)"""
    if risk_level == "CRITICAL":
        return f"[CRITICAL] FLOOD at {region_name}, {river_name}! Water {water_level}m (limit {threshold}m). EVACUATE NOW!"
    elif risk_level == "HIGH":
        return f"[HIGH] Flood risk at {region_name}, {river_name}. Water {water_level}m. Evacuate immediately."
    elif risk_level == "MEDIUM":
        return f"[WARNING] Flood warning at {region_name}. Water rising. Prepare for evacuation."
    else:
        return f"[INFO] Flood monitor: {region_name} normal. Water {water_level}m."

def format_email_alert(participant_name: str, region_name: str, river_name: str, risk_level: str, water_level: float, threshold: float, rainfall: float, action: str) -> str:
    """Format HTML email"""
    color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(risk_level, "#6b7280")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
            .alert-box {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid {color}; }}
            .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 0.875rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Rainly Flood Alert</h1>
                <p style="margin: 5px 0 0 0; font-size: 1.125rem;">{risk_level} RISK DETECTED</p>
            </div>
            
            <div class="content">
                <p><strong>Dear {participant_name},</strong></p>
                
                <p>This is an automated flood alert for your region:</p>
                
                <div class="alert-box">
                    <h3 style="margin-top: 0; color: {color};">{region_name}, {river_name}</h3>
                    <p><strong>Risk Level:</strong> {risk_level}</p>
                    <p><strong>Water Level:</strong> {water_level:.2f}m (Threshold: {threshold:.1f}m)</p>
                    <p><strong>Rainfall:</strong> {rainfall:.0f}mm</p>
                    <p><strong>Action Required:</strong> {action.upper()}</p>
                </div>
                
                <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin-top: 20px;">
                    <strong>Recommended Actions:</strong>
                    <ul>
                        {'<li>Move to higher ground immediately</li>' if risk_level in ['CRITICAL', 'HIGH'] else ''}
                        {'<li>Prepare emergency supplies</li>' if risk_level in ['CRITICAL', 'HIGH', 'MEDIUM'] else ''}
                        {'<li>Stay tuned for updates</li>'}
                        <li>Follow local authorities' instructions</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>Rainly - Early Flood Detection System for India</p>
                <p>This is an automated message. Do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

async def send_sms(phone: str, message: str) -> dict:
    """Send SMS via Twilio"""
    if not TWILIO_ENABLED:
        print(f"[INFO] SMS disabled. Would send to {phone}: {message}")
        return {"status": "disabled", "message": "Twilio not configured"}
    
    try:
        msg = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=phone
        )
        print(f"[SUCCESS] SMS sent to {phone}: {msg.sid}")
        return {"status": "sent", "sid": msg.sid}
    except Exception as e:
        print(f"[ERROR] SMS failed for {phone}: {e}")
        return {"status": "failed", "error": str(e)}

async def send_email(to_email: str, subject: str, html_body: str) -> dict:
    """Send email via Gmail SMTP"""
    if not EMAIL_ENABLED:
        print(f"[INFO] Email disabled. Would send to {to_email}")
        return {"status": "disabled", "message": "Gmail not configured"}
    
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
