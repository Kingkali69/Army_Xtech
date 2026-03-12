#!/usr/bin/env python3
"""
Offline Buffering System
Buffers events when disconnected and replays when connection restores
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
from dataclasses import dataclass, field

@dataclass
class BufferedEvent:
    """Event buffered for later replay"""
    event_type: str
    data: Dict[str, Any]
    timestamp: float
    device_id: str
    sequence: int = 0

class OfflineBuffer:
    """Buffer events when offline and replay when connected"""
    
    def __init__(self, max_buffer_size=1000):
        self.buffer = deque(maxlen=max_buffer_size)
        self.lock = threading.Lock()
        self.sequence_counter = 0
        self.replay_in_progress = False
        
    def add_event(self, event_type: str, data: Dict[str, Any], device_id: str):
        """Add event to buffer"""
        with self.lock:
            self.sequence_counter += 1
            event = BufferedEvent(
                event_type=event_type,
                data=data,
                timestamp=time.time(),
                device_id=device_id,
                sequence=self.sequence_counter
            )
            self.buffer.append(event)
    
    def get_buffered_events(self, since_sequence: int = 0) -> List[Dict]:
        """Get buffered events since sequence number"""
        with self.lock:
            events = []
            for event in self.buffer:
                if event.sequence > since_sequence:
                    dt = datetime.fromtimestamp(event.timestamp)
                    events.append({
                        'type': event.event_type,
                        'data': event.data,
                        'timestamp': dt.strftime('%H:%M:%S.%f')[:-3],
                        'device_id': event.device_id,
                        'sequence': event.sequence
                    })
            return events
    
    def replay_events(self, callback) -> int:
        """Replay buffered events to callback function"""
        if self.replay_in_progress:
            return 0
        
        self.replay_in_progress = True
        try:
            with self.lock:
                events_to_replay = list(self.buffer)
                replay_count = len(events_to_replay)
            
            # Replay events in order
            for event in events_to_replay:
                try:
                    callback(event.event_type, event.data, event.device_id, event.timestamp)
                except Exception as e:
                    print(f"[OFFLINE BUFFER] Error replaying event {event.sequence}: {e}")
            
            # Clear buffer after successful replay
            with self.lock:
                self.buffer.clear()
            
            return replay_count
        finally:
            self.replay_in_progress = False
    
    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.buffer.clear()
    
    def size(self) -> int:
        """Get buffer size"""
        with self.lock:
            return len(self.buffer)

# Global instance
_buffer_instance = None

def get_offline_buffer() -> OfflineBuffer:
    """Get global offline buffer instance"""
    global _buffer_instance
    if _buffer_instance is None:
        _buffer_instance = OfflineBuffer()
    return _buffer_instance

