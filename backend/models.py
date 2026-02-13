from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Region(BaseModel):
    region_id: str
    name: str
    latitude: float
    longitude: float
    river_name: str
    state: Optional[str] = None
    district: Optional[str] = None
    risk_level: Optional[str] = "LOW"  # LOW, MEDIUM, HIGH

class Device(BaseModel):
    device_id: str
    region_id: str
    name: str
    alert_threshold: float
    is_active: bool = True
    last_water_level: Optional[float] = None
    last_rainfall: Optional[float] = None
    last_flow_rate: Optional[float] = None
    battery_level: Optional[int] = None  # 0-100
    last_seen: Optional[datetime] = None

class Participant(BaseModel):
    participant_id: Optional[str] = None
    name: str
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    region_id: str

class Warning(BaseModel):
    warning_id: Optional[str] = None
    region_id: str
    device_id: str
    river_name: str
    participant_id: str
    warning_type: str
    risk_level: str
    timestamp: datetime
    water_level: float
    rainfall: float
    flow_rate: float

class SensorPayload(BaseModel):
    sensor_id: str
    region_id: str
    water_level: float
    rainfall: float
    flow_rate: float
    timestamp: Optional[datetime] = None

class PredictionResult(BaseModel):
    risk_level: str
    warning_type: str
    risk_score: float
