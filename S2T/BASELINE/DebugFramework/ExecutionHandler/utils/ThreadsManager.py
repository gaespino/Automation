"""
Thread Management and Cleanup System for Debug Framework
Provides comprehensive thread lifecycle management, cleanup, and emergency termination
"""

import threading
import time
import queue
import psutil
import os
import signal
import sys
from typing import Dict, List, Optional, Callable, Any
from enum import Enum, auto
from dataclasses import dataclass
import tkinter as tk
from tkinter import TclError

class ThreadState(Enum):
    """Thread state enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    CLEANUP = "cleanup"
    TERMINATED = "terminated"
    ABANDONED = "abandoned"
    ERROR = "error"

class CleanupPhase(Enum):
    """Cleanup phase enumeration"""
    INITIATED = auto()
    FRAMEWORK_STOPPING = auto()
    THREAD_JOINING = auto()
    STATE_CLEANUP = auto()
    UI_CLEANUP = auto()
    FINALIZATION = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class ThreadInfo:
    """Thread information tracking"""
    thread: threading.Thread
    name: str
    state: ThreadState
    start_time: float
    cleanup_start_time: Optional[float] = None
    force_stop_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class FrameworkThreadManager:
    """Comprehensive thread management system for Debug Framework"""
    
    def __init__(self, ui_controller=None, logger=None):
        self.ui_controller = ui_controller
        self.logger = logger or print
        
        # Thread tracking
        self.active_threads: Dict[str, ThreadInfo] = {}
        self.cleanup_threads: Dict[str, threading.Thread] = {}
        self.thread_lock = threading.RLock()
        
        # Cleanup coordination
        self.cleanup_events: Dict[str, threading.Event] = {}
        self.force_stop_events: Dict[str, threading.Event] = {}
        self.cleanup_callbacks: Dict[str, List[Callable]] = {}
        
        # Emergency termination tracking
        self.emergency_processes: List[int] = []
        self.main_process_pid = os.getpid()
        
        # Configuration
        self.graceful_timeout = 5.0  # seconds
        self.force_timeout = 10.0    # seconds
        self.cleanup_timeout = 15.0  # seconds
        
        # Status tracking
        self.cleanup_status: Dict[str, CleanupPhase] = {}
        self.cleanup_progress: Dict[str, Dict[str, Any]] = {}
        
        self._log("FrameworkThreadManager initialized")
    
    def _log(self, message: str, level: str = "INFO"):
        """Enhanced logging with thread info"""
        try:
            thread_name = threading.current_thread().name
            timestamp = time.strftime("%H:%M:%S")
            log_msg = f"[{timestamp}][{thread_name}][{level}] THREAD_MGR: {message}"
                
            # Also log to UI if available
            if self.ui_controller and hasattr(self.ui_controller, 'log_status'):
                try:
                    self.ui_controller.log_status(message)
                except (TclError, AttributeError):
                    pass  # UI might be destroyed
            
            elif self.logger:
                self.logger(log_msg)
            else:
                print(log_msg)                   
        except Exception as e:
            print(f"Logging error: {e}")
    
    # ==================== THREAD REGISTRATION AND TRACKING ====================
    
    def register_thread(self, thread: threading.Thread, name: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a thread for management"""
        with self.thread_lock:
            thread_info = ThreadInfo(
                thread=thread,
                name=name,
                state=ThreadState.IDLE,
                start_time=time.time(),
                metadata=metadata or {}
            )
            
            self.active_threads[name] = thread_info
            self.cleanup_events[name] = threading.Event()
            self.force_stop_events[name] = threading.Event()
            self.cleanup_callbacks[name] = []
            
            self._log(f"📝 Registered thread: {name}")
            return name
    
    def start_managed_thread(self, name: str) -> bool:
        """Start a registered thread"""
        with self.thread_lock:
            if name not in self.active_threads:
                self._log(f"❌ Thread {name} not registered", "ERROR")
                return False
            
            thread_info = self.active_threads[name]
            
            try:
                thread_info.thread.start()
                thread_info.state = ThreadState.RUNNING
                thread_info.start_time = time.time()
                
                self._log(f"🚀 Started managed thread: {name}")
                return True
                
            except Exception as e:
                thread_info.state = ThreadState.ERROR
                self._log(f"❌ Failed to start thread {name}: {e}", "ERROR")
                return False
    
    def add_cleanup_callback(self, thread_name: str, callback: Callable):
        """Add cleanup callback for a thread"""
        with self.thread_lock:
            if thread_name in self.cleanup_callbacks:
                self.cleanup_callbacks[thread_name].append(callback)
                self._log(f"📋 Added cleanup callback for {thread_name}")
    
    # ==================== GRACEFUL SHUTDOWN ====================
    
    def request_graceful_shutdown(self, thread_name: str, 
                                 timeout: Optional[float] = None) -> bool:
        """Request graceful shutdown of a thread"""
        timeout = timeout or self.graceful_timeout
        
        with self.thread_lock:
            if thread_name not in self.active_threads:
                self._log(f"⚠️ Thread {thread_name} not found for graceful shutdown")
                return True  # Already gone
            
            thread_info = self.active_threads[thread_name]
            
            if thread_info.state != ThreadState.RUNNING:
                self._log(f"⚠️ Thread {thread_name} not running (state: {thread_info.state})")
                return True
            
            self._log(f"🛑 Requesting graceful shutdown: {thread_name}")
            thread_info.state = ThreadState.STOPPING
            
            # Set cleanup event to signal the thread
            self.cleanup_events[thread_name].set()
            
            # Start cleanup monitoring
            cleanup_thread = threading.Thread(
                target=self._monitor_graceful_shutdown,
                args=(thread_name, timeout),
                name=f"Cleanup_{thread_name}",
                daemon=True
            )
            
            self.cleanup_threads[thread_name] = cleanup_thread
            cleanup_thread.start()
            
            return True
    
    def _monitor_graceful_shutdown(self, thread_name: str, timeout: float):
        """Monitor graceful shutdown process"""
        try:
            self._log(f"👁️ Monitoring graceful shutdown: {thread_name}")
            self.cleanup_status[thread_name] = CleanupPhase.INITIATED
            
            thread_info = self.active_threads[thread_name]
            thread_info.cleanup_start_time = time.time()
            
            # Phase 1: Wait for thread to respond
            self.cleanup_status[thread_name] = CleanupPhase.FRAMEWORK_STOPPING
            self._update_cleanup_progress(thread_name, "Requesting framework shutdown", 10)
            
            # Execute cleanup callbacks
            for callback in self.cleanup_callbacks[thread_name]:
                try:
                    callback()
                except Exception as e:
                    self._log(f"❌ Cleanup callback error for {thread_name}: {e}", "ERROR")
            
            # Phase 2: Wait for thread to join
            self.cleanup_status[thread_name] = CleanupPhase.THREAD_JOINING
            self._update_cleanup_progress(thread_name, "Waiting for thread termination", 30)
            
            thread_info.thread.join(timeout=timeout)
            
            # Phase 3: Check if thread terminated
            if thread_info.thread.is_alive():
                self._log(f"⚠️ Thread {thread_name} did not terminate gracefully")
                self._initiate_force_termination(thread_name)
            else:
                self._log(f"✅ Thread {thread_name} terminated gracefully")
                self._finalize_thread_cleanup(thread_name, graceful=True)
                
        except Exception as e:
            self._log(f"❌ Error monitoring shutdown for {thread_name}: {e}", "ERROR")
            self._initiate_force_termination(thread_name)
    
    # ==================== FORCE TERMINATION ====================
    
    def _initiate_force_termination(self, thread_name: str):
        """Initiate force termination of a thread"""
        try:
            self._log(f"🔨 Initiating force termination: {thread_name}")
            
            with self.thread_lock:
                if thread_name not in self.active_threads:
                    return
                
                thread_info = self.active_threads[thread_name]
                thread_info.force_stop_time = time.time()
                thread_info.state = ThreadState.CLEANUP
                
                self.cleanup_status[thread_name] = CleanupPhase.STATE_CLEANUP
                self._update_cleanup_progress(thread_name, "Force termination initiated", 50)
                
                # Set force stop event
                self.force_stop_events[thread_name].set()
            
            # Wait a bit more for force termination
            thread_info.thread.join(timeout=self.force_timeout)
            
            if thread_info.thread.is_alive():
                self._log(f"⚠️ Thread {thread_name} survived force termination - abandoning")
                self._abandon_thread(thread_name)
            else:
                self._log(f"✅ Thread {thread_name} force terminated successfully")
                self._finalize_thread_cleanup(thread_name, graceful=False)
                
        except Exception as e:
            self._log(f"❌ Error in force termination for {thread_name}: {e}", "ERROR")
            self._abandon_thread(thread_name)
    
    def _abandon_thread(self, thread_name: str):
        """Abandon an unresponsive thread"""
        try:
            self._log(f"🏃‍♂️ Abandoning unresponsive thread: {thread_name}")
            
            with self.thread_lock:
                if thread_name in self.active_threads:
                    thread_info = self.active_threads[thread_name]
                    thread_info.state = ThreadState.ABANDONED
                    
                    # Mark as abandoned but keep reference for monitoring
                    self.cleanup_status[thread_name] = CleanupPhase.FAILED
                    self._update_cleanup_progress(thread_name, "Thread abandoned", 100)
            
            # Note: In Python, we can't forcefully kill threads
            # The thread will remain as a daemon and should eventually be cleaned up by the interpreter
            
        except Exception as e:
            self._log(f"❌ Error abandoning thread {thread_name}: {e}", "ERROR")
    
    # ==================== CLEANUP FINALIZATION ====================
    
    def _finalize_thread_cleanup(self, thread_name: str, graceful: bool = True):
        """Finalize thread cleanup"""
        try:
            self._log(f"🧹 Finalizing cleanup for {thread_name} (graceful: {graceful})")
            
            self.cleanup_status[thread_name] = CleanupPhase.UI_CLEANUP
            self._update_cleanup_progress(thread_name, "Cleaning up UI state", 80)
            
            # UI cleanup (if available)
            if self.ui_controller:
                try:
                    if hasattr(self.ui_controller, '_cleanup_ui_state'):
                        self.ui_controller._cleanup_ui_state()
                except Exception as e:
                    self._log(f"UI cleanup error: {e}", "ERROR")
            
            # Final cleanup
            self.cleanup_status[thread_name] = CleanupPhase.FINALIZATION
            self._update_cleanup_progress(thread_name, "Finalizing", 90)
            
            with self.thread_lock:
                # Clean up tracking data
                self.active_threads.pop(thread_name, None)
                self.cleanup_events.pop(thread_name, None)
                self.force_stop_events.pop(thread_name, None)
                self.cleanup_callbacks.pop(thread_name, None)
                self.cleanup_threads.pop(thread_name, None)
            
            self.cleanup_status[thread_name] = CleanupPhase.COMPLETED
            self._update_cleanup_progress(thread_name, "Cleanup completed", 100)
            
            self._log(f"✅ Thread {thread_name} cleanup finalized")
            
        except Exception as e:
            self._log(f"❌ Error finalizing cleanup for {thread_name}: {e}", "ERROR")
    
    def _update_cleanup_progress(self, thread_name: str, message: str, progress: int):
        """Update cleanup progress"""
        self.cleanup_progress[thread_name] = {
            'message': message,
            'progress': progress,
            'timestamp': time.time()
        }
        
        # Update UI if available
        if self.ui_controller and hasattr(self.ui_controller, 'log_status'):
            try:
                self.ui_controller.log_status(f"🔄 {thread_name}: {message} ({progress}%)")
            except:
                pass
    
    # ==================== EMERGENCY TERMINATION ====================
    
    def emergency_shutdown_all(self) -> bool:
        """Emergency shutdown of all threads"""
        self._log("🚨 EMERGENCY SHUTDOWN INITIATED")
        
        try:
            with self.thread_lock:
                active_names = list(self.active_threads.keys())
            
            if not active_names:
                self._log("✅ No active threads to shutdown")
                return True
            
            self._log(f"🛑 Emergency shutdown for {len(active_names)} threads: {active_names}")
            
            # Set all force stop events
            for name in active_names:
                if name in self.force_stop_events:
                    self.force_stop_events[name].set()
            
            # Wait briefly for threads to respond
            time.sleep(1.0)
            
            # Check which threads are still alive
            surviving_threads = []
            for name in active_names:
                if name in self.active_threads:
                    thread_info = self.active_threads[name]
                    if thread_info.thread.is_alive():
                        surviving_threads.append(name)
            
            if surviving_threads:
                self._log(f"⚠️ {len(surviving_threads)} threads survived emergency shutdown: {surviving_threads}")
                
                # Abandon surviving threads
                for name in surviving_threads:
                    self._abandon_thread(name)
            
            # Clear all tracking
            with self.thread_lock:
                self.active_threads.clear()
                self.cleanup_events.clear()
                self.force_stop_events.clear()
                self.cleanup_callbacks.clear()
                self.cleanup_threads.clear()
            
            self._log("✅ Emergency shutdown completed")
            return True
            
        except Exception as e:
            self._log(f"❌ Emergency shutdown error: {e}", "ERROR")
            return False
    
    def force_kill_process_tree(self) -> bool:
        """Force kill the entire process tree (nuclear option)"""
        self._log("☢️ NUCLEAR OPTION: Force killing process tree")
        
        try:
            current_process = psutil.Process(self.main_process_pid)
            children = current_process.children(recursive=True)
            
            self._log(f"🔍 Found {len(children)} child processes")
            
            # Terminate children first
            for child in children:
                try:
                    self._log(f"🔪 Terminating child process {child.pid}")
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait for children to terminate
            gone, alive = psutil.wait_procs(children, timeout=3)
            
            # Kill any remaining children
            for child in alive:
                try:
                    self._log(f"💀 Force killing child process {child.pid}")
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Finally, terminate main process
            self._log("💀 Terminating main process")
            current_process.terminate()
            
            return True
            
        except Exception as e:
            self._log(f"❌ Process tree kill error: {e}", "ERROR")
            return False
    
    # ==================== STATUS AND MONITORING ====================
    
    def get_thread_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all managed threads"""
        with self.thread_lock:
            status = {}
            
            for name, thread_info in self.active_threads.items():
                status[name] = {
                    'state': thread_info.state.value,
                    'is_alive': thread_info.thread.is_alive(),
                    'start_time': thread_info.start_time,
                    'cleanup_start_time': thread_info.cleanup_start_time,
                    'force_stop_time': thread_info.force_stop_time,
                    'cleanup_phase': self.cleanup_status.get(name, CleanupPhase.INITIATED).name,
                    'cleanup_progress': self.cleanup_progress.get(name, {}),
                    'metadata': thread_info.metadata
                }
            
            return status
    
    def print_thread_status(self):
        """Print detailed thread status"""
        status = self.get_thread_status()
        
        print("\n" + "="*60)
        print("FRAMEWORK THREAD MANAGER STATUS")
        print("="*60)
        
        if not status:
            print("No active threads")
        else:
            for name, info in status.items():
                print(f"\nThread: {name}")
                print(f"  State: {info['state']}")
                print(f"  Alive: {info['is_alive']}")
                print(f"  Cleanup Phase: {info['cleanup_phase']}")
                
                if info['cleanup_progress']:
                    progress = info['cleanup_progress']
                    print(f"  Progress: {progress.get('message', 'N/A')} ({progress.get('progress', 0)}%)")
                
                if info['start_time']:
                    runtime = time.time() - info['start_time']
                    print(f"  Runtime: {runtime:.1f}s")
        
        print("="*60)
    
    def is_cleanup_complete(self) -> bool:
        """Check if all cleanup operations are complete"""
        with self.thread_lock:
            if not self.active_threads:
                return True
            
            for name in self.active_threads:
                phase = self.cleanup_status.get(name, CleanupPhase.INITIATED)
                if phase not in [CleanupPhase.COMPLETED, CleanupPhase.FAILED]:
                    return False
            
            return True
    
    def wait_for_cleanup_complete(self, timeout: float = 30.0) -> bool:
        """Wait for all cleanup operations to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_cleanup_complete():
                return True
            time.sleep(0.1)
        
        return False
    
    # ==================== UTILITY METHODS ====================
    
    def cleanup_all(self, timeout: Optional[float] = None) -> bool:
        """Clean up all managed threads"""
        timeout = timeout or self.cleanup_timeout
        
        with self.thread_lock:
            active_names = list(self.active_threads.keys())
        
        if not active_names:
            return True
        
        self._log(f"🧹 Cleaning up {len(active_names)} threads")
        
        # Request graceful shutdown for all
        for name in active_names:
            self.request_graceful_shutdown(name)
        
        # Wait for completion
        return self.wait_for_cleanup_complete(timeout)
    
    def get_thread_info(self, thread_name: str) -> Optional[ThreadInfo]:
        """Get information about a specific thread"""
        with self.thread_lock:
            return self.active_threads.get(thread_name)
    
    def is_thread_active(self, thread_name: str) -> bool:
        """Check if a thread is active"""
        with self.thread_lock:
            if thread_name not in self.active_threads:
                return False
            
            thread_info = self.active_threads[thread_name]
            return (thread_info.thread.is_alive() and 
                   thread_info.state in [ThreadState.RUNNING, ThreadState.STARTING])