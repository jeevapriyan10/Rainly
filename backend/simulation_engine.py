"""
Real-Time Sensor Simulation Engine
Simulates live IoT sensor data streams until real devices are connected
"""
import asyncio
import random
from datetime import datetime
from typing import Dict, Optional
from models import SensorPayload
from predictor import predict_flood_risk
from llm_service import analyze_with_llm, LLM_ENABLED
from websocket_manager import manager

class SimulationEngine:
    def __init__(self):
        self.active_simulations: Dict[str, dict] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_simulation(self, device_id: str, region_id: str, config: dict, db):
        """
        Start real-time simulation for a device
        config: {
            'initial_water_level': float,
            'initial_rainfall': float,
            'initial_flow_rate': float,
            'alert_threshold': float,
            'variation_speed': str,  # 'slow', 'medium', 'fast'
            'trend': str  # 'rising', 'falling', 'stable', 'random'
        }
        """
        if device_id in self.running_tasks:
            # Stop existing simulation
            await self.stop_simulation(device_id)
        
        # Store config
        self.active_simulations[device_id] = config
        # Reset alert cooldown tracking
        if not hasattr(self, 'last_alert_times'):
            self.active_simulations[device_id]['last_alert_time'] = {}
        
        # Start simulation task
        task = asyncio.create_task(
            self._run_simulation(device_id, region_id, config, db)
        )
        self.running_tasks[device_id] = task
        
        print(f"[START] Started simulation for device: {device_id}")
        
        # Also simulate first payload immediately
        initial_payload = SensorPayload(
            sensor_id=device_id,
            region_id=region_id,
            water_level=config.get('initial_water_level', 280),
            rainfall=config.get('initial_rainfall', 20),
            flow_rate=config.get('initial_flow_rate', 800),
            timestamp=datetime.utcnow()
        )
        
        # Update DB immediately so frontend loads correct last seen values on refresh
        await db.devices.update_one(
            {"device_id": device_id},
            {"$set": {
                "last_water_level": initial_payload.water_level,
                "last_rainfall": initial_payload.rainfall,
                "last_flow_rate": initial_payload.flow_rate,
                "last_seen": initial_payload.timestamp
            }}
        )
        
        return {"status": "simulation_started", "device_id": device_id}
    
    async def stop_simulation(self, device_id: str):
        """Stop simulation for a device"""
        if device_id in self.running_tasks:
            self.running_tasks[device_id].cancel()
            del self.running_tasks[device_id]
            del self.active_simulations[device_id]
            print(f"[STOP] Stopped simulation for device: {device_id}")
            return {"status": "simulation_stopped", "device_id": device_id}
        return {"status": "no_active_simulation", "device_id": device_id}
    
    async def adjust_parameters(self, device_id: str, params: dict):
        """Adjust simulation parameters in real-time"""
        if device_id in self.active_simulations:
            self.active_simulations[device_id].update(params)
            
            # Broadcast immediate update
            await manager.broadcast_device_update(device_id, {
                'water_level': params.get('water_level', self.active_simulations[device_id]['current_water_level']),
                'rainfall': params.get('rainfall', self.active_simulations[device_id]['current_rainfall']),
                'flow_rate': params.get('flow_rate', self.active_simulations[device_id]['current_flow_rate'])
            })
            
            return {"status": "parameters_adjusted", "device_id": device_id}
        return {"status": "no_active_simulation", "device_id": device_id}
    
    def get_active_simulations(self) -> list:
        """Get list of all active simulations"""
        return list(self.active_simulations.keys())
    
    async def _run_simulation(self, device_id: str, region_id: str, config: dict, db):
        """Main simulation loop"""
        # Initialize current values
        current_water = config.get('initial_water_level', 280.0)
        current_rain = config.get('initial_rainfall', 20.0)
        current_flow = config.get('initial_flow_rate', 800.0)
        alert_threshold = config.get('alert_threshold', 294.5)
        
        speed_multiplier = {
            'slow': 0.3,
            'medium': 1.0,
            'fast': 2.0
        }.get(config.get('variation_speed', 'medium'), 1.0)
        
        trend = config.get('trend', 'random')
        
        # Update config with current values
        self.active_simulations[device_id]['current_water_level'] = current_water
        self.active_simulations[device_id]['current_rainfall'] = current_rain
        self.active_simulations[device_id]['current_flow_rate'] = current_flow
        
        update_interval = 5  # seconds
        
        try:
            while True:
                device_check = await db.devices.find_one({"device_id": device_id})
                if not device_check or not device_check.get("is_active", True):
                    print(f"[STOP] Device {device_id} is inactive. Stopping simulation.")
                    await manager.broadcast_device_update(device_id, {
                        'status': 'stopped',
                        'message': 'Device is inactive'
                    })
                    # We need to clean up self.active_simulations and tasks
                    # But we can't call stop_simulation directly easily because it cancels the task we are running in!
                    # So we just break the loop and let the cleanup happen or handle it gracefully.
                    # Best way: Just break, and remove from active_simulations manually here.
                    if device_id in self.active_simulations:
                        del self.active_simulations[device_id]
                    if device_id in self.running_tasks:
                        # Don't cancel self, just remove validation key
                        del self.running_tasks[device_id]
                    break

                # Calculate changes based on trend
                if trend == 'rising':
                    water_delta = random.uniform(0.5, 2.0) * speed_multiplier
                    rain_delta = random.uniform(2, 10) * speed_multiplier
                elif trend == 'falling':
                    water_delta = random.uniform(-2.0, -0.5) * speed_multiplier
                    rain_delta = random.uniform(-10, -2) * speed_multiplier
                elif trend == 'stable':
                    water_delta = random.uniform(-0.3, 0.3) * speed_multiplier
                    rain_delta = random.uniform(-5, 5) * speed_multiplier
                else:  # random
                    water_delta = random.uniform(-1.5, 2.5) * speed_multiplier
                    rain_delta = random.uniform(-8, 12) * speed_multiplier
                
                # Update values
                current_water += water_delta
                current_rain = max(0, current_rain + rain_delta)
                current_flow = current_water * 10 + random.uniform(-50, 50)  # Approximation
                
                # Keep realistic bounds
                current_water = max(250, min(350, current_water))
                current_rain = max(0, min(300, current_rain))
                current_flow = max(0, min(5000, current_flow))
                
                # Update config
                self.active_simulations[device_id]['current_water_level'] = current_water
                self.active_simulations[device_id]['current_rainfall'] = current_rain
                self.active_simulations[device_id]['current_flow_rate'] = current_flow
                
                # Create sensor payload
                payload = SensorPayload(
                    sensor_id=device_id,
                    region_id=region_id,
                    water_level=current_water,
                    rainfall=current_rain,
                    flow_rate=current_flow,
                    timestamp=datetime.utcnow()
                )
                
                # Predict flood risk
                prediction = predict_flood_risk(payload, alert_threshold)
                
                # Update device in database
                await db.devices.update_one(
                    {"device_id": device_id},
                    {
                        "$set": {
                            "last_water_level": current_water,
                            "last_rainfall": current_rain,
                            "last_flow_rate": current_flow,
                            "last_seen": datetime.utcnow()
                        }
                    }
                )
                
                # Update region risk level
                await db.regions.update_one(
                    {"region_id": region_id},
                    {"$set": {"risk_level": prediction.risk_level}}
                )
                
                # LLM Analysis (if enabled and high risk or periodic)
                # For local models, we want to be careful not to spam it every 5 seconds
                # So we only run it:
                # 1. If risk is HIGH/CRITICAL (every time? maybe too slow. Let's do every 3rd time or so? No, user wants it.)
                # 2. Or randomly 10% of the time for other states.
                
                # Use cached reasoning if we don't run LLM this turn
                current_reasoning = self.active_simulations[device_id].get('last_reasoning')

                if LLM_ENABLED:
                    # Basic throttling: only if risk changed or random chance
                    should_run_llm = False
                    if prediction.risk_level in ['HIGH', 'CRITICAL']:
                        should_run_llm = True
                    elif random.random() < 0.1:
                        should_run_llm = True
                    
                    if should_run_llm:
                        sensor_data_for_llm = {
                            'water_level': current_water,
                            'rainfall': current_rain,
                            'flow_rate': current_flow,
                            'threshold': alert_threshold
                        }
                        # Run in executor to avoid blocking main loop if it's slow
                        # formatting
                        try:
                            llm_result = await asyncio.to_thread(analyze_with_llm, sensor_data_for_llm)
                            if llm_result:
                                reasoning_text = llm_result.get('reasoning')
                                # Add emoji to show it's working
                                current_reasoning = f"(Live) {reasoning_text}"
                                self.active_simulations[device_id]['last_reasoning'] = current_reasoning
                        except Exception as e:
                            print(f"LLM analysis error: {e}")
                
                # Broadcast update to all clients
                update_data = {
                    'water_level': round(current_water, 2),
                    'rainfall': round(current_rain, 1),
                    'flow_rate': round(current_flow, 1),
                    'risk_level': prediction.risk_level,
                    'risk_score': round(prediction.risk_score, 2),
                    'alert_threshold': alert_threshold
                }
                
                if current_reasoning:
                    update_data['llm_reasoning'] = current_reasoning
                
                await manager.broadcast_device_update(device_id, update_data)
                
                # Generate warning if CRITICAL risk (with cooldown)
                # Only send emails for CRITICAL
                if prediction.risk_level == 'CRITICAL':
                    # Fetch region info
                    region = await db.regions.find_one({"region_id": region_id}, {"_id": 0})
                    
                    # Fetch device info
                    device_doc = await db.devices.find_one({"device_id": device_id}, {"_id": 0})
                    
                    # Fetch participants in region
                    participants = await db.participants.find(
                        {"region_id": region_id},
                        {"_id": 0}
                    ).to_list(100)
                    
                    if participants:
                        # Import notification service
                        from notify import send_flood_alert
                        
                        # Initialize alert tracking for this device if needed
                        if 'last_alert_time' not in self.active_simulations[device_id]:
                             self.active_simulations[device_id]['last_alert_time'] = {}
                        
                        # Create warnings and send emails for each participant
                        for participant in participants:
                            
                            # Check cooldown (30 mins = 1800 seconds)
                            p_id = participant['participant_id']
                            last_sent = self.active_simulations[device_id]['last_alert_time'].get(p_id)
                            current_time = datetime.utcnow()
                            
                            if last_sent and (current_time - last_sent).total_seconds() < 1800:
                                # Skip if sent less than 30 mins ago
                                continue
                            
                            warning = {
                                "warning_id": f"w_{datetime.utcnow().timestamp()}_{participant['participant_id']}",
                                "region_id": region_id,
                                "device_id": device_id,
                                "river_name": region.get('river_name', 'Unknown'),
                                "participant_id": participant['participant_id'],
                                "warning_type": prediction.warning_type,
                                "risk_level": prediction.risk_level,
                                "timestamp": datetime.utcnow(),
                                "water_level": current_water,
                                "rainfall": current_rain,
                                "flow_rate": current_flow
                            }
                            
                            await db.warnings.insert_one(warning)
                            
                            # Send automatic email/SMS notification
                            try:
                                sensor_data = {
                                    'water_level': current_water,
                                    'rainfall': current_rain,
                                    'flow_rate': current_flow
                                }
                                
                                pred_dict = {
                                    'risk_level': prediction.risk_level,
                                    'warning_type': prediction.warning_type
                                }
                                
                                result = await send_flood_alert(
                                    participant=participant,
                                    region=region,
                                    device=device_doc,
                                    prediction=pred_dict,
                                    sensor_data=sensor_data
                                )
                                
                                # Update last sent time
                                self.active_simulations[device_id]['last_alert_time'][p_id] = current_time
                                
                                print(f"[EMAIL] Alert sent to {participant['name']}: SMS={result.get('sms', {}).get('status')}, Email={result.get('email', {}).get('status')}")
                            except Exception as e:
                                print(f"[WARN] Failed to send alert to {participant['name']}: {e}")
                        
                        # Broadcast warning alert (UI)
                        await manager.broadcast_alert({
                            'region': region.get('name', 'Unknown'),
                            'river': region.get('river_name', 'Unknown'),
                            'risk_level': prediction.risk_level,
                            'water_level': current_water,
                            'threshold': alert_threshold,
                            'participants_notified': len(participants)
                        })
                
                # Wait before next update
                await asyncio.sleep(update_interval)
                
        except asyncio.CancelledError:
            print(f"[STOP] Simulation cancelled for device: {device_id}")
        except Exception as e:
            print(f"[ERROR] Error in simulation for {device_id}: {e}")

# Global simulation engine instance
engine = SimulationEngine()
