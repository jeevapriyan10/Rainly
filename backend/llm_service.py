"""
LLM Service for Local Quantized Models
Optimized for small GGUF models: TinyLlama (669MB), Qwen2-0.5B (352MB), Phi-2 (1.6GB)
Uses llama-cpp-python for fast CPU inference
"""

import os
import json
from typing import Dict, Any, Optional

# Configuration
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google") # 'local' or 'google'
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "models/llm")
LLM_MODEL_FILE = os.getenv("LLM_MODEL_FILE", "qwen2-0_5b-instruct-q4_k_m.gguf")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Global model instance
_model = None
_gemini_model = None

def initialize_llm():
    """Initialize LLM (Local or Google Gemini)"""
    global _model, _gemini_model
    
    if not LLM_ENABLED:
        print("[WARN] LLM is disabled. Using enhanced rule-based system.")
        return False
    
    if LLM_PROVIDER == "google":
        try:
            import google.generativeai as genai
            if not GEMINI_API_KEY:
                print("[ERROR] GEMINI_API_KEY not found in .env")
                return False
            
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_model = genai.GenerativeModel('gemini-pro')
            print("[SUCCESS] Google Gemini Pro loaded successfully!")
            return True
        except ImportError:
            print("[ERROR] google-generativeai not installed. Run: pip install google-generativeai")
            return False
        except Exception as e:
            print(f"[ERROR] Gemini initialization failed: {e}")
            return False

    elif LLM_PROVIDER == "local":
        try:
            from llama_cpp import Llama
            
            model_path = os.path.join(LLM_MODEL_PATH, LLM_MODEL_FILE)
            
            if not os.path.exists(model_path):
                print(f"[ERROR] Model not found: {model_path}")
                print(f"   Using Dummy/Fallback mode.")
                return False
            
            print(f"[INFO] Loading GGUF model: {LLM_MODEL_FILE}")
            _model = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                n_gpu_layers=0,
                verbose=False
            )
            print(f"[SUCCESS] Local Model loaded successfully!")
            return True
            
        except ImportError:
            print("[ERROR] llama-cpp-python not installed")
            return False
        except Exception as e:
            print(f"[ERROR] Local model loading failed: {e}")
            return False
    
    return False

def generate_with_llm(prompt: str, max_tokens: int = 500) -> str:
    """Generate text using configured provider"""
    try:
        if LLM_PROVIDER == "google" and _gemini_model:
            response = _gemini_model.generate_content(prompt)
            return response.text
            
        elif LLM_PROVIDER == "local" and _model:
            response = _model(
                prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                stop=["</s>", "\n\n\n"],
                echo=False
            )
            return response["choices"][0]["text"].strip()
            
    except Exception as e:
        print(f"Generation failed: {e}")
        return "Analysis unavailable at this moment."
    
    return "LLM not initialized properly."

def analyze_with_llm(sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyze flood risk using LLM and return structured data
    """
    if not LLM_ENABLED or (_model is None and _gemini_model is None):
        return None

    prompt = f"""You are a hydrology expert. Analyze this sensor data and determine flood risk.
    
    Data:
    - Water Level: {sensor_data['water_level']}m (Threshold: {sensor_data['threshold']}m)
    - Rainfall: {sensor_data['rainfall']}mm
    - Flow Rate: {sensor_data['flow_rate']} m3/s

    Return ONLY a JSON object with this format (no markdown):
    {{
        "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
        "action": "monitor" | "prepare" | "evacuate",
        "reasoning": "brief explanation"
    }}
    """
    
    try:
        response_text = generate_with_llm(prompt, max_tokens=200)
        # cleanup response to ensure valid json
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(response_text)
        return result
    except Exception as e:
        print(f"LLM Analysis failed: {e}")
        return None

def generate_detailed_warning(participant: dict, region: dict, device: dict, prediction: dict, sensor_data: dict) -> str:
    """
    Use LLM to generate a detailed, context-aware flood warning email
    Includes: causes, risks, timeline, and specific recommendations
    """
    if not LLM_ENABLED or (_model is None and _gemini_model is None):
        # Fallback to enhanced template without LLM
        return generate_enhanced_email_fallback(participant, region, device, prediction, sensor_data)
    
    try:
        prompt = f"""You are the official Rainly Flood Warning System.
        Write a formal ALERT EMAIL to a resident named {participant.get('name', 'Resident')}.
        DO NOT roleplay as the resident. You are the SYSTEM sending the warning.
        
        SITUATION:
        - Location: {region.get('name', 'Unknown')}, {region.get('river_name', 'Unknown River')}, {region.get('state', 'India')}
        - Water Level: {sensor_data['water_level']:.2f}m (Threshold: {device['alert_threshold']:.1f}m)
        - Rainfall: {sensor_data.get('rainfall', 0):.0f}mm
        - Flow Rate: {sensor_data.get('flow_rate', 0):.0f} m³/s
        - Risk Level: {prediction['risk_level']}
        - Action Required: {prediction['warning_type'].upper()}

        Write a concise, urgent warning email (max 200 words).
        Structure:
        1. CURRENT STATUS: Brief summary of water levels.
        2. IMMEDIATE THREAT: What is happening now.
        3. REQUIRED ACTION: What the user must do (Evacuate/Prepare).
        4. SAFETY INSTRUCTIONS: 2-3 key safety tips.

        Tone: Urgent, Authoritative, Clear.
        Sign off as: Rainly Flood Control Room.
        
        Email Body:"""

        llm_content = generate_with_llm(prompt, max_tokens=400)
        
        # Wrap in HTML template
        color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(prediction['risk_level'], "#6b7280")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .llm-analysis {{ background: white; padding: 20px; border-left: 4px solid {color}; margin: 20px 0; white-space: pre-wrap; }}
                .sensor-data {{ background: #fff7ed; padding: 15px; border-radius: 6px; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 0.875rem; border-radius: 0 0 8px 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">URGENT FLOOD ALERT</h1>
                    <p style="margin: 5px 0 0 0; font-size: 1.125rem;">{prediction['risk_level']} RISK - {region['name']}</p>
                </div>
                
                <div class="content">
                    <p><strong>Dear {participant['name']},</strong></p>
                    
                    <div class="sensor-data">
                        <strong>Current Conditions ({region['river_name']}):</strong><br>
                        • Water Level: <strong>{sensor_data['water_level']:.2f}m</strong> (Threshold: {device['alert_threshold']:.1f}m)<br>
                        • Rainfall: {sensor_data.get('rainfall', 0):.0f}mm<br>
                        • Flow Rate: {sensor_data.get('flow_rate', 0):.0f} m³/s<br>
                        • Action Required: <strong style="color: {color};">{prediction['warning_type'].upper()}</strong>
                    </div>
                    
                    <div class="llm-analysis">
                        {llm_content}
                    </div>
                    
                    <div style="background: #fee2e2; padding: 15px; border-radius: 6px; margin-top: 20px;">
                        <strong style="color: #dc2626;">EMERGENCY CONTACTS:</strong><br>
                        • National Disaster Helpline: <strong>1078</strong><br>
                        • State Emergency: <strong>108</strong><br>
                        • Follow local authorities' instructions immediately
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Rainly - AI-Powered Flood Detection System</strong></p>
                    <p style="font-size: 0.75rem;">Powered by Local AI • Real-time sensor data</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
        
    except Exception as e:
        print(f"[ERROR] LLM warning generation failed: {e}")
        return generate_enhanced_email_fallback(participant, region, device, prediction, sensor_data)

def generate_enhanced_email_fallback(participant: dict, region: dict, device: dict, prediction: dict, sensor_data: dict) -> str:
    """
    Enhanced fallback email without LLM - includes detailed analysis
    This works perfectly without any LLM!
    """
    color = {"CRITICAL": "#dc2626", "HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(prediction['risk_level'], "#6b7280")
    
    # Analyze causes based on data
    causes = []
    if sensor_data.get('rainfall', 0) > 100:
        causes.append(f"Heavy rainfall ({sensor_data['rainfall']:.0f}mm) in the catchment area")
    if sensor_data['water_level'] > device['alert_threshold']:
        excess = sensor_data['water_level'] - device['alert_threshold']
        causes.append(f"Water level {excess:.1f}m above safe threshold")
    if sensor_data.get('flow_rate', 0) > 2000:
        causes.append(f"High river flow rate ({sensor_data['flow_rate']:.0f} m³/s)")
    
    causes_text = "<br>• ".join(causes) if causes else "Natural river water level variation"
    
    # Risk-specific content
    if prediction['risk_level'] in ['CRITICAL', 'HIGH']:
        timeline = "IMMEDIATE - Evacuate within 1-2 hours"
        risks = """
        • Life-threatening flooding possible
        • Property damage likely
        • Road closures and infrastructure damage
        • Risk of waterborne diseases
        • Power and water supply disruption
        """
        actions = """
        • Move to higher ground IMMEDIATELY
        • Take emergency supplies (water, food, medicine, documents)
        • Avoid walking/driving through floodwater
        • Stay away from electrical equipment
        • Keep phone charged and follow official updates
        """
    elif prediction['risk_level'] == 'MEDIUM':
        timeline = "4-6 hours - Monitor and prepare"
        risks = """
        • Potential flooding in low-lying areas
        • Possible property damage
        • Travel disruptions
        """
        actions = """
        • Prepare evacuation bag (documents, medicine, essentials)
        • Move valuables to higher floors
        • Stay informed via news/alerts
        • Avoid unnecessary travel
        • Keep emergency numbers handy
        """
    else:
        timeline = "24+ hours - Stay vigilant"
        risks = "Minor flooding possible in vulnerable areas"
        actions = """
        • Continue normal activities with caution
        • Monitor water levels
        • Stay updated via official channels
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; }}
            .section {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid {color}; }}
            .sensor-data {{ background: #fff7ed; padding: 15px; border-radius: 6px; margin: 15px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 0.875rem; border-radius: 0 0 8px 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">FLOOD WARNING</h1>
                <p style="margin: 5px 0 0 0; font-size: 1.125rem;">{prediction['risk_level']} RISK - {region['name']}</p>
            </div>
            
            <div class="content">
                <p><strong>Dear {participant['name']},</strong></p>
                
                <div class="sensor-data">
                    <strong>Current Conditions:</strong><br>
                    • Location: {region['name']}, {region['river_name']}, {region.get('state', 'India')}<br>
                    • Water Level: <strong>{sensor_data['water_level']:.2f}m</strong> (Safe limit: {device['alert_threshold']:.1f}m)<br>
                    • Rainfall: {sensor_data.get('rainfall', 0):.0f}mm<br>
                    • River Flow: {sensor_data.get('flow_rate', 0):.0f} m³/s
                </div>
                
                <div class="section">
                    <h3 style="margin-top: 0; color: {color};">CAUSES</h3>
                    • {causes_text}
                </div>
                
                <div class="section">
                    <h3 style="margin-top: 0; color: {color};">TIMELINE</h3>
                    <strong>{timeline}</strong>
                </div>
                
                <div class="section">
                    <h3 style="margin-top: 0; color: {color};">RISKS</h3>
                    {risks}
                </div>
                
                <div class="section">
                    <h3 style="margin-top: 0; color: {color};">ACTION REQUIRED</h3>
                    {actions}
                </div>
                
                <div style="background: #fee2e2; padding: 15px; border-radius: 6px; margin-top: 20px;">
                    <strong style="color: #dc2626;">EMERGENCY CONTACTS:</strong><br>
                    • National Disaster Helpline: <strong>1078</strong><br>
                    • State Emergency: <strong>108</strong><br>
                    • Police: <strong>100</strong> | Ambulance: <strong>102</strong>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Rainly - Real-Time Flood Detection System</strong></p>
                <p style="font-size: 0.75rem;">Automated alert based on live sensor data</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# Initialize LLM on module import (but only if enabled)
if LLM_ENABLED:
    initialize_llm()
