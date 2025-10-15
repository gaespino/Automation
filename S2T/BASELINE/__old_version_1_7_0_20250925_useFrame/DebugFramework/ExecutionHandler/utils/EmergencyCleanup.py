"""
Emergency Cleanup Utilities
Provides standalone cleanup functions that can be called independently
"""

import threading
import time
import psutil
import os
import signal
import sys
from typing import List, Optional

class EmergencyCleanup:
    """Emergency cleanup utilities for Debug Framework"""
    
    @staticmethod
    def kill_all_framework_threads(pattern: str = "Framework") -> int:
        """Kill all threads matching a pattern"""
        killed_count = 0
        
        try:
            # Get all threads in current process
            current_threads = threading.enumerate()
            
            print(f" Found {len(current_threads)} total threads")
            
            framework_threads = [t for t in current_threads if pattern in t.name]
            
            print(f" Found {len(framework_threads)} framework threads")
            
            for thread in framework_threads:
                if thread != threading.current_thread():
                    print(f"🔪 Attempting to stop thread: {thread.name}")
                    # Note: Python doesn't allow direct thread killing
                    # This is more of a marker for cleanup
                    killed_count += 1
            
            return killed_count
            
        except Exception as e:
            print(f" Error killing framework threads: {e}")
            return 0
    
    @staticmethod
    def kill_python_processes_by_name(name_pattern: str = "python") -> int:
        """Kill Python processes matching a pattern"""
        killed_count = 0
        current_pid = os.getpid()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (name_pattern.lower() in proc.info['name'].lower() and 
                        proc.info['pid'] != current_pid):
                        
                        # Check if it's likely a Framework process
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'Framework' in cmdline or 'debug' in cmdline.lower():
                            print(f"🔪 Killing process {proc.info['pid']}: {proc.info['name']}")
                            proc.terminate()
                            killed_count += 1
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return killed_count
            
        except Exception as e:
            print(f" Error killing Python processes: {e}")
            return 0
    
    @staticmethod
    def cleanup_tkinter_resources():
        """Clean up Tkinter resources"""
        try:
            import tkinter as tk
            
            # Try to destroy any remaining Tk instances
            try:
                root = tk._default_root
                if root:
                    print("🧹 Cleaning up default Tkinter root")
                    root.quit()
                    root.destroy()
                    tk._default_root = None
            except:
                pass
            
            # Force garbage collection
            import gc
            gc.collect()
            
            print(" Tkinter resources cleaned up")
            
        except Exception as e:
            print(f" Error cleaning Tkinter resources: {e}")
    
    @staticmethod
    def force_exit_application(exit_code: int = 0):
        """Force exit the application"""
        print(f" Force exiting application with code {exit_code}")
        
        try:
            # Clean up Tkinter first
            EmergencyCleanup.cleanup_tkinter_resources()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Give a moment for cleanup
            time.sleep(0.1)
            
        except:
            pass
        finally:
            # Force exit
            os._exit(exit_code)
    
    @staticmethod
    def emergency_cleanup_all():
        """Perform complete emergency cleanup"""
        print(" EMERGENCY CLEANUP INITIATED")
        
        try:
            # Step 1: Kill framework threads
            thread_count = EmergencyCleanup.kill_all_framework_threads()
            print(f" Processed {thread_count} framework threads")
            
            # Step 2: Clean up Tkinter
            EmergencyCleanup.cleanup_tkinter_resources()
            
            # Step 3: Kill related processes (optional)
            # proc_count = EmergencyCleanup.kill_python_processes_by_name()
            # print(f" Killed {proc_count} related processes")
            
            print(" Emergency cleanup completed")
            
        except Exception as e:
            print(f" Emergency cleanup error: {e}")
        
        # Give a moment for cleanup to complete
        time.sleep(0.5)

def emergency_cleanup_standalone():
    """Standalone emergency cleanup function"""
    EmergencyCleanup.emergency_cleanup_all()

if __name__ == "__main__":
    """Allow running as standalone script"""
    print("Running emergency cleanup...")
    emergency_cleanup_standalone()
    print("Emergency cleanup completed")