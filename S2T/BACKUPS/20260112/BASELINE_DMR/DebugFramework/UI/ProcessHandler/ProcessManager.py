# ProcessCommunication.py
import multiprocessing as mp
import queue
import time
import threading
import os
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Callable
from enum import Enum
import json

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

from UI.ProcessHandler.ProcessTypes import ProcessSafeQueue, ProcessMessage, ProcessMessageType
from UI.ProcessHandler.ProcessExecutor import framework_process_main

class ProcessCommunicationManager:
    """Manages communication between UI and Framework processes"""
    
    def __init__(self):
        # Queues for bidirectional communication
        self.ui_to_framework = ProcessSafeQueue()  # Commands from UI to Framework
        self.framework_to_ui = ProcessSafeQueue()  # Status updates from Framework to UI
        
        # Process management
        self.framework_process = None
        self.communication_active = False
        
        # Callbacks for UI updates
        self.status_callbacks = []
        
        # Start communication thread
        self.comm_thread = None
        self.start_communication()
    
    def start_communication(self):
        """Start communication thread"""
        self.communication_active = True
        self.comm_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.comm_thread.start()
    
    def stop_communication(self):
        """Stop communication"""
        self.communication_active = False
        if self.comm_thread:
            self.comm_thread.join(timeout=2.0)
        
        # Close queues
        self.ui_to_framework.close()
        self.framework_to_ui.close()
    
    def _communication_loop(self):
        """Main communication loop running in separate thread"""
        while self.communication_active:
            try:
                # Check for messages from Framework
                message = self.framework_to_ui.get(timeout=0.1)
                if message:
                    self._handle_framework_message(message)
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"Communication loop error: {e}")
    
    def _handle_framework_message(self, message: ProcessMessage):
        """Handle message from Framework process"""
        # Call all registered callbacks
        for callback in self.status_callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def register_status_callback(self, callback: Callable[[ProcessMessage], None]):
        """Register callback for status updates"""
        self.status_callbacks.append(callback)
    
    def send_command_to_framework(self, command_type: ProcessMessageType, data: Dict[str, Any] = None):
        """Send command from UI to Framework"""
        message = ProcessMessage(
            type=command_type,
            data=data or {},
            timestamp=time.time(),
            process_id="UI"
        )
        return self.ui_to_framework.put(message)
    
    def start_framework_process(self, experiment_data, config_data, framework):
        """Start Framework in separate process"""
        if self.framework_process and self.framework_process.is_alive():
            print("Framework process already running")
            return False
        
        try:
            self.framework_process = mp.Process(
                target=framework_process_main,
                args=(
                    experiment_data,
                    config_data,
                    self.ui_to_framework.queue,
                    self.framework_to_ui.queue,
                    framework
                ),
                daemon=False
            )
            self.framework_process.start()
            return True
            
        except Exception as e:
            print(f"Error starting framework process: {e}")
            return False
    
    def terminate_framework_process(self):
        """Terminate Framework process"""
        if self.framework_process:
            try:
                # Send termination command first
                self.send_command_to_framework(ProcessMessageType.CANCEL_COMMAND, {"reason": "Process termination"})
                
                # Wait for graceful shutdown
                self.framework_process.join(timeout=5.0)
                
                # Force terminate if needed
                if self.framework_process.is_alive():
                    self.framework_process.terminate()
                    self.framework_process.join(timeout=2.0)
                
                self.framework_process = None
                return True
                
            except Exception as e:
                print(f"Error terminating framework process: {e}")
                return False
        return True
    