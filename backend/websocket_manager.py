"""
Real-time WebSocket Manager for Live Sensor Updates
"""
from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.device_data: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    def update_device_data(self, device_id: str, data: dict):
        """Update cached device data"""
        self.device_data[device_id] = {
            **data,
            'last_update': datetime.utcnow().isoformat()
        }
    
    async def broadcast_device_update(self, device_id: str, data: dict):
        """Broadcast device update to all clients"""
        self.update_device_data(device_id, data)
        await self.broadcast({
            'type': 'device_update',
            'device_id': device_id,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def broadcast_alert(self, alert_data: dict):
        """Broadcast flood alert to all clients"""
        await self.broadcast({
            'type': 'flood_alert',
            'data': alert_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def broadcast_warning(self, warning_data: dict):
        """Broadcast warning to all clients"""
        await self.broadcast({
            'type': 'warning_generated',
            'data': warning_data,
            'timestamp': datetime.utcnow().isoformat()
        })

# Global connection manager instance
manager = ConnectionManager()
