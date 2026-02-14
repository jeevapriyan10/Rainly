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
        self.active_simulations[device_id]['llm_status'] = 'idle'
        
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
            if device_id in self.active_simulations:
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
                'water_level': params.get('water_level', self.active_simulations[device_id].get('current_water_level')),
                'rainfall': params.get('rainfall', self.active_simulations[device_id].get('current_rainfall')),
                'flow_rate': params.get('flow_rate', self.active_simulations[device_id].get('current_flow_rate'))
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
        
        update_interval = 2  # seconds (faster updates)
        
        try:
            while True:
                # Check directly from DB if device is still active (allows external stop)
                device_check = await db.devices.find_one({"device_id": device_id})
                if not device_check or not device_check.get("is_active", True):
                    print(f"[STOP] Device {device_id} is inactive. Stopping simulation.")
                    await manager.broadcast_device_update(device_id, {
                        'status': 'stopped',
                        'message': 'Device is inactive'
                    })
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
                if device_id in self.active_simulations:
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
                
                # Update device in database (Non-blocking)
                asyncio.create_task(db.devices.update_one(
                    {"device_id": device_id},
                    {
                        "$set": {
                            "last_water_level": current_water,
                            "last_rainfall": current_rain,
                            "last_flow_rate": current_flow,
                            "last_seen": datetime.utcnow()
                        }
                    }
                ))
                
                asyncio.create_task(db.regions.update_one(
                    {"region_id": region_id},
                    {"$set": {"risk_level": prediction.risk_level}}
                ))
                
                # --- LLM ANALYSIS ---
                if LLM_ENABLED and device_id in self.active_simulations:
                    llm_status = self.active_simulations[device_id].get('llm_status', 'idle')
                    
                    if llm_status != 'processing':
                        should_run_llm = False
                        if prediction.risk_level in ['HIGH', 'CRITICAL']:
                            should_run_llm = True
                        elif random.random() < 0.05: # Reduced chance for normal monitoring
                            should_run_llm = True
                        
                        if should_run_llm:
                            sensor_data_for_llm = {
                                'water_level': current_water,
                                'rainfall': current_rain,
                                'flow_rate': current_flow,
                                'threshold': alert_threshold
                            }
                            # FIRE BACKGROUND TASK
                            asyncio.create_task(self._process_llm_analysis(device_id, sensor_data_for_llm))

                # --- BROADCAST UPDATE ---
                update_data = {
                    'water_level': round(current_water, 2),
                    'rainfall': round(current_rain, 1),
                    'flow_rate': round(current_flow, 1),
                    'risk_level': prediction.risk_level,
                    'risk_score': round(prediction.risk_score, 2),
                    'alert_threshold': alert_threshold,
                    'llm_status': self.active_simulations.get(device_id, {}).get('llm_status', 'idle')
                }
                
                current_reasoning = self.active_simulations.get(device_id, {}).get('last_reasoning')
                if current_reasoning:
                    update_data['llm_reasoning'] = current_reasoning
                
                await manager.broadcast_device_update(device_id, update_data)
                
                # --- ALERTS (CRITICAL ONLY) ---
                if prediction.risk_level == 'CRITICAL':
                    # FIRE BACKGROUND TASK
                    asyncio.create_task(self._process_alerts(device_id, region_id, prediction, current_water, current_rain, current_flow, alert_threshold, db))
                
                # Wait before next update
                await asyncio.sleep(update_interval)
                
        except asyncio.CancelledError:
            print(f"[STOP] Simulation cancelled for device: {device_id}")
        except Exception as e:
            print(f"[ERROR] Error in simulation for {device_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if device_id in self.active_simulations:
                del self.active_simulations[device_id]
            if device_id in self.running_tasks:
                del self.running_tasks[device_id]

    async def _process_llm_analysis(self, device_id: str, sensor_data: dict):
        """Run LLM analysis in background without blocking main loop"""
        try:
            if device_id in self.active_simulations:
                self.active_simulations[device_id]['llm_status'] = 'processing'
                await manager.broadcast_device_update(device_id, {'llm_status': 'processing'})
            
            # Run LLM in thread pool
            llm_result = await asyncio.to_thread(analyze_with_llm, sensor_data)
            
            if device_id in self.active_simulations:
                if llm_result:
                    reasoning = llm_result.get('reasoning', 'Analysis completed')
                    start_emoji = "⚠️" if sensor_data.get('water_level', 0) > sensor_data.get('threshold', 0) else "✅"
                    self.active_simulations[device_id]['last_reasoning'] = f"{start_emoji} (Live AI) {reasoning}"
                    self.active_simulations[device_id]['llm_status'] = 'completed'
                    
                    await manager.broadcast_device_update(device_id, {
                        'llm_status': 'completed',
                        'llm_reasoning': self.active_simulations[device_id]['last_reasoning']
                    })
                else:
                    self.active_simulations[device_id]['llm_status'] = 'failed'
                    await manager.broadcast_device_update(device_id, {'llm_status': 'failed'})
                    
        except Exception as e:
            print(f"[_process_llm_analysis] Error: {e}")
            if device_id in self.active_simulations:
                self.active_simulations[device_id]['llm_status'] = 'failed'
                await manager.broadcast_device_update(device_id, {'llm_status': 'failed'})

    async def _process_alerts(self, device_id: str, region_id: str, prediction, water, rain, flow, threshold, db):
        """Process alerts and emails in background"""
        try:
            # Global throttle for this device alert batch (15 mins)
            if device_id in self.active_simulations:
                last_time = self.active_simulations[device_id].get('last_bulk_alert_time')
                if last_time and (datetime.utcnow() - last_time).total_seconds() < 900:
                    return

            # Fetch data (IO bound)
            region = await db.regions.find_one({"region_id": region_id}, {"_id": 0})
            device_doc = await db.devices.find_one({"device_id": device_id}, {"_id": 0})
            participants = await db.participants.find({"region_id": region_id}, {"_id": 0}).to_list(100)
            
            if not participants:
                return

            from notify import send_flood_alert

            if device_id in self.active_simulations and 'last_alert_time' not in self.active_simulations[device_id]:
                self.active_simulations[device_id]['last_alert_time'] = {}

            alerts_sent = 0
            
            for participant in participants:
                p_id = participant['participant_id']
                # Individual cooldown check (30 mins)
                last_sent = self.active_simulations[device_id]['last_alert_time'].get(p_id) if device_id in self.active_simulations else None
                if last_sent and (datetime.utcnow() - last_sent).total_seconds() < 1800:
                    continue

                warning = {
                    "warning_id": f"w_{datetime.utcnow().timestamp()}_{p_id}",
                    "region_id": region_id,
                    "device_id": device_id,
                    "river_name": region.get('river_name', 'Unknown'),
                    "participant_id": p_id,
                    "warning_type": prediction.warning_type,
                    "risk_level": prediction.risk_level,
                    "timestamp": datetime.utcnow(),
                    "water_level": water,
                    "rainfall": rain,
                    "flow_rate": flow
                }
                await db.warnings.insert_one(warning)

                try:
                    sensor_data = {'water_level': water, 'rainfall': rain, 'flow_rate': flow}
                    pred_dict = {'risk_level': prediction.risk_level, 'warning_type': prediction.warning_type}
                    
                    # This call might take time (LLM email generation), but we are in a background task
                    await send_flood_alert(participant, region, device_doc, pred_dict, sensor_data)
                    
                    if device_id in self.active_simulations:
                        self.active_simulations[device_id]['last_alert_time'][p_id] = datetime.utcnow()
                    
                    alerts_sent += 1
                except Exception as e:
                    print(f"[WARN] Alert failed for {participant['name']}: {e}")
            
            if alerts_sent > 0:
                if device_id in self.active_simulations:
                    self.active_simulations[device_id]['last_bulk_alert_time'] = datetime.utcnow()
                
                await manager.broadcast_alert({
                    'region': region.get('name', 'Unknown') if region else 'Unknown',
                    'river': region.get('river_name', 'Unknown') if region else 'Unknown',
                    'risk_level': prediction.risk_level,
                    'water_level': water,
                    'threshold': threshold,
                    'participants_notified': alerts_sent
                })
                
        except Exception as e:
             print(f"[_process_alerts] Error: {e}")

# Global simulation engine instance
engine = SimulationEngine()
