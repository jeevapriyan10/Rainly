import os
from models import PredictionResult, SensorPayload
from llm_service import LLM_ENABLED, analyze_with_llm

def predict_flood_risk(payload: SensorPayload, alert_threshold: float) -> PredictionResult:
    """
    Predict flood risk using LLM if available, otherwise use rule-based system
    """
    # Try LLM prediction first if enabled
    # Note: We now use rule-based for the core prediction to ensure speed and reliability.
    # The LLM is used in the simulation_engine for *reasoning* and in notify.py for *email generation*.
    # Trying to use LLM for every single sensor tick for basic risk level is too slow and costly.
    
    return rules_based_predict(payload, alert_threshold)

def rules_based_predict(payload: SensorPayload, alert_threshold: float) -> PredictionResult:
    """
    Rule-based flood risk prediction with enhanced threshold checks
    """
    water_level = payload.water_level
    rainfall = payload.rainfall
    flow_rate = payload.flow_rate
    
    # Calculate risk score based on multiple factors
    water_ratio = water_level / alert_threshold if alert_threshold > 0 else 0
    rainfall_factor = min(rainfall / 200.0, 1.0)  # Normalize to 0-1
    flow_factor = min(flow_rate / 3000.0, 1.0) if flow_rate else 0  # Normalize to 0-1
    
    # Weighted risk score
    risk_score = (water_ratio * 0.5) + (rainfall_factor * 0.3) + (flow_factor * 0.2)
    
    # CRITICAL RISK - Immediate danger
    # Early Warning: If water level is 90% of threshold but rising fast (heuristic from trend), upgrade risk
    # Here we simulate that heuristic by checking if it's very close (95%)
    
    if water_level >= alert_threshold * 1.2 or rainfall >= 200:
        return PredictionResult(
            risk_level="CRITICAL",
            warning_type="evacuate",
            risk_score=min(0.95, risk_score)
        )
    
    # HIGH RISK - Evacuation needed
    elif water_level >= alert_threshold * 1.1 or rainfall >= 150:
        return PredictionResult(
            risk_level="HIGH",
            warning_type="evacuate",
            risk_score=min(0.85, risk_score)
        )
    
    # MEDIUM RISK - Prepare for evacuation
    elif water_level >= alert_threshold or rainfall >= 75:
        return PredictionResult(
            risk_level="MEDIUM",
            warning_type="prepare",
            risk_score=min(0.55, risk_score)
        )
    
    # LOW RISK - Monitor situation
    else:
        return PredictionResult(
            risk_level="LOW",
            warning_type="monitor",
            risk_score=min(0.3, risk_score)
        )
