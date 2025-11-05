import multiprocessing as mp
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class ProcessMessageType(Enum):
    # Status updates (Framework -> UI)
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"
    EXPERIMENT_START = "experiment_start"
    EXPERIMENT_COMPLETE = "experiment_complete"
    ITERATION_COMPLETE = "iteration_complete"
    STRATEGY_PROGRESS = "strategy_progress"
    
    # Commands (UI -> Framework)
    CANCEL_COMMAND = "cancel_command"
    END_COMMAND = "end_command"
    PAUSE_COMMAND = "pause_command"
    RESUME_COMMAND = "resume_command"
    STEP_CONTINUE = "step_continue"
    
    # Control messages
    PROCESS_READY = "process_ready"
    PROCESS_COMPLETE = "process_complete"
    PROCESS_ERROR = "process_error"
    HEARTBEAT = "heartbeat"

@dataclass
class ProcessMessage:
    type: ProcessMessageType
    data: Dict[str, Any]
    timestamp: float
    process_id: Optional[str] = None
    
    def to_dict(self):
        return {
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'process_id': self.process_id
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            type=ProcessMessageType(data['type']),
            data=data['data'],
            timestamp=data['timestamp'],
            process_id=data.get('process_id')
        )

class ProcessSafeQueue:
    """Thread and process safe queue wrapper"""
    
    def __init__(self, maxsize=1000):
        self.queue = mp.Queue(maxsize)
        self._closed = False
    
    def put(self, message: ProcessMessage, timeout=1.0):
        if self._closed:
            return False
        try:
            # Convert to dict for JSON serialization
            self.queue.put(message.to_dict(), timeout=timeout)
            return True
        except:
            return False
    
    def get(self, timeout=0.1):
        try:
            data = self.queue.get(timeout=timeout)
            return ProcessMessage.from_dict(data)
        except:
            return None
    
    def close(self):
        self._closed = True
        try:
            self.queue.close()
        except:
            pass
