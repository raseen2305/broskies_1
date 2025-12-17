"""
WebSocket Event Batching Service
Batches progress events to reduce WebSocket message frequency
Requirements: 3.5
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class WebSocketEventBatcher:
    """
    Batches WebSocket events to reduce message frequency.
    
    Features:
    - 500ms batching interval
    - Event merging for similar events
    - Priority system for critical events
    - Per-scan event queues
    
    Requirements: 3.5
    """
    
    def __init__(self, batch_interval: float = 0.5):
        """
        Initialize the event batcher.
        
        Args:
            batch_interval: Batching interval in seconds (default 500ms)
        """
        self.batch_interval = batch_interval
        self.event_queues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.is_running = False
        self.batch_task: Optional[asyncio.Task] = None
        self.websocket_manager = None
        
        logger.info(f"WebSocket Event Batcher initialized with {batch_interval}s interval")
    
    def set_websocket_manager(self, manager):
        """Set the WebSocket manager for broadcasting"""
        self.websocket_manager = manager
    
    async def start(self):
        """Start the batching service"""
        if self.is_running:
            logger.warning("Event batcher already running")
            return
        
        self.is_running = True
        self.batch_task = asyncio.create_task(self._batch_loop())
        logger.info("Event batcher started")
    
    async def stop(self):
        """Stop the batching service"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining events
        await self._flush_all_queues()
        logger.info("Event batcher stopped")
    
    def add_event(
        self,
        scan_id: str,
        user_id: str,
        event: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL
    ):
        """
        Add an event to the batch queue.
        
        Args:
            scan_id: Scan identifier
            user_id: User identifier
            event: Event data
            priority: Event priority level
        """
        event_data = {
            'scan_id': scan_id,
            'user_id': user_id,
            'event': event,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Critical events bypass batching
        if priority == EventPriority.CRITICAL:
            asyncio.create_task(self._send_immediate(event_data))
        else:
            self.event_queues[scan_id].append(event_data)
    
    async def _batch_loop(self):
        """Main batching loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._process_batches()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch loop: {e}")
    
    async def _process_batches(self):
        """Process all queued events"""
        if not self.event_queues:
            return
        
        # Process each scan's queue
        for scan_id in list(self.event_queues.keys()):
            queue = self.event_queues[scan_id]
            if not queue:
                continue
            
            # Merge similar events
            merged_events = self._merge_events(queue)
            
            # Send batched events
            if merged_events:
                await self._send_batch(scan_id, merged_events)
            
            # Clear processed queue
            self.event_queues[scan_id] = []
    
    def _merge_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge similar events to reduce message count.
        
        Strategy:
        - Keep the latest event for each phase
        - Preserve high-priority events
        - Merge progress updates
        """
        if not events:
            return []
        
        # Group events by phase
        phase_events: Dict[str, Dict[str, Any]] = {}
        high_priority_events: List[Dict[str, Any]] = []
        
        for event_data in events:
            priority = event_data['priority']
            event = event_data['event']
            
            # Keep high-priority events separate
            if priority in (EventPriority.HIGH, EventPriority.CRITICAL):
                high_priority_events.append(event_data)
                continue
            
            # Get phase from event
            phase = event.get('phase', 'unknown')
            
            # Keep only the latest event per phase
            if phase not in phase_events or \
               event_data['timestamp'] > phase_events[phase]['timestamp']:
                phase_events[phase] = event_data
        
        # Combine phase events and high-priority events
        merged = list(phase_events.values()) + high_priority_events
        
        # Sort by timestamp
        merged.sort(key=lambda x: x['timestamp'])
        
        logger.debug(f"Merged {len(events)} events into {len(merged)} events")
        return merged
    
    async def _send_batch(self, scan_id: str, events: List[Dict[str, Any]]):
        """Send a batch of events"""
        if not self.websocket_manager or not events:
            return
        
        try:
            # Get user_id from first event
            user_id = events[0]['user_id']
            
            # Create batch message
            batch_message = {
                'type': 'scan_progress_batch',
                'scan_id': scan_id,
                'events': [e['event'] for e in events],
                'batch_size': len(events),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Broadcast to user
            await self.websocket_manager.broadcast_to_user(user_id, batch_message)
            
            logger.debug(f"Sent batch of {len(events)} events for scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
    
    async def _send_immediate(self, event_data: Dict[str, Any]):
        """Send a critical event immediately"""
        if not self.websocket_manager:
            return
        
        try:
            user_id = event_data['user_id']
            event = event_data['event']
            
            message = {
                'type': 'scan_progress',
                'task_id': event_data['scan_id'],
                'progress': event,
                'priority': 'critical'
            }
            
            await self.websocket_manager.broadcast_to_user(user_id, message)
            
            logger.debug(f"Sent critical event immediately for scan {event_data['scan_id']}")
            
        except Exception as e:
            logger.error(f"Error sending immediate event: {e}")
    
    async def _flush_all_queues(self):
        """Flush all remaining events in queues"""
        for scan_id in list(self.event_queues.keys()):
            queue = self.event_queues[scan_id]
            if queue:
                merged_events = self._merge_events(queue)
                await self._send_batch(scan_id, merged_events)
        
        self.event_queues.clear()
        logger.info("Flushed all event queues")
    
    def get_queue_size(self, scan_id: str) -> int:
        """Get the current queue size for a scan"""
        return len(self.event_queues.get(scan_id, []))
    
    def get_total_queue_size(self) -> int:
        """Get the total queue size across all scans"""
        return sum(len(queue) for queue in self.event_queues.values())


# Global instance
event_batcher = WebSocketEventBatcher()


async def start_event_batcher(websocket_manager):
    """Start the global event batcher"""
    event_batcher.set_websocket_manager(websocket_manager)
    await event_batcher.start()


async def stop_event_batcher():
    """Stop the global event batcher"""
    await event_batcher.stop()
