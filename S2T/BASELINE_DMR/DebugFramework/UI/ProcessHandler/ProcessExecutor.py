# ProcessFrameworkWrapper.py
import multiprocessing as mp
import time
import signal
import sys
import os
from typing import Dict, Any, List
import traceback

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

from UI.ProcessHandler.ProcessTypes import ProcessSafeQueue, ProcessMessage, ProcessMessageType

class ProcessFrameworkExecutor:
    """Framework executor that runs in separate process"""
    
    def __init__(self, command_queue, status_queue, framework):
        self.command_queue = command_queue
        self.status_queue = status_queue
        self.framework = framework
        self.running = True
        self.current_execution = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"Framework process received signal {signum}")
        self.running = False
        if self.framework:
            try:
                self.framework.cancel_execution()
            except:
                pass
    
    def send_status(self, message_type: ProcessMessageType, data: Dict[str, Any]):
        """Send status update to UI process"""
        try:
            message = ProcessMessage(
                type=message_type,
                data=data,
                timestamp=time.time(),
                process_id="Framework"
            )
            
            # Put with timeout to avoid blocking
            self.status_queue.put(message.to_dict(), timeout=1.0)
            
        except Exception as e:
            print(f"Error sending status: {e}")
    
    def check_commands(self):
        """Check for commands from UI process"""
        try:
            while True:
                try:
                    command_data = self.command_queue.get_nowait()
                    command = ProcessMessage.from_dict(command_data)
                    self._handle_command(command)
                except:
                    break  # No more commands
        except Exception as e:
            print(f"Error checking commands: {e}")
    
    def _handle_command(self, command: ProcessMessage):
        """Handle command from UI"""
        try:
            if command.type == ProcessMessageType.CANCEL_COMMAND:
                if self.framework:
                    self.framework.cancel_execution()
                self.running = False
                
            elif command.type == ProcessMessageType.END_COMMAND:
                if self.framework:
                    self.framework.end_experiment()
                    
            elif command.type == ProcessMessageType.PAUSE_COMMAND:
                if self.framework:
                    self.framework.halt_execution()
                    
            elif command.type == ProcessMessageType.RESUME_COMMAND:
                if self.framework:
                    self.framework.continue_execution()
                    
            elif command.type == ProcessMessageType.STEP_CONTINUE:
                if self.framework:
                    self.framework.step_continue()
                    
        except Exception as e:
            print(f"Error handling command {command.type}: {e}")
    
    def execute_experiments(self, experiment_data: List[Dict], config_data: Dict):
        """Execute experiments in process"""
        try:
            # Send ready signal
            self.send_status(ProcessMessageType.PROCESS_READY, {
                "message": "Framework process started",
                "experiment_count": len(experiment_data)
            })
            
            # Create Framework with process-safe status reporter
            status_reporter = ProcessStatusReporter(self.send_status)
            self.framework.status_reporter = status_reporter# = Framework(status_reporter=status_reporter)
            
            # Execute each experiment
            for i, exp_data in enumerate(experiment_data):
                if not self.running:
                    break
                
                # Check for commands before each experiment
                self.check_commands()
                
                if not self.running:
                    break
                
                try:
                    # Send experiment start
                    self.send_status(ProcessMessageType.EXPERIMENT_START, {
                        "experiment_index": i,
                        "experiment_name": exp_data.get("experiment_name", f"Experiment_{i}"),
                        "total_experiments": len(experiment_data)
                    })
                    
                    # Execute experiment
                    results = self.framework.RecipeExecutor(
                        data=exp_data,
                        S2T_BOOT_CONFIG=config_data.get("s2t_config"),
                        extmask=exp_data.get("External Mask"),
                        experiment_name=exp_data.get("experiment_name")
                    )
                    
                    # Send experiment complete
                    self.send_status(ProcessMessageType.EXPERIMENT_COMPLETE, {
                        "experiment_index": i,
                        "experiment_name": exp_data.get("experiment_name", f"Experiment_{i}"),
                        "results": results,
                        "success": "CANCELLED" not in results and "FAILED" not in results
                    })
                    
                    # Check for commands after experiment
                    self.check_commands()
                    
                except Exception as e:
                    error_msg = f"Experiment {i} failed: {str(e)}"
                    print(error_msg)
                    traceback.print_exc()
                    
                    self.send_status(ProcessMessageType.PROCESS_ERROR, {
                        "experiment_index": i,
                        "error": error_msg,
                        "traceback": traceback.format_exc()
                    })
            
            # Send completion
            self.send_status(ProcessMessageType.PROCESS_COMPLETE, {
                "message": "All experiments completed",
                "total_executed": len(experiment_data)
            })
            
        except Exception as e:
            error_msg = f"Framework process error: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            self.send_status(ProcessMessageType.PROCESS_ERROR, {
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
        
        finally:
            self.running = False

class ProcessStatusReporter:
    """Status reporter that sends updates through process queue"""
    
    def __init__(self, send_status_func):
        self.send_status = send_status_func
    
    def report_status(self, status_data: Dict[str, Any]):
        """Report status through process communication"""
        # Convert status data to process message
        message_type = self._map_status_to_message_type(status_data.get('type', ''))
        
        self.send_status(message_type, status_data.get('data', {}))
    
    def _map_status_to_message_type(self, status_type: str) -> ProcessMessageType:
        """Map Framework status types to process message types"""
        mapping = {
            'iteration_progress': ProcessMessageType.PROGRESS_UPDATE,
            'iteration_complete': ProcessMessageType.ITERATION_COMPLETE,
            'strategy_progress': ProcessMessageType.STRATEGY_PROGRESS,
            'experiment_start': ProcessMessageType.EXPERIMENT_START,
            'experiment_complete': ProcessMessageType.EXPERIMENT_COMPLETE,
        }
        
        return mapping.get(status_type, ProcessMessageType.STATUS_UPDATE)

def framework_process_main(experiment_data, config_data, command_queue, status_queue, framework = None):
    """Main function for Framework process - no imports needed here"""
    try:
        print("Framework process starting...")
        
        # Create executor
        executor = ProcessFrameworkExecutor(command_queue, status_queue, framework)
        
        # Execute experiments
        executor.execute_experiments(experiment_data, config_data)
        
        print("Framework process completed")
        
    except Exception as e:
        print(f"Framework process error: {e}")
        traceback.print_exc()
        
        # Send error to UI
        try:
            error_message = ProcessMessage(
                type=ProcessMessageType.PROCESS_ERROR,
                data={"error": str(e), "traceback": traceback.format_exc()},
                timestamp=time.time(),
                process_id="Framework"
            )
            status_queue.put(error_message.to_dict(), timeout=1.0)
        except:
            pass
    
    finally:
        print("Framework process exiting...")
