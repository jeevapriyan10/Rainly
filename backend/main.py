from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List
import uuid
import os

from db import connect_db, close_db, get_db
from models import Region, Device, Participant, Warning, SensorPayload
from predictor import predict_flood_risk
from notify import send_notification, send_flood_alert
from download_model import download_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    
    # Auto-seed if empty
    db = get_db()
    if await db.regions.count_documents({}) == 0:
        print("[INIT] Database empty. Seeding initial data...")
        await seed_database()
        print("[SUCCESS] Database seeded!")
    
    # Check for LLM Model (if local provider)
    if os.getenv("LLM_PROVIDER", "google") == "local":
        print("[INIT] Checking for local LLM model...")
        model_file = os.getenv("LLM_MODEL_FILE", "qwen2-0_5b-instruct-q4_k_m.gguf")
        
        # Ensure directory exists relative to current file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "models", "llm", model_file)
        
        if not os.path.exists(model_path):
             print(f"[INFO] Model not found at {model_path}. Downloading...")
             
             # Determine model key based on filename
             model_key = "qwen"
             if "tinyllama" in model_file.lower():
                 model_key = "tinyllama"
             elif "phi" in model_file.lower():
                 model_key = "phi2"
                 
             # Call download function
             print(f"[INFO] Starting download for {model_key}...")
             download_model(model_key)
        else:
            print("[SUCCESS] Local LLM model found.")
    yield
    await close_db()

app = FastAPI(title="Early Flood Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === REGIONS ===
@app.get("/api/regions", response_model=List[Region])
async def get_regions():
    db = get_db()
    regions = await db.regions.find({}, {"_id": 0}).to_list(1000)
    return regions

@app.post("/api/regions", response_model=Region)
async def create_region(region: Region):
    db = get_db()
    await db.regions.insert_one(region.dict())
    return region

# === DEVICES ===
@app.get("/api/devices", response_model=List[Device])
async def get_devices():
    db = get_db()
    devices = await db.devices.find({}, {"_id": 0}).to_list(1000)
    return devices

@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device(device_id: str):
    db = get_db()
    device = await db.devices.find_one({"device_id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@app.post("/api/devices", response_model=Device)
async def create_device(device: Device):
    db = get_db()
    await db.devices.insert_one(device.dict())
    return device

@app.put("/api/devices/{device_id}/toggle")
async def toggle_device(device_id: str):
    db = get_db()
    device = await db.devices.find_one({"device_id": device_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    new_status = not device["is_active"]
    await db.devices.update_one({"device_id": device_id}, {"$set": {"is_active": new_status}})
    return {"device_id": device_id, "is_active": new_status}

# === PARTICIPANTS ===
@app.get("/api/participants", response_model=List[Participant])
async def get_participants():
    db = get_db()
    participants = await db.participants.find({}, {"_id": 0}).to_list(1000)
    return participants

@app.post("/api/participants", response_model=Participant)
async def create_participant(participant: Participant):
    db = get_db()
    participant.participant_id = str(uuid.uuid4())
    await db.participants.insert_one(participant.dict())
    return participant

# === WARNINGS ===
@app.get("/api/warnings", response_model=List[Warning])
async def get_warnings():
    db = get_db()
    warnings = await db.warnings.find({}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    return warnings

@app.get("/api/warnings/participant/{participant_id}", response_model=List[Warning])
async def get_participant_warnings(participant_id: str):
    db = get_db()
    warnings = await db.warnings.find({"participant_id": participant_id}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    return warnings

# === SIMULATOR (IoT Payload Processing) ===
@app.post("/api/simulate")
async def simulate_iot_payload(payload: SensorPayload):
    """
    Receive simulated IoT sensor data, analyze with predictor, generate warnings for all participants in region
    """
    db = get_db()
    
    # Set timestamp if not provided
    if not payload.timestamp:
        payload.timestamp = datetime.utcnow()
    
    # Get device info
    device = await db.devices.find_one({"device_id": payload.sensor_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update device last seen and sensor values
    await db.devices.update_one(
        {"device_id": payload.sensor_id},
        {"$set": {
            "last_water_level": payload.water_level,
            "last_rainfall": payload.rainfall,
            "last_flow_rate": payload.flow_rate,
            "last_seen": payload.timestamp
        }}
    )
    
    # Predict flood risk
    prediction = predict_flood_risk(payload, device["alert_threshold"])
    
    # Get region info
    region = await db.regions.find_one({"region_id": payload.region_id})
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Get all participants in this region
    participants = await db.participants.find({"region_id": payload.region_id}).to_list(1000)
    
    warnings_generated = []
    
    # Generate warnings for each participant
    for participant in participants:
        warning = Warning(
            warning_id=str(uuid.uuid4()),
            region_id=payload.region_id,
            device_id=payload.sensor_id,
            river_name=region["river_name"],
            participant_id=participant["participant_id"],
            warning_type=prediction.warning_type,
            risk_level=prediction.risk_level,
            timestamp=payload.timestamp,
            water_level=payload.water_level,
            rainfall=payload.rainfall,
            flow_rate=payload.flow_rate
        )
        
        # Store warning in DB
        await db.warnings.insert_one(warning.dict())
        warnings_generated.append(warning)
        
        # Send notification (Email + SMS)
        sensor_data = {
            'water_level': payload.water_level,
            'rainfall': payload.rainfall,
            'flow_rate': payload.flow_rate
        }
        pred_dict = {
            'risk_level': prediction.risk_level,
            'warning_type': prediction.warning_type
        }
        
        try:
            await send_flood_alert(
                participant=participant,
                region=region,
                device=device,
                prediction=pred_dict,
                sensor_data=sensor_data
            )
        except Exception as e:
            print(f"[ERROR] Failed to send manual alert: {e}")
    
    return {
        "status": "success",
        "prediction": prediction.dict(),
        "warnings_generated": len(warnings_generated),
        "affected_participants": len(participants)
    }

# === ANALYTICS ===
@app.get("/api/analytics")
async def get_analytics():
    db = get_db()
    
    total_devices = await db.devices.count_documents({})
    active_devices = await db.devices.count_documents({"is_active": True})
    devices_in_warning = await db.devices.count_documents({
        "last_water_level": {"$gte": 5.0}  # Simple heuristic
    })
    
    # Fetch warnings and exclude _id field
    recent_warnings_raw = await db.warnings.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    
    return {
        "total_devices": total_devices,
        "active_devices": active_devices,
        "devices_in_warning": devices_in_warning,
        "recent_warnings": recent_warnings_raw
    }

# === SEED DATA ===
@app.post("/api/seed")
async def seed_database():
    """
    Seed database with comprehensive mock data for Indian rivers
    """
    db = get_db()
    
    # Clear existing data
    await db.regions.delete_many({})
    await db.devices.delete_many({})
    await db.participants.delete_many({})
    await db.warnings.delete_many({})
    
    # Seed regions with major Indian rivers
    regions = [
        # Ganges Basin
        {
            "region_id": "r001",
            "name": "Haridwar Region",
            "latitude": 29.9457,
            "longitude": 78.1642,
            "river_name": "Ganges",
            "state": "Uttarakhand",
            "district": "Haridwar",
            "risk_level": "MEDIUM"
        },
        {
            "region_id": "r002",
            "name": "Varanasi Region",
            "latitude": 25.3176,
            "longitude": 82.9739,
            "river_name": "Ganges",
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "risk_level": "LOW"
        },
        {
            "region_id": "r003",
            "name": "Patna Region",
            "latitude": 25.5941,
            "longitude": 85.1376,
            "river_name": "Ganges",
            "state": "Bihar",
            "district": "Patna",
            "risk_level": "HIGH"
        },
        # Yamuna Basin
        {
            "region_id": "r004",
            "name": "Delhi Region",
            "latitude": 28.7041,
            "longitude": 77.1025,
            "river_name": "Yamuna",
            "state": "Delhi",
            "district": "New Delhi",
            "risk_level": "MEDIUM"
        },
        {
            "region_id": "r005",
            "name": "Agra Region",
            "latitude": 27.1767,
            "longitude": 78.0081,
            "river_name": "Yamuna",
            "state": "Uttar Pradesh",
            "district": "Agra",
            "risk_level": "LOW"
        },
        # Brahmaputra Basin
        {
            "region_id": "r006",
            "name": "Guwahati Region",
            "latitude": 26.1445,
            "longitude": 91.7362,
            "river_name": "Brahmaputra",
            "state": "Assam",
            "district": "Kamrup",
            "risk_level": "HIGH"
        },
        # Godavari Basin
        {
            "region_id": "r007",
            "name": "Nashik Region",
            "latitude": 19.9975,
            "longitude": 73.7898,
            "river_name": "Godavari",
            "state": "Maharashtra",
            "district": "Nashik",
            "risk_level": "MEDIUM"
        },
        # Krishna Basin
        {
            "region_id": "r008",
            "name": "Vijayawada Region",
            "latitude": 16.5062,
            "longitude": 80.6480,
            "river_name": "Krishna",
            "state": "Andhra Pradesh",
            "district": "Krishna",
            "risk_level": "MEDIUM"
        },
        # Narmada Basin
        {
            "region_id": "r009",
            "name": "Jabalpur Region",
            "latitude": 23.1815,
            "longitude": 79.9864,
            "river_name": "Narmada",
            "state": "Madhya Pradesh",
            "district": "Jabalpur",
            "risk_level": "LOW"
        },
        # Mahanadi Basin
        {
            "region_id": "r010",
            "name": "Cuttack Region",
            "latitude": 20.4625,
            "longitude": 85.8830,
            "river_name": "Mahanadi",
            "state": "Odisha",
            "district": "Cuttack",
            "risk_level": "HIGH"
        }
    ]
    await db.regions.insert_many(regions)
    
    # Seed devices for each region
    devices = [
        # Haridwar - Ganges
        {
            "device_id": "d001",
            "region_id": "r001",
            "name": "Har Ki Pauri Sensor",
            "alert_threshold": 294.5,
            "is_active": True,
            "last_water_level": 296.2,
            "last_rainfall": 45.0,
            "last_flow_rate": 1200.0,
            "battery_level": 85,
            "last_seen": datetime.utcnow()
        },
        {
            "device_id": "d002",
            "region_id": "r001",
            "name": "Bhimgoda Barrage Monitor",
            "alert_threshold": 298.0,
            "is_active": True,
            "last_water_level": 295.5,
            "last_rainfall": 42.0,
            "last_flow_rate": 1150.0,
            "battery_level": 92,
            "last_seen": datetime.utcnow()
        },
        # Varanasi - Ganges
        {
            "device_id": "d003",
            "region_id": "r002",
            "name": "Assi Ghat Station",
            "alert_threshold": 62.5,
            "is_active": True,
            "last_water_level": 60.2,
            "last_rainfall": 25.0,
            "last_flow_rate": 950.0,
            "battery_level": 78,
            "last_seen": datetime.utcnow()
        },
        {
            "device_id": "d004",
            "region_id": "r002",
            "name": "Dashashwamedh Sensor",
            "alert_threshold": 63.0,
            "is_active": True,
            "last_water_level": 61.8,
            "last_rainfall": 28.0,
            "last_flow_rate": 980.0,
            "battery_level": 88,
            "last_seen": datetime.utcnow()
        },
        # Patna - Ganges
        {
            "device_id": "d005",
            "region_id": "r003",
            "name": "Gandhi Ghat Monitor",
            "alert_threshold": 45.0,
            "is_active": True,
            "last_water_level": 47.5,
            "last_rainfall": 95.0,
            "last_flow_rate": 1850.0,
            "battery_level": 65,
            "last_seen": datetime.utcnow()
        },
        {
            "device_id": "d006",
            "region_id": "r003",
            "name": "Patna Bridge Sensor",
            "alert_threshold": 46.0,
            "is_active": False,
            "last_water_level": None,
            "last_rainfall": None,
            "last_flow_rate": None,
            "battery_level": 12,
            "last_seen": None
        },
        # Delhi - Yamuna
        {
            "device_id": "d007",
            "region_id": "r004",
            "name": "ITO Bridge Station",
            "alert_threshold": 204.5,
            "is_active": True,
            "last_water_level": 206.8,
            "last_rainfall": 55.0,
            "last_flow_rate": 650.0,
            "battery_level": 75,
            "last_seen": datetime.utcnow()
        },
        {
            "device_id": "d008",
            "region_id": "r004",
            "name": "Wazirabad Barrage Sensor",
            "alert_threshold": 203.0,
            "is_active": True,
            "last_water_level": 205.2,
            "last_rainfall": 52.0,
            "last_flow_rate": 620.0,
            "battery_level": 82,
            "last_seen": datetime.utcnow()
        },
        # Agra - Yamuna
        {
            "device_id": "d009",
            "region_id": "r005",
            "name": "Taj Yamuna Monitor",
            "alert_threshold": 151.5,
            "is_active": True,
            "last_water_level": 149.2,
            "last_rainfall": 18.0,
            "last_flow_rate": 420.0,
            "battery_level": 90,
            "last_seen": datetime.utcnow()
        },
        # Guwahati - Brahmaputra
        {
            "device_id": "d010",
            "region_id": "r006",
            "name": "Panbazar Station",
            "alert_threshold": 50.5,
            "is_active": True,
            "last_water_level": 52.8,
            "last_rainfall": 145.0,
            "last_flow_rate": 3200.0,
            "battery_level": 70,
            "last_seen": datetime.utcnow()
        },
        {
            "device_id": "d011",
            "region_id": "r006",
            "name": "Saraighat Bridge Sensor",
            "alert_threshold": 51.0,
            "is_active": True,
            "last_water_level": 53.2,
            "last_rainfall": 150.0,
            "last_flow_rate": 3350.0,
            "battery_level": 68,
            "last_seen": datetime.utcnow()
        },
        # Nashik - Godavari
        {
            "device_id": "d012",
            "region_id": "r007",
            "name": "Ramkund Monitor",
            "alert_threshold": 565.0,
            "is_active": True,
            "last_water_level": 566.5,
            "last_rainfall": 65.0,
            "last_flow_rate": 850.0,
            "battery_level": 85,
            "last_seen": datetime.utcnow()
        },
        # Vijayawada - Krishna
        {
            "device_id": "d013",
            "region_id": "r008",
            "name": "Prakasam Barrage Station",
            "alert_threshold": 22.5,
            "is_active": True,
            "last_water_level": 23.8,
            "last_rainfall": 72.0,
            "last_flow_rate": 1150.0,
            "battery_level": 77,
            "last_seen": datetime.utcnow()
        },
        # Jabalpur - Narmada
        {
            "device_id": "d014",
            "region_id": "r009",
            "name": "Marble Rocks Sensor",
            "alert_threshold": 412.0,
            "is_active": True,
            "last_water_level": 408.5,
            "last_rainfall": 32.0,
            "last_flow_rate": 720.0,
            "battery_level": 95,
            "last_seen": datetime.utcnow()
        },
        # Cuttack - Mahanadi
        {
            "device_id": "d015",
            "region_id": "r010",
            "name": "Naraj Barrage Monitor",
            "alert_threshold": 25.8,
            "is_active": True,
            "last_water_level": 27.5,
            "last_rainfall": 125.0,
            "last_flow_rate": 2100.0,
            "battery_level": 62,
            "last_seen": datetime.utcnow()
        }
    ]
    await db.devices.insert_many(devices)
    
    # Seed participants across different regions
    participants = [
        {"participant_id": "p001", "name": "Rajesh Kumar", "age": 35, "phone": "+911234567890", "email": "yo.heisenberg10@gmail.com", "region_id": "r001"},
        {"participant_id": "p002", "name": "Priya Sharma", "age": 28, "phone": "+911234567891", "email": "yo.heisenberg10@gmail.com", "region_id": "r001"},
        {"participant_id": "p003", "name": "Amit Patel", "age": 42, "phone": "+911234567892", "email": "yo.heisenberg10@gmail.com", "region_id": "r003"},
        {"participant_id": "p004", "name": "Sunita Verma", "age": 31, "phone": "+911234567893", "email": "yo.heisenberg10@gmail.com", "region_id": "r003"},
        {"participant_id": "p005", "name": "Vikram Singh", "age": 45, "phone": "+911234567894", "email": "yo.heisenberg10@gmail.com", "region_id": "r004"},
        {"participant_id": "p006", "name": "Ananya Das", "age": 29, "phone": "+911234567895", "email": "yo.heisenberg10@gmail.com", "region_id": "r006"},
        {"participant_id": "p007", "name": "Mohammed Khan", "age": 38, "phone": "+911234567896", "email": "yo.heisenberg10@gmail.com", "region_id": "r006"},
        {"participant_id": "p008", "name": "Lakshmi Reddy", "age": 52, "phone": "+911234567897", "email": "yo.heisenberg10@gmail.com", "region_id": "r008"},
    ]
    await db.participants.insert_many(participants)
    
    # Seed warnings
    warnings = [
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r001",
            "device_id": "d001",
            "river_name": "Ganges",
            "participant_id": "p001",
            "warning_type": "prepare",
            "risk_level": "MEDIUM",
            "timestamp": datetime.utcnow(),
            "water_level": 296.2,
            "rainfall": 45.0,
            "flow_rate": 1200.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r001",
            "device_id": "d001",
            "river_name": "Ganges",
            "participant_id": "p002",
            "warning_type": "prepare",
            "risk_level": "MEDIUM",
            "timestamp": datetime.utcnow(),
            "water_level": 296.2,
            "rainfall": 45.0,
            "flow_rate": 1200.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r003",
            "device_id": "d005",
            "river_name": "Ganges",
            "participant_id": "p003",
            "warning_type": "evacuate",
            "risk_level": "HIGH",
            "timestamp": datetime.utcnow(),
            "water_level": 47.5,
            "rainfall": 95.0,
            "flow_rate": 1850.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r003",
            "device_id": "d005",
            "river_name": "Ganges",
            "participant_id": "p004",
            "warning_type": "evacuate",
            "risk_level": "HIGH",
            "timestamp": datetime.utcnow(),
            "water_level": 47.5,
            "rainfall": 95.0,
            "flow_rate": 1850.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r004",
            "device_id": "d007",
            "river_name": "Yamuna",
            "participant_id": "p005",
            "warning_type": "prepare",
            "risk_level": "MEDIUM",
            "timestamp": datetime.utcnow(),
            "water_level": 206.8,
            "rainfall": 55.0,
            "flow_rate": 650.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r006",
            "device_id": "d010",
            "river_name": "Brahmaputra",
            "participant_id": "p006",
            "warning_type": "evacuate",
            "risk_level": "HIGH",
            "timestamp": datetime.utcnow(),
            "water_level": 52.8,
            "rainfall": 145.0,
            "flow_rate": 3200.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r006",
            "device_id": "d011",
            "river_name": "Brahmaputra",
            "participant_id": "p007",
            "warning_type": "evacuate",
            "risk_level": "HIGH",
            "timestamp": datetime.utcnow(),
            "water_level": 53.2,
            "rainfall": 150.0,
            "flow_rate": 3350.0
        },
        {
            "warning_id": str(uuid.uuid4()),
            "region_id": "r008",
            "device_id": "d013",
            "river_name": "Krishna",
            "participant_id": "p008",
            "warning_type": "prepare",
            "risk_level": "MEDIUM",
            "timestamp": datetime.utcnow(),
            "water_level": 23.8,
            "rainfall": 72.0,
            "flow_rate": 1150.0
        }
    ]
    await db.warnings.insert_many(warnings)
    
    return {
        "status": "success",
        "message": "Database seeded with comprehensive Indian river data",
        "counts": {
            "regions": len(regions),
            "devices": len(devices),
            "participants": len(participants),
            "warnings": len(warnings)
        }
    }

@app.get("/")
async def root():
    return {"message": "Rainly - Early Flood Detection API", "status": "running"}

# === WEBSOCKET FOR REAL-TIME UPDATES ===
from fastapi import WebSocket, WebSocketDisconnect
from websocket_manager import manager
from simulation_engine import engine

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get('type') == 'ping':
                await manager.send_personal_message(
                    {'type': 'pong', 'timestamp': datetime.utcnow().isoformat()},
                    websocket
                )
            elif data.get('type') == 'get_status':
                active_sims = engine.get_active_simulations()
                await manager.send_personal_message({
                    'type': 'status',
                    'active_simulations': active_sims,
                    'total_connections': len(manager.active_connections)
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# === REAL-TIME SIMULATION APIs ===
@app.post("/api/simulation/start")
async def start_simulation(device_id: str, config: dict):
    """
    Start real-time simulation for a device
    Body: {
        "device_id": "d001",
        "config": {
            "initial_water_level": 290.0,
            "initial_rainfall": 30.0,
            "initial_flow_rate": 1000.0,
            "variation_speed": "medium",  // slow, medium, fast
            "trend": "rising"  // rising, falling, stable, random
        }
    }
    """
    db = get_db()
    
    # Get device info
    device = await db.devices.find_one({"device_id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    result = await engine.start_simulation(
        device_id=device_id,
        region_id=device['region_id'],
        config={
            **config,
            'alert_threshold': device['alert_threshold']
        },
        db=db
    )
    
    return result

@app.post("/api/simulation/stop/{device_id}")
async def stop_simulation(device_id: str):
    """Stop simulation for a device"""
    result = await engine.stop_simulation(device_id)
    return result

@app.post("/api/simulation/adjust/{device_id}")
async def adjust_simulation(device_id: str, params: dict):
    """
    Adjust simulation parameters in real-time
    Body: {
        "water_level": 295.0,  // optional
        "rainfall": 85.0,      // optional
        "flow_rate": 1500.0,    // optional
        "trend": "rising"      // optional
    }
    """
    result = await engine.adjust_parameters(device_id, params)
    return result

@app.get("/api/simulation/active")
async def get_active_simulations():
    """Get list of all active simulations"""
    active = engine.get_active_simulations()
    return {
        "active_simulations": active,
        "count": len(active)
    }

# === MANUAL SIMULATE (Original one-time simulation) ===
# Endpoint merged with /api/simulate above

# End of file
