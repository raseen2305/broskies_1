from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
import logging
from app.core.security import verify_token

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, scan_id: str):
        await websocket.accept()
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = []
        self.active_connections[scan_id].append(websocket)
        logger.info(f"WebSocket connected for scan_id: {scan_id}")
    
    def disconnect(self, websocket: WebSocket, scan_id: str):
        if scan_id in self.active_connections:
            self.active_connections[scan_id].remove(websocket)
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]
        logger.info(f"WebSocket disconnected for scan_id: {scan_id}")
    
    async def send_progress_update(self, scan_id: str, data: dict):
        if scan_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[scan_id]:
                try:
                    await connection.send_text(json.dumps(data))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[scan_id].remove(conn)

manager = ConnectionManager()

@router.websocket("/scan-progress/{scan_id}")
async def websocket_scan_progress(websocket: WebSocket, scan_id: str):
    """WebSocket endpoint for real-time scan progress updates"""
    try:
        # Verify authentication (optional - could be done via query params)
        await manager.connect(websocket, scan_id)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to scan progress updates",
            "scan_id": scan_id
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (ping/pong for keep-alive)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for scan_id {scan_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket, scan_id)

# Function to send progress updates (called from scan router)
async def send_scan_progress_update(scan_id: str, progress_data: dict):
    """Send progress update to all connected WebSocket clients"""
    await manager.send_progress_update(scan_id, {
        "type": "progress_update",
        "scan_id": scan_id,
        **progress_data
    })