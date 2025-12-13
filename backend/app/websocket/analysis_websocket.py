"""
Analysis WebSocket Manager
Handles real-time progress updates for Stage 2 deep analysis
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)


class AnalysisWebSocketManager:
    """
    Manages WebSocket connections for analysis progress updates
    
    Provides real-time updates for:
    - Analysis progress (percentage, current repository)
    - Estimated time remaining
    - Completion status
    - Error notifications
    """
    
    def __init__(self):
        """Initialize WebSocket manager"""
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Background task for broadcasting updates
        self.broadcast_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Progress tracker reference (set externally)
        self.progress_tracker = None
    
    def set_progress_tracker(self, progress_tracker):
        """
        Set progress tracker reference
        
        Args:
            progress_tracker: ProgressTracker instance
        """
        self.progress_tracker = progress_tracker
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        logger.info(f"Analysis WebSocket connected for user {user_id}")
        
        # Start broadcast task if not running
        if not self.running:
            self.start_broadcast_task()
        
        # Send initial connection confirmation
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send current progress if analysis is in progress
        if self.progress_tracker:
            progress = await self.progress_tracker.get_progress(user_id)
            if progress:
                await self.send_personal_message(websocket, {
                    "type": "progress_update",
                    "data": progress
                })
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"Analysis WebSocket disconnected for user {user_id}")
        
        # Stop broadcast task if no connections
        if not self.active_connections and self.running:
            self.stop_broadcast_task()
    
    async def send_personal_message(
        self,
        websocket: WebSocket,
        message: dict
    ):
        """
        Send a message to a specific WebSocket connection
        
        Args:
            websocket: WebSocket connection
            message: Message dictionary
        """
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_user(
        self,
        user_id: str,
        message: dict
    ):
        """
        Broadcast a message to all connections for a user
        
        Args:
            user_id: User ID
            message: Message dictionary
        """
        if user_id not in self.active_connections:
            return
        
        # Get all connections for user
        connections = list(self.active_connections[user_id])
        
        # Send to all connections
        disconnected = []
        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket, user_id)
    
    async def broadcast_progress_update(
        self,
        user_id: str,
        progress: dict
    ):
        """
        Broadcast progress update to user
        
        Args:
            user_id: User ID
            progress: Progress dictionary
        """
        message = {
            "type": "progress_update",
            "data": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_user(user_id, message)
    
    async def broadcast_completion(
        self,
        user_id: str,
        results: dict
    ):
        """
        Broadcast analysis completion to user
        
        Args:
            user_id: User ID
            results: Analysis results dictionary
        """
        message = {
            "type": "analysis_complete",
            "data": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_user(user_id, message)
    
    async def broadcast_error(
        self,
        user_id: str,
        error: str
    ):
        """
        Broadcast error to user
        
        Args:
            user_id: User ID
            error: Error message
        """
        message = {
            "type": "analysis_error",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_user(user_id, message)
    
    def start_broadcast_task(self):
        """Start background task for broadcasting updates"""
        if not self.running:
            self.running = True
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
            logger.info("Started analysis WebSocket broadcast task")
    
    def stop_broadcast_task(self):
        """Stop background task for broadcasting updates"""
        if self.running:
            self.running = False
            if self.broadcast_task:
                self.broadcast_task.cancel()
            logger.info("Stopped analysis WebSocket broadcast task")
    
    async def _broadcast_loop(self):
        """
        Background loop for broadcasting progress updates
        
        Checks for progress updates every 2 seconds and broadcasts to connected clients
        """
        while self.running:
            try:
                # Get all active user IDs
                user_ids = list(self.active_connections.keys())
                
                # Check progress for each user
                for user_id in user_ids:
                    if self.progress_tracker:
                        progress = await self.progress_tracker.get_progress(user_id)
                        
                        if progress and progress.get('status') == 'in_progress':
                            # Broadcast progress update
                            await self.broadcast_progress_update(user_id, progress)
                        elif progress and progress.get('status') == 'completed':
                            # Broadcast completion
                            await self.broadcast_completion(user_id, progress)
                        elif progress and progress.get('status') == 'failed':
                            # Broadcast error
                            error = progress.get('error', 'Analysis failed')
                            await self.broadcast_error(user_id, error)
                
                # Wait before next check
                await asyncio.sleep(2.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(2.0)
    
    async def handle_client_message(
        self,
        websocket: WebSocket,
        user_id: str,
        message: dict
    ):
        """
        Handle incoming message from client
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            message: Message dictionary
        """
        message_type = message.get('type')
        
        if message_type == 'ping':
            # Respond to ping
            await self.send_personal_message(websocket, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == 'get_progress':
            # Send current progress
            if self.progress_tracker:
                progress = await self.progress_tracker.get_progress(user_id)
                if progress:
                    await self.send_personal_message(websocket, {
                        "type": "progress_update",
                        "data": progress
                    })
                else:
                    await self.send_personal_message(websocket, {
                        "type": "no_progress",
                        "message": "No analysis in progress"
                    })
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections
        
        Returns:
            Number of active connections
        """
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of connections for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of connections for user
        """
        return len(self.active_connections.get(user_id, set()))


# Global WebSocket manager instance
analysis_ws_manager = AnalysisWebSocketManager()


async def analysis_websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint for analysis progress updates
    
    Args:
        websocket: WebSocket connection
        user_id: User ID (from authentication)
    """
    await analysis_ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await analysis_ws_manager.handle_client_message(
                    websocket,
                    user_id,
                    message
                )
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client: {data}")
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
    
    except WebSocketDisconnect:
        await analysis_ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await analysis_ws_manager.disconnect(websocket, user_id)
