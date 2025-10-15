"""
Integration module for Thread Manager with Debug Framework Control Panel
"""

import threading
import time
from typing import Optional
import os
import sys

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)


from ExecutionHandler.utils.ThreadsManager import FrameworkThreadManager, ThreadState
from ExecutionHandler.utils.EmergencyCleanup import EmergencyCleanup

class ControlPanelThreadIntegration:
    """Integration class for Control Panel with Thread Manager"""
    
    def __init__(self, control_panel):
        self.control_panel = control_panel
        self.thread_manager = FrameworkThreadManager(
            ui_controller=control_panel,
            logger=control_panel.log_status if hasattr(control_panel, 'log_status') else print
        )
        
        # Integration state
        self.current_framework_thread_name: Optional[str] = None
        self.cleanup_in_progress = False
        
        # Replace control panel methods
        self._integrate_with_control_panel()
    
    def _integrate_with_control_panel(self):
        """Integrate thread manager with control panel methods"""
        # Store original methods
        self.control_panel._original_start_tests_thread = self.control_panel.start_tests_thread
        self.control_panel._original_cancel_tests = self.control_panel.cancel_tests
        self.control_panel._original_on_closing = self.control_panel.on_closing
        
        # Replace with enhanced versions
        self.control_panel.start_tests_thread = self.enhanced_start_tests_thread
        self.control_panel.cancel_tests = self.enhanced_cancel_tests
        self.control_panel.on_closing = self.enhanced_on_closing
        
        # Add emergency cleanup method
        self.control_panel.emergency_cleanup = self.emergency_cleanup
    
    def enhanced_start_tests_thread(self):
        """Enhanced start tests with thread management"""
        if self.cleanup_in_progress:
            self.control_panel.log_status("⚠️ Cleanup in progress - please wait")
            return
        
        # Check if any threads are still active
        if self.thread_manager.active_threads:
            self.control_panel.log_status("⚠️ Previous threads still active - cleaning up first")
            self.enhanced_cancel_tests()
            return
        
        # Prepare for new execution
        if self.control_panel.Framework:
            if not self.control_panel.Framework._prepare_for_new_execution():
                self.control_panel.log_status("❌ Failed to prepare framework for execution")
                return
        
        # Create thread name
        thread_name = f"FrameworkExecution_{int(time.time())}"
        
        # Prepare thread function
        def managed_thread_function():
            try:
                # Call original thread function
                self.control_panel._original_start_tests_thread()
            except Exception as e:
                self.control_panel.log_status(f"❌ Thread execution error: {e}")
            finally:
                # Thread is completing
                self.control_panel.log_status("🏁 Framework thread completing")
        
        # Create and register thread
        framework_thread = threading.Thread(
            target=managed_thread_function,
            name=thread_name,
            daemon=False
        )
        
        # Register with thread manager
        self.thread_manager.register_thread(
            thread=framework_thread,
            name=thread_name,
            metadata={
                'type': 'framework_execution',
                'start_method': 'control_panel',
                'experiments_count': getattr(self.control_panel, 'total_experiments', 0)
            }
        )
        
        # Add cleanup callbacks
        self.thread_manager.add_cleanup_callback(
            thread_name, 
            lambda: self._cleanup_framework_state()
        )
        
        self.thread_manager.add_cleanup_callback(
            thread_name,
            lambda: self._cleanup_execution_state()
        )
        
        # Start managed thread
        if self.thread_manager.start_managed_thread(thread_name):
            self.current_framework_thread_name = thread_name
            self.control_panel.thread_active = True
            self.control_panel.framework_thread = framework_thread
            
            self.control_panel.log_status(f"🚀 Started managed framework thread: {thread_name}")
        else:
            self.control_panel.log_status("❌ Failed to start managed thread")
    
    def enhanced_cancel_tests(self):
        """Enhanced cancel with thread management"""
        if self.cleanup_in_progress:
            self.control_panel.log_status("⚠️ Cleanup already in progress")
            return
        
        self.cleanup_in_progress = True
        
        try:
            self.control_panel.log_status("🚫 Enhanced cancel initiated")
            
            # Step 1: Issue cancel to Framework
            if self.control_panel.Framework:
                self.control_panel.Framework.cancel_execution()
            
            # Step 2: Request graceful shutdown of current thread
            if self.current_framework_thread_name:
                success = self.thread_manager.request_graceful_shutdown(
                    self.current_framework_thread_name,
                    timeout=8.0
                )
                
                if success:
                    self.control_panel.log_status("✅ Graceful shutdown requested")
                else:
                    self.control_panel.log_status("⚠️ Graceful shutdown failed - using emergency cleanup")
                    self.emergency_cleanup()
            
            # Step 3: Update UI
            self._update_ui_for_cancel()
            
        except Exception as e:
            self.control_panel.log_status(f"❌ Enhanced cancel error: {e}")
            self.emergency_cleanup()
        finally:
            # Schedule cleanup completion check
            self.control_panel.root.after(1000, self._check_cleanup_completion)
    
    def enhanced_on_closing(self):
        """Enhanced closing with thread management"""
        try:
            self.control_panel.log_status("🚪 Enhanced application closing initiated")
            
            # Step 1: Cancel any running operations
            if self.thread_manager.active_threads:
                self.control_panel.log_status("🛑 Stopping active threads...")
                
                # Request cleanup of all threads
                cleanup_success = self.thread_manager.cleanup_all(timeout=10.0)
                
                if not cleanup_success:
                    self.control_panel.log_status("⚠️ Normal cleanup failed - using emergency cleanup")
                    self.emergency_cleanup()
            
            # Step 2: Call original cleanup
            try:
                self.control_panel._original_on_closing()
            except Exception as e:
                self.control_panel.log_status(f"⚠️ Original cleanup error: {e}")
                # Continue with emergency cleanup
                EmergencyCleanup.emergency_cleanup_all()
                
        except Exception as e:
            print(f"❌ Enhanced closing error: {e}")
            # Last resort
            EmergencyCleanup.force_exit_application(1)
    
    def emergency_cleanup(self):
        """Emergency cleanup method"""
        try:
            self.control_panel.log_status("🚨 EMERGENCY CLEANUP INITIATED")
            
            # Step 1: Emergency shutdown all managed threads
            self.thread_manager.emergency_shutdown_all()
            
            # Step 2: Framework-specific cleanup
            self._emergency_framework_cleanup()
            
            # Step 3: System-wide emergency cleanup
            EmergencyCleanup.emergency_cleanup_all()
            
            # Step 4: Reset UI
            self._reset_ui_after_emergency()
            
            self.control_panel.log_status("✅ Emergency cleanup completed")
            
        except Exception as e:
            print(f"❌ Emergency cleanup error: {e}")
        finally:
            self.cleanup_in_progress = False
            self.current_framework_thread_name = None
    
    def _cleanup_framework_state(self):
        """Clean up Framework state"""
        try:
            if self.control_panel.Framework:
                if hasattr(self.control_panel.Framework, '_finalize_execution'):
                    self.control_panel.Framework._finalize_execution("thread_manager_cleanup")
                
                if hasattr(self.control_panel.Framework, 'status_manager'):
                    self.control_panel.Framework.status_manager.disable()
        except Exception as e:
            print(f"Framework state cleanup error: {e}")
    
    def _cleanup_execution_state(self):
        """Clean up execution state"""
        try:
            if hasattr(self.control_panel, 'execution_state'):
                self.control_panel.execution_state.finalize_execution("thread_manager_cleanup")
        except Exception as e:
            print(f"Execution state cleanup error: {e}")
    
    def _emergency_framework_cleanup(self):
        """Emergency Framework cleanup"""
        try:
            if self.control_panel.Framework:
                # Force disable status manager
                if hasattr(self.control_panel.Framework, 'status_manager'):
                    self.control_panel.Framework.status_manager.disable()
                
                # Clear Framework references
                self.control_panel.Framework._status_reporter = None
                
                # Reset Framework state
                if hasattr(self.control_panel.Framework, '_reset_execution_state'):
                    self.control_panel.Framework._reset_execution_state()
        except Exception as e:
            print(f"Emergency Framework cleanup error: {e}")
    
    def _update_ui_for_cancel(self):
        """Update UI for cancellation"""
        try:
            self.control_panel.status_label.configure(text=" Cancelling ", bg="red", fg="white")
            self.control_panel.cancel_button.configure(state='disabled', text="Cancelling...")
        except Exception as e:
            print(f"UI update error: {e}")
    
    def _reset_ui_after_emergency(self):
        """Reset UI after emergency cleanup"""
        try:
            self.control_panel.thread_active = False
            self.control_panel.framework_thread = None
            
            self.control_panel.run_button.configure(state='normal')
            self.control_panel.cancel_button.configure(state='disabled', text="Cancel")
            self.control_panel.hold_button.configure(state='disabled')
            self.control_panel.end_button.configure(state='disabled')
            
            self.control_panel.root.after(2000, lambda: 
                self.control_panel.status_label.configure(text=" Ready ", bg="white", fg="black")
            )
        except Exception as e:
            print(f"UI reset error: {e}")
    
    def _check_cleanup_completion(self):
        """Check if cleanup is complete"""
        try:
            if self.thread_manager.is_cleanup_complete():
                self.cleanup_in_progress = False
                self.current_framework_thread_name = None
                self.control_panel.log_status("✅ All cleanup operations completed")
                
                # Reset UI
                self._reset_ui_after_emergency()
            else:
                # Check again in 1 second
                self.control_panel.root.after(1000, self._check_cleanup_completion)
        except Exception as e:
            print(f"Cleanup completion check error: {e}")
    
    def get_status(self) -> dict:
        """Get comprehensive status"""
        return {
            'thread_manager_status': self.thread_manager.get_thread_status(),
            'cleanup_in_progress': self.cleanup_in_progress,
            'current_thread': self.current_framework_thread_name,
            'active_thread_count': len(self.thread_manager.active_threads)
        }
    
    def print_status(self):
        """Print comprehensive status"""
        print("\n" + "="*60)
        print("CONTROL PANEL THREAD INTEGRATION STATUS")
        print("="*60)
        
        status = self.get_status()
        
        print(f"Cleanup in Progress: {status['cleanup_in_progress']}")
        print(f"Current Thread: {status['current_thread']}")
        print(f"Active Threads: {status['active_thread_count']}")
        
        if status['thread_manager_status']:
            print("\nThread Manager Status:")
            self.thread_manager.print_thread_status()
        
        print("="*60)