import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.core.security import verify_token
from app.core.config import settings
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

def verify_websocket_token(token: str) -> dict:
    """Verify JWT token for WebSocket connections (doesn't raise HTTPException)"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            raise ValueError("Token has expired")
        
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")

class ScanWebSocketManager:
    """Manages WebSocket connections for scan progress updates"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store task subscriptions by user_id
        self.user_tasks: Dict[str, Set[str]] = {}
        # Background task for broadcasting updates
        self.broadcast_task = None
        self.running = False
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
            self.user_tasks[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Start broadcast task if not running
        if not self.running:
            self.start_broadcast_task()
        
        # Send initial connection confirmation
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_tasks:
                    del self.user_tasks[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
        
        # Stop broadcast task if no connections
        if not self.active_connections and self.running:
            self.stop_broadcast_task()
    
    async def subscribe_to_task(self, user_id: str, task_id: str):
        """Subscribe a user to task progress updates"""
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = set()
        
        self.user_tasks[user_id].add(task_id)
        logger.info(f"User {user_id} subscribed to task {task_id}")
    
    async def unsubscribe_from_task(self, user_id: str, task_id: str):
        """Unsubscribe a user from task progress updates"""
        if user_id in self.user_tasks:
            self.user_tasks[user_id].discard(task_id)
            logger.info(f"User {user_id} unsubscribed from task {task_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast a message to all connections for a specific user"""
        if user_id not in self.active_connections:
            return
        
        disconnected_websockets = []
        
        for websocket in self.active_connections[user_id].copy():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message))
                else:
                    disconnected_websockets.append(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.active_connections[user_id].discard(websocket)
    
    def start_broadcast_task(self):
        """Start the background task for broadcasting progress updates"""
        if not self.running:
            self.running = True
            self.broadcast_task = asyncio.create_task(self._broadcast_progress_updates())
            logger.info("Started WebSocket broadcast task")
    
    def stop_broadcast_task(self):
        """Stop the background broadcast task"""
        if self.running and self.broadcast_task:
            self.running = False
            self.broadcast_task.cancel()
            logger.info("Stopped WebSocket broadcast task")
    
    async def _broadcast_progress_updates(self):
        """Background task to periodically broadcast progress updates"""
        while self.running:
            try:
                # Check progress for all subscribed tasks
                for user_id, task_ids in self.user_tasks.items():
                    if not task_ids or user_id not in self.active_connections:
                        continue
                    
                    for task_id in task_ids.copy():
                        try:
                            # Get progress from enhanced tracker first
                            from app.services.scan_progress_tracker import get_scan_progress_data
                            progress = await get_scan_progress_data(task_id)
                            
                            # Fallback to database if not in tracker
                            if not progress:
                                try:
                                    from app.database import get_database
                                    db = await get_database()
                                    if db:
                                        progress = await db.scan_progress.find_one({"task_id": task_id})
                                        if progress:
                                            progress.pop('_id', None)
                                except Exception as db_error:
                                    logger.debug(f"Could not get progress from database: {db_error}")
                            
                            if progress:
                                message = {
                                    "type": "scan_progress",
                                    "task_id": task_id,
                                    "progress": progress,
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                                
                                await self.broadcast_to_user(user_id, message)
                                
                                # Unsubscribe if task is completed or failed
                                status = progress.get('status') or progress.get('phase')
                                if status in ['completed', 'error']:
                                    await self.unsubscribe_from_task(user_id, task_id)
                            
                        except Exception as e:
                            logger.error(f"Error checking progress for task {task_id}: {e}")
                
                # Wait before next update cycle
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast task: {e}")
                await asyncio.sleep(5)  # Wait longer on error

# Global WebSocket manager instance
websocket_manager = ScanWebSocketManager()

async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for scan progress updates"""
    
    user_id = None
    
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        try:
            payload = verify_websocket_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token: missing user ID")
                return
                
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"WebSocket authentication failed: {error_msg}")
            await websocket.close(code=4001, reason=error_msg[:123])  # WebSocket close reason max 123 bytes
            return
        except Exception as e:
            error_msg = f"Unexpected authentication error: {str(e)}"
            logger.error(f"WebSocket authentication failed: {error_msg}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect user
        await websocket_manager.connect(websocket, user_id)
        
        try:
            while True:
                # Listen for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "subscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await websocket_manager.subscribe_to_task(user_id, task_id)
                        
                        # Send immediate progress update
                        # Import here to avoid circular import
                        from app.tasks.scan_tasks import get_scan_progress
                        progress = await get_scan_progress(task_id)
                        
                        if progress:
                            await websocket_manager.send_personal_message(websocket, {
                                "type": "scan_progress",
                                "task_id": task_id,
                                "progress": progress,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                
                elif message_type == "unsubscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await websocket_manager.unsubscribe_from_task(user_id, task_id)
                
                elif message_type == "ping":
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
    
    finally:
        if user_id:
            await websocket_manager.disconnect(websocket, user_id)

# Helper function to send scan updates
async def send_scan_update(user_id: str, task_id: str, update_data: dict):
    """Send a scan update to a specific user"""
    message = {
        "type": "scan_update",
        "task_id": task_id,
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await websocket_manager.broadcast_to_user(user_id, message)