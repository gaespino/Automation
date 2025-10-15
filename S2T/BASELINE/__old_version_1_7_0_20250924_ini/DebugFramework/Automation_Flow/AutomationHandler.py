import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from abc import ABC, abstractmethod
import threading
import time
from datetime import datetime
import queue

# Setup paths for current and parent directories, and add parent directory to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

# Test Variables
def test_runStatusHistory(ID):
    if '1' in ID:
        FAIL = True
    elif '2' in ID:
        FAIL = False    
    elif '3' in ID:
        FAIL = True
    else:
        FAIL = False    
    return ['FAIL' if FAIL else 'PASS']

# Import FileHandler module for loading JSON files
import FileHandler as fh  # Assuming FileHandler contains functions for loading JSON

# Default configuration for System-to-Tester communication
S2T_CONFIGURATION = {
    'AFTER_MRC_POST': 0xbf000000,
    'EFI_POST': 0xef0000ff,
    'LINUX_POST': 0x58000000,
    'BOOTSCRIPT_RETRY_TIMES': 3,
    'BOOTSCRIPT_RETRY_DELAY': 60,
    'MRC_POSTCODE_WT': 30,
    'EFI_POSTCODE_WT': 60,
    'MRC_POSTCODE_CHECK_COUNT': 5,
    'EFI_POSTCODE_CHECK_COUNT': 10,
    'BOOT_STOP_POSTCODE': 0x0,
    'BOOT_POSTCODE_WT': 30,
    'BOOT_POSTCODE_CHECK_COUNT': 1
}

class FrameworkExternalAPI:
    """External API interface for automation systems"""
    
    def __init__(self, framework):
        self.framework = framework
    
    def start_experiment_step_by_step(self, recipe_data, **kwargs):
        """Start experiment in step-by-step mode"""
        try:
            self.framework.enable_step_by_step_mode()
            
            # Start execution in background thread
            execution_thread = threading.Thread(
                target=self.framework.RecipeExecutor,
                args=(recipe_data,),
                kwargs={**kwargs, 'step_by_step': True}
            )
            execution_thread.daemon = True
            execution_thread.start()
            
            return {
                'success': True,
                'message': 'Experiment started in step-by-step mode',
                'state': self.framework.get_execution_state()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_current_state(self):
        """Get current execution state"""
        return self.framework.get_execution_state()
    
    def continue_next_iteration(self):
        """Continue to next iteration"""
        success = self.framework.step_continue()
        return {
            'success': success,
            'message': 'Continue command sent' if success else 'Failed to send continue command',
            'state': self.framework.get_execution_state()
        }
    
    def end_current_experiment(self):
        """End current experiment"""
        success = self.framework.end_experiment()
        return {
            'success': success,
            'message': 'End command sent' if success else 'Failed to send end command',
            'state': self.framework.get_execution_state()
        }
    
    def cancel_experiment(self):
        """Cancel experiment immediately"""
        self.framework.cancel_execution()
        return {
            'success': True,
            'message': 'Cancel command sent - experiment will stop immediately',
            'state': self.framework.get_execution_state()
        }
    
    def get_iteration_statistics(self):
        """Get detailed statistics for decision making"""
        state = self.framework.get_execution_state()
        stats = state.get('current_stats', {})
        
        return {
            'total_completed': stats.get('total_completed', 0),
            'pass_rate': stats.get('pass_rate', 0.0),
            'fail_rate': stats.get('fail_rate', 0.0),
            'recent_trend': self._analyze_recent_trend(state.get('latest_results', [])),
            'recommendation': self._get_recommendation(stats),
            'end_requested': state.get('end_requested', False),
            'sufficient_data': self._has_sufficient_data(stats)
        }
    
    def _has_sufficient_data(self, stats):
        """Determine if we have sufficient data for decision making"""
        total = stats.get('total_completed', 0)
        pass_rate = stats.get('pass_rate', 0.0)
        
        if total >= 10:
            return True
        elif total >= 5:
            if pass_rate >= 95 or pass_rate <= 20:
                return True
        
        return False
    
    def _analyze_recent_trend(self, recent_results):
        """Analyze recent test trend"""
        if len(recent_results) < 3:
            return "insufficient_data"
        
        recent_failures = sum(1 for r in recent_results[-3:] if r['status'] == 'FAIL')
        
        if recent_failures >= 2:
            return "declining"
        elif recent_failures == 0:
            return "stable"
        else:
            return "mixed"
    
    def _get_recommendation(self, stats):
        """Get recommendation based on current statistics"""
        pass_rate = stats.get('pass_rate', 0.0)
        total = stats.get('total_completed', 0)
        
        if total < 5:
            return "continue"
        elif self._has_sufficient_data(stats):
            if pass_rate >= 90:
                return "sufficient_data_good"
            elif pass_rate <= 30:
                return "sufficient_data_poor"
            else:
                return "continue"
        elif pass_rate >= 95:
            return "trending_excellent"
        elif pass_rate <= 20:
            return "trending_poor"
        else:
            return "continue"

class FlowInstance(ABC):
    """
    Enhanced base class representing a flow instance with Framework step-by-step integration.
    """

    def __init__(self, ID, Name, Framework, Experiment, outputNodeMap, logger=None):
        self.ID = ID
        self.Name = Name
        self.Framework = Framework
        self.Experiment = Experiment
        self.outputNodeMap = outputNodeMap
        self.outputPort = 0  # Default output port
        self.runStatusHistory = []  # History of run statuses
        self.execution_stats = {}  # Detailed execution statistics
        self.framework_api = None  # Will be set by FlowTestExecutor
        
        if not logger: 
            logger = print
        self.logger = logger

        # Initialize system-to-tester configuration
        self.S2T_CONFIG = Framework.system_2_tester_default() if Framework else S2T_CONFIGURATION

    def run_experiment(self):
        """
        Executes the experiment using Framework's step-by-step mode with real-time decision making.
        """
        self.logger(f"Running Experiment: {self.Name} (ID: {self.ID})")
        
        if self.Framework is not None and self.framework_api is not None:
            # Use Framework with step-by-step mode
            self._run_framework_experiment()
        else:
            # Fallback to test mode
            self.runStatusHistory = test_runStatusHistory(self.ID)
            self.logger(f"Test mode result: {self.runStatusHistory}")
            
        self.set_output_port()

    def _run_framework_experiment(self):
        """
        Run experiment using Framework's step-by-step mode with intelligent decision making.
        """
        try:
            # Start experiment in step-by-step mode
            experiment_name = f"{self.Name}_{self.ID}"
            result = self.framework_api.start_experiment_step_by_step(
                self.Experiment, 
                experiment_name=experiment_name,
                S2T_BOOT_CONFIG=self.S2T_CONFIG
            )
            
            if not result['success']:
                self.logger(f"Failed to start experiment: {result.get('error', 'Unknown error')}")
                self.runStatusHistory = ['FAILED']
                return

            self.logger(f"Experiment started successfully in step-by-step mode")
            
            # Monitor and control experiment execution
            self._monitor_step_by_step_execution()
            
        except Exception as e:
            self.logger(f"Error running Framework experiment: {e}")
            self.runStatusHistory = ['FAILED']

    def _monitor_step_by_step_execution(self):
        """
        Monitor step-by-step execution and make decisions based on results.
        """
        iteration_count = 0
        max_iterations = self._get_max_iterations()
        
        while True:
            state = self.framework_api.get_current_state()
            
            if not state['is_running']:
                self.logger(f"Experiment completed. Final state: {state}")
                break
            
            if state['waiting_for_command']:
                iteration_count += 1
                stats = self.framework_api.get_iteration_statistics()
                
                self.logger(f"Iteration {state['current_iteration']} completed:")
                self.logger(f"  Pass rate: {stats['pass_rate']}%")
                self.logger(f"  Total completed: {stats['total_completed']}")
                self.logger(f"  Recommendation: {stats['recommendation']}")
                
                # Store current statistics
                self.execution_stats = stats
                
                # Make decision based on node-specific logic
                decision = self._make_iteration_decision(stats, iteration_count, max_iterations)
                
                if decision == 'continue':
                    self.logger(f"Decision: Continue to next iteration")
                    continue_result = self.framework_api.continue_next_iteration()
                    if not continue_result['success']:
                        self.logger(f"Failed to continue: {continue_result['message']}")
                        break
                elif decision == 'end':
                    self.logger(f"Decision: End experiment early")
                    end_result = self.framework_api.end_current_experiment()
                    if end_result['success']:
                        self.logger(f"Experiment ended successfully")
                    break
                else:
                    self.logger(f"Decision: Cancel experiment")
                    self.framework_api.cancel_experiment()
                    break
            
            time.sleep(2)  # Check every 2 seconds
        
        # Extract final results
        self._extract_final_results()

    def _get_max_iterations(self):
        """
        Get maximum iterations based on experiment type.
        Override in subclasses for specific limits.
        """
        test_type = self.Experiment.get('Test Type', 'Loops')
        
        if test_type == 'Loops':
            return self.Experiment.get('Loops', 10)
        elif test_type == 'Sweep':
            start = self.Experiment.get('Start', 0)
            end = self.Experiment.get('End', 10)
            step = self.Experiment.get('Steps', 1)
            return max(1, int((end - start) / step) + 1)
        elif test_type == 'Shmoo':
            return 50  # Default estimate for shmoo
        else:
            return 20  # Default maximum

    @abstractmethod
    def _make_iteration_decision(self, stats, iteration_count, max_iterations):
        """
        Abstract method for making decisions after each iteration.
        Must return 'continue', 'end', or 'cancel'.
        
        Parameters:
        - stats: Current execution statistics
        - iteration_count: Current iteration number
        - max_iterations: Maximum allowed iterations
        """
        pass

    def _extract_final_results(self):
        """
        Extract final results from the completed experiment.
        """
        try:
            final_state = self.framework_api.get_current_state()
            final_stats = self.framework_api.get_iteration_statistics()
            
            # Build status history based on final statistics
            total_completed = final_stats.get('total_completed', 0)
            pass_count = int(total_completed * final_stats.get('pass_rate', 0) / 100)
            fail_count = total_completed - pass_count
            
            # Create status history
            self.runStatusHistory = (['PASS'] * pass_count) + (['FAIL'] * fail_count)
            
            # Store detailed stats
            self.execution_stats = final_stats
            
            self.logger(f"Final Results - Total: {total_completed}, Pass: {pass_count}, Fail: {fail_count}")
            
        except Exception as e:
            self.logger(f"Error extracting final results: {e}")
            self.runStatusHistory = ['FAILED']

    @abstractmethod
    def set_output_port(self):
        """
        Abstract method for setting the output port based on the run status.
        Subclasses must implement this method to determine specific output behavior.
        """
        pass

    def get_next_node(self):
        """
        Returns the next node to execute based on the output port determined in `set_output_port`.
        """
        if self.outputNodeMap: 
            try:
                nextNode = self.outputNodeMap[self.outputPort]
                self.logger(f"Next node: {nextNode.Name} (Port: {self.outputPort})")
                return nextNode
            except KeyError as e:
                self.logger(f"Output Port Error: No handler found for port {self.outputPort}. Exception: {e}")
        return None

    def get_execution_summary(self):
        """
        Get a summary of the execution results.
        """
        return {
            'node_id': self.ID,
            'node_name': self.Name,
            'status_history': self.runStatusHistory,
            'execution_stats': self.execution_stats,
            'output_port': self.outputPort,
            'total_tests': len(self.runStatusHistory),
            'pass_count': self.runStatusHistory.count('PASS'),
            'fail_count': self.runStatusHistory.count('FAIL')
        }

class SingleFailFlowInstance(FlowInstance):
    """
    Flow instance that stops on first failure and routes based on any failure occurrence.
    """
    
    def _make_iteration_decision(self, stats, iteration_count, max_iterations):
        """
        Stop immediately if any failure is detected.
        """
        if stats['total_completed'] >= 1:
            if stats['fail_rate'] > 0:
                return 'end'  # Stop on first failure
            elif stats['total_completed'] >= 5 and stats['pass_rate'] == 100:
                return 'end'  # Stop early if we have good confidence
        
        if iteration_count >= max_iterations:
            return 'end'
        
        return 'continue'

    def set_output_port(self):
        """
        Returns 0 if any failure found, otherwise 1.
        """
        self.outputPort = 0 if 'FAIL' in self.runStatusHistory else 1

class AllFailFlowInstance(FlowInstance):
    """
    Flow instance that requires all tests to fail for failure path.
    """
    
    def _make_iteration_decision(self, stats, iteration_count, max_iterations):
        """
        Continue until we have enough data to determine if all tests fail.
        """
        if stats['total_completed'] >= 3:
            if stats['pass_rate'] > 0:
                return 'end'  # We have passes, so not all fail
            elif stats['total_completed'] >= 10:
                return 'end'  # Enough failures to be confident
        
        if iteration_count >= max_iterations:
            return 'end'
        
        return 'continue'

    def set_output_port(self):
        """
        Returns 0 if all tests failed, otherwise 1.
        """
        has_failures = 'FAIL' in self.runStatusHistory
        all_failed = len(set(self.runStatusHistory)) <= 1 and has_failures
        self.outputPort = 0 if all_failed else 1

class MajorityFailFlowInstance(FlowInstance):
    """
    Flow instance that routes based on majority failure rate.
    """
    
    def _make_iteration_decision(self, stats, iteration_count, max_iterations):
        """
        Continue until we have statistical confidence in the failure rate.
        """
        if stats['total_completed'] >= 10:
            # We have enough data for statistical confidence
            if abs(stats['fail_rate'] - 50) > 20:  # Clear majority either way
                return 'end'
        elif stats['total_completed'] >= 20:
            return 'end'  # Maximum for statistical analysis
        
        if iteration_count >= max_iterations:
            return 'end'
        
        return 'continue'

    def set_output_port(self):
        """
        Returns 0 if majority of tests failed (>=50%), otherwise 1.
        """
        fail_rate = self.runStatusHistory.count('FAIL') / len(self.runStatusHistory) if self.runStatusHistory else 0
        self.outputPort = 0 if fail_rate >= 0.5 else 1

class AdaptiveFlowInstance(FlowInstance):
    """
    Advanced flow instance that adapts based on trends and confidence levels.
    """
    
    def _make_iteration_decision(self, stats, iteration_count, max_iterations):
        """
        Make intelligent decisions based on trends and confidence.
        """
        total = stats['total_completed']
        
        # Early stopping conditions
        if total >= 5:
            if stats['pass_rate'] >= 95:
                return 'end'  # Very high pass rate, confident in success
            elif stats['pass_rate'] <= 5:
                return 'end'  # Very high fail rate, confident in failure
        
        # Medium confidence stopping
        if total >= 15:
            if stats['pass_rate'] >= 80 or stats['pass_rate'] <= 20:
                return 'end'  # Clear trend established
        
        # Maximum iterations reached
        if iteration_count >= max_iterations:
            return 'end'
        
        # Check for sufficient data based on recommendation
        if stats['recommendation'] in ['sufficient_data_good', 'sufficient_data_poor']:
            return 'end'
        
        return 'continue'

    def set_output_port(self):
        """
        Intelligent routing based on execution statistics and trends.
        """
        if not self.execution_stats:
            # Fallback to simple majority
            fail_rate = self.runStatusHistory.count('FAIL') / len(self.runStatusHistory) if self.runStatusHistory else 0
            self.outputPort = 0 if fail_rate >= 0.5 else 1
            return
        
        pass_rate = self.execution_stats.get('pass_rate', 0)
        total_tests = self.execution_stats.get('total_completed', 0)
        
        # Route based on confidence and results
        if total_tests >= 10:
            if pass_rate >= 70:
                self.outputPort = 1  # Success path
            else:
                self.outputPort = 0  # Failure path
        else:
            # Not enough data, use simple majority
            self.outputPort = 0 if pass_rate < 50 else 1

class FlowTestExecutor:
    """
    Enhanced executor with Framework API integration and comprehensive logging.
    """

    def __init__(self, root, framework=None):
        self.root = root
        self.framework = framework
        self.framework_api = None
        self.execution_log = []
        self.start_time = None
        
        # Initialize Framework API if available
        if framework:
            self.framework_api = FrameworkExternalAPI(framework)
            
            # Set API reference for all nodes
            self._set_api_for_all_nodes(root)

    def _set_api_for_all_nodes(self, node, visited=None):
        """
        Recursively set Framework API reference for all nodes in the flow.
        """
        if visited is None:
            visited = set()
        
        if node.ID in visited:
            return
        
        visited.add(node.ID)
        node.framework_api = self.framework_api
        
        # Recursively set for connected nodes
        for next_node in node.outputNodeMap.values():
            self._set_api_for_all_nodes(next_node, visited)

    def execute(self):
        """
        Execute the flow with comprehensive logging and error handling.
        """
        self.start_time = datetime.now()
        self.log_execution("Flow execution started")
        
        try:
            current_node = self.root
            node_count = 0
            
            while current_node is not None and node_count < 50:  # Safety limit
                node_count += 1
                
                self.log_execution(f"Executing node: {current_node.Name} (ID: {current_node.ID})")
                
                # Execute the current node
                start_time = time.time()
                current_node.run_experiment()
                execution_time = time.time() - start_time
                
                # Log execution results
                summary = current_node.get_execution_summary()
                self.log_execution(f"Node completed in {execution_time:.1f}s: {summary}")
                
                # Get next node
                next_node = current_node.get_next_node()
                
                if next_node:
                    self.log_execution(f"Moving to next node: {next_node.Name}")
                else:
                    self.log_execution("Flow execution completed - no more nodes")
                
                current_node = next_node
            
            if node_count >= 50:
                self.log_execution("WARNING: Flow execution stopped due to safety limit (50 nodes)")
                
        except Exception as e:
            self.log_execution(f"ERROR: Flow execution failed: {e}")
            raise
        finally:
            total_time = (datetime.now() - self.start_time).total_seconds()
            self.log_execution(f"Flow execution finished. Total time: {total_time:.1f}s")

    def log_execution(self, message):
        """
        Log execution messages with timestamps.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_log.append(log_entry)
        print(log_entry)

    def get_execution_report(self):
        """
        Generate a comprehensive execution report.
        """
        return {
            'start_time': self.start_time,
            'execution_log': self.execution_log,
            'total_time': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }

class FlowTestBuilder:
    """
    Enhanced builder with Framework integration and better error handling.
    """

    def __init__(self, structureFilePath: str, flowsFilePath: str, iniFilePath: str, Framework=None, logger=None):
        if not logger: 
            logger = print
        self.logger = logger

        self.structureFilePath = structureFilePath
        self.flowsFilePath = flowsFilePath
        self.iniFilePath = iniFilePath
        self.Framework = Framework

        try:
            # Load configuration files
            self.structureFile = fh.load_json(structureFilePath)
            self.flowsFile = fh.load_json(flowsFilePath)
            self.initFile = fh.ini_to_dict_with_types(iniFilePath, convert_key_underscores=True)
            
            self.logger(f"Loaded structure file: {len(self.structureFile)} nodes")
            self.logger(f"Loaded flows file: {len(self.flowsFile)} flows")
            self.logger(f"Loaded ini file: {len(self.initFile)} configurations")
            
        except Exception as e:
            self.logger(f"Error loading configuration files: {e}")
            raise

        # Dictionary to store built nodes
        self.builtNodes = {}

        # UI configuration
        self.status_colors = {'default': 'gray', 'running': 'blue', 'success': 'green', 'failed': 'red'}
        self.connection_colors = ['orange', 'purple', 'yellow', 'brown']
        self.node_width, self.node_height = 70, 120
        self.square_size = 15

    def build_flow(self, rootID):
        """
        Build and return an enhanced executor for the flow starting at rootID.
        """
        try:
            root = self.__build_instance(rootID)
            executor = FlowTestExecutor(root=root, framework=self.Framework)
            
            self.logger(f"Flow built successfully with root: {rootID}")
            self.logger(f"Total nodes in flow: {len(self.builtNodes)}")
            
            return executor
            
        except Exception as e:
            self.logger(f"Error building flow: {e}")
            raise

    def __build_instance(self, flowKey):
        """
        Enhanced instance building with better error handling.
        """
        if flowKey in self.builtNodes:
            return self.builtNodes[flowKey]

        try:
            nodeConfig = self.structureFile[flowKey]
            ExperimentInfo = self.flowsFile[nodeConfig["flow"]]
            ExperimentIni = self.initFile.get(nodeConfig["flow"], {})
            
            # Merge experiment configuration
            ExperimentInfo = {**ExperimentInfo, **ExperimentIni}
            
            # Get flow class
            flowClass = globals()[nodeConfig["instanceType"]]
            
            # Build output node mappings
            outputNodeMap = self.__build_following_nodes(nodeConfig.get("outputNodeMap", {}))
            
            # Create node instance
            node = flowClass(
                ID=flowKey,
                Name=nodeConfig["name"],
                Framework=self.Framework,
                Experiment=ExperimentInfo,
                outputNodeMap=outputNodeMap,
                logger=self.logger
            )
            
            self.builtNodes[flowKey] = node
            self.logger(f"Built node: {flowKey} ({nodeConfig['name']})")
            
            return node
            
        except Exception as e:
            self.logger(f"Error building instance {flowKey}: {e}")
            raise

    def __build_following_nodes(self, nodeMap: dict):
        """
        Recursively builds and returns mappings for the output nodes.
        """
        outputNodeMap = {}
        if nodeMap:
            for port, nodeKey in nodeMap.items():
                outputNodeMap[int(port)] = self.__build_instance(nodeKey)
        return outputNodeMap

class FlowProgressInterface:
    """
    Advanced UI for flow execution with node visualization and real-time monitoring.
    """
    
    def __init__(self, framework=None):
        self.framework = framework
        self.builder = None
        self.executor = None
        self.root_node = None
        
        # File paths
        self.flow_folder = None
        self.structure_path = None
        self.flows_path = None
        self.ini_path = None
        
        # Default file names
        self.default_files = {
            'structure': 'FrameworkAutomationStructure.json',
            'flows': 'FrameworkAutomationFlows.json',
            'ini': 'FrameworkAutomationInit.ini'
        }
        
        # UI State
        self.current_node = None
        self.completed_nodes = set()
        self.failed_nodes = set()
        self.node_widgets = {}
        self.connection_lines = {}
        
        # Statistics tracking
        self.start_time = None
        self.total_nodes = 0
        self.completed_count = 0
        self.failed_count = 0
        
        # Threading
        self.update_queue = queue.Queue()
        self.execution_thread = None
        self.is_running = False
        
        # Create main window
        self.setup_main_window()
        self.create_widgets()
        
        # Start update loop
        self.root.after(100, self.process_updates)

    def setup_main_window(self):
        """Setup the main window with proper styling."""
        self.root = tk.Tk()
        self.root.title("Automation Flow Execution Monitor")
        self.root.geometry("1600x900")
        self.root.minsize(1200, 700)
        
        # Configure styles
        self.setup_styles()

    def setup_styles(self):
        """Configure ttk styles for consistent appearance."""
        self.style = ttk.Style()
        self.style.theme_use('alt')  # Match your control panel theme
        
        # Node status colors
        self.node_colors = {
            'idle': '#E0E0E0',
            'current': '#2196F3',
            'completed': '#4CAF50',
            'failed': '#F44336',
            'skipped': '#FF9800'
        }
        
        # Connection colors
        self.connection_colors = {
            0: '#F44336',  # Red for failure path
            1: '#4CAF50',  # Green for success path
            2: '#FF9800',  # Orange for alternative path
            3: '#9C27B0'   # Purple for special path
        }

    def create_widgets(self):
        """Create the main UI layout."""
        # Main horizontal container
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side - Flow diagram
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=3)
        
        # Right side - Status and logs
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=1)
        
        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        """Create the flow diagram panel."""
        # Title and controls
        title_frame = ttk.Frame(self.left_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(title_frame, text="Automation Flow Execution", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Control buttons
        controls_frame = ttk.Frame(title_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        self.start_button = ttk.Button(controls_frame, text="Start Flow", 
                                     command=self.start_execution, state=tk.DISABLED)
        self.start_button.pack(side=tk.RIGHT, padx=2)
        
        self.pause_button = ttk.Button(controls_frame, text="Pause", 
                                     command=self.pause_execution, state=tk.DISABLED)
        self.pause_button.pack(side=tk.RIGHT, padx=2)
        
        self.stop_button = ttk.Button(controls_frame, text="Stop", 
                                    command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=2)
        
        # File selection frame
        file_frame = ttk.Frame(self.left_frame)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="Flow Folder:", width=12).pack(side=tk.LEFT)
        
        self.folder_entry = ttk.Entry(file_frame, state='readonly')
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.browse_button = ttk.Button(file_frame, text="Browse", 
                                      command=self.browse_flow_folder)
        self.browse_button.pack(side=tk.RIGHT)
        
        # File status frame
        self.file_status_frame = ttk.Frame(self.left_frame)
        self.file_status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Initially hidden, will be shown after folder selection
        self.create_file_status_widgets()
        
        # Progress bar
        progress_frame = ttk.Frame(self.left_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(progress_frame, text="Overall Progress:").pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.RIGHT)
        
        # Separator
        ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        # Canvas for flow diagram
        canvas_frame = ttk.Frame(self.left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind mouse events for canvas interaction
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # Initial message on canvas
        self.show_canvas_message("Please select a flow folder to begin")

    def create_file_status_widgets(self):
        """Create file status indicators."""
        # File status labels (initially hidden)
        self.file_labels = {}
        
        for file_type, filename in self.default_files.items():
            frame = ttk.Frame(self.file_status_frame)
            
            # Status indicator
            status_label = ttk.Label(frame, text="●", foreground="red", font=("Arial", 12))
            status_label.pack(side=tk.LEFT)
            
            # File name
            name_label = ttk.Label(frame, text=filename, width=35)
            name_label.pack(side=tk.LEFT, padx=(5, 0))
            
            # Browse individual file button (initially hidden)
            browse_btn = ttk.Button(frame, text="Browse", 
                                  command=lambda ft=file_type: self.browse_individual_file(ft),
                                  state=tk.DISABLED)
            browse_btn.pack(side=tk.RIGHT)
            
            self.file_labels[file_type] = {
                'frame': frame,
                'status': status_label,
                'name': name_label,
                'browse': browse_btn
            }

    def browse_flow_folder(self):
        """Browse for flow folder containing configuration files."""
        folder_path = filedialog.askdirectory(title="Select Flow Configuration Folder")
        
        if not folder_path:
            return
        
        self.flow_folder = folder_path
        self.folder_entry.configure(state='normal')
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_path)
        self.folder_entry.configure(state='readonly')
        
        self.log_message(f"Selected flow folder: {folder_path}")
        
        # Check for default files
        self.check_default_files()

    def check_default_files(self):
        """Check for default configuration files in the selected folder."""
        if not self.flow_folder:
            return
        
        found_files = {}
        missing_files = []
        
        # Show file status frame
        self.file_status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for file_type, filename in self.default_files.items():
            file_path = os.path.join(self.flow_folder, filename)
            frame_info = self.file_labels[file_type]
            
            # Show the frame
            frame_info['frame'].pack(fill=tk.X, pady=2)
            
            if os.path.exists(file_path):
                # File found
                found_files[file_type] = file_path
                frame_info['status'].configure(foreground="green")
                frame_info['browse'].configure(state=tk.DISABLED)
                self.log_message(f"Found {filename}")
            else:
                # File not found
                missing_files.append(file_type)
                frame_info['status'].configure(foreground="red")
                frame_info['browse'].configure(state=tk.NORMAL)
                self.log_message(f"Missing {filename}", level="warning")
        
        # Store found file paths
        self.structure_path = found_files.get('structure')
        self.flows_path = found_files.get('flows')
        self.ini_path = found_files.get('ini')
        
        if missing_files:
            # Show message about missing files
            missing_list = [self.default_files[ft] for ft in missing_files]
            message = f"Missing files:\n" + "\n".join(f"• {f}" for f in missing_list)
            message += "\n\nPlease use the Browse buttons to select these files individually."
            
            messagebox.showwarning("Missing Configuration Files", message)
            self.log_message("Some configuration files are missing. Please browse for them individually.", level="warning")
        else:
            # All files found, try to load the flow
            self.log_message("All configuration files found. Loading flow...")
            self.load_flow_configuration()

    def browse_individual_file(self, file_type):
        """Browse for individual configuration file."""
        filename = self.default_files[file_type]
        
        # Determine file type for dialog
        if file_type in ['structure', 'flows']:
            filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        else:  # ini
            filetypes = [("INI files", "*.ini"), ("All files", "*.*")]
        
        file_path = filedialog.askopenfilename(
            title=f"Select {filename}",
            filetypes=filetypes
        )
        
        if not file_path:
            return
        
        # Update the corresponding path
        if file_type == 'structure':
            self.structure_path = file_path
        elif file_type == 'flows':
            self.flows_path = file_path
        elif file_type == 'ini':
            self.ini_path = file_path
        
        # Update UI
        frame_info = self.file_labels[file_type]
        frame_info['status'].configure(foreground="green")
        frame_info['name'].configure(text=os.path.basename(file_path))
        frame_info['browse'].configure(state=tk.DISABLED)
        
        self.log_message(f"Selected {file_type} file: {os.path.basename(file_path)}")
        
        # Check if all files are now available
        if all([self.structure_path, self.flows_path, self.ini_path]):
            self.log_message("All configuration files selected. Loading flow...")
            self.load_flow_configuration()

    def load_flow_configuration(self):
        """Load the flow configuration from selected files."""
        try:
            # Create builder
            self.builder = FlowTestBuilder(
                self.structure_path, 
                self.flows_path, 
                self.ini_path, 
                Framework=self.framework,
                logger=self.log_message
            )
            
            # Build the flow
            self.root_node = self.builder._FlowTestBuilder__build_instance('BASELINE')
            self.executor = FlowTestExecutor(root=self.root_node, framework=self.framework)
            
            # Update total nodes count
            self.total_nodes = len(self.builder.builtNodes)
            
            # Draw the flow diagram
            self.draw_flow_diagram()
            
            # Enable start button
            self.start_button.configure(state=tk.NORMAL)
            
            self.log_message(f"Flow loaded successfully with {self.total_nodes} nodes", level="success")
            self.log_message("Ready to start execution")
            
        except Exception as e:
            error_msg = f"Error loading flow configuration: {str(e)}"
            self.log_message(error_msg, level="error")
            messagebox.showerror("Configuration Error", error_msg)
            
            # Reset UI state
            self.builder = None
            self.executor = None
            self.root_node = None
            self.start_button.configure(state=tk.DISABLED)
            self.show_canvas_message("Error loading configuration. Please check files and try again.")

    def show_canvas_message(self, message):
        """Show a message on the canvas when no flow is loaded."""
        self.canvas.delete("all")
        self.canvas.create_text(
            400, 300, text=message, 
            font=("Arial", 14), 
            fill="gray",
            width=600
        )

    def create_right_panel(self):
        """Create the status and logging panel."""
        # Title
        title_label = ttk.Label(self.right_frame, text="Execution Monitor", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(5, 10))
        
        # Current status section
        status_frame = ttk.LabelFrame(self.right_frame, text="Current Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Current node info
        self.current_node_label = ttk.Label(status_frame, text="Node: Ready to start")
        self.current_node_label.pack(anchor="w")
        
        self.current_experiment_label = ttk.Label(status_frame, text="Experiment: None")
        self.current_experiment_label.pack(anchor="w")
        
        self.current_status_label = ttk.Label(status_frame, text="Status: Idle")
        self.current_status_label.pack(anchor="w")
        
        # Statistics section
        stats_frame = ttk.LabelFrame(self.right_frame, text="Flow Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Node counters
        counters_frame = ttk.Frame(stats_frame)
        counters_frame.pack(fill=tk.X)
        
        self.completed_nodes_label = ttk.Label(counters_frame, text="✓ Completed: 0", 
                                             foreground="green")
        self.completed_nodes_label.pack(side=tk.LEFT)
        
        self.failed_nodes_label = ttk.Label(counters_frame, text="✗ Failed: 0", 
                                          foreground="red")
        self.failed_nodes_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.total_nodes_label = ttk.Label(counters_frame, text="Total: 0")
        self.total_nodes_label.pack(side=tk.RIGHT)
        
        # Timing info
        timing_frame = ttk.Frame(stats_frame)
        timing_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.elapsed_time_label = ttk.Label(timing_frame, text="Elapsed: 00:00")
        self.elapsed_time_label.pack(side=tk.LEFT)
        
        self.eta_label = ttk.Label(timing_frame, text="ETA: --:--")
        self.eta_label.pack(side=tk.RIGHT)
        
        # Current experiment statistics
        exp_stats_frame = ttk.LabelFrame(self.right_frame, text="Current Experiment", padding=10)
        exp_stats_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        self.exp_iteration_label = ttk.Label(exp_stats_frame, text="Iteration: 0/0")
        self.exp_iteration_label.pack(anchor="w")
        
        self.exp_pass_rate_label = ttk.Label(exp_stats_frame, text="Pass Rate: 0%")
        self.exp_pass_rate_label.pack(anchor="w")
        
        self.exp_recommendation_label = ttk.Label(exp_stats_frame, text="Recommendation: --")
        self.exp_recommendation_label.pack(anchor="w")
        
        # Execution log
        log_frame = ttk.LabelFrame(self.right_frame, text="Execution Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, bg="black", fg="white", 
                                                 font=("Consolas", 9), wrap=tk.WORD, 
                                                 state=tk.DISABLED, width=50, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear", command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save", command=self.save_log).pack(side=tk.LEFT, padx=(5, 0))
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_controls, text="Auto-scroll", 
                       variable=self.auto_scroll_var).pack(side=tk.RIGHT)
        
        # Add initial log message
        self.log_message("Flow interface initialized")
        self.log_message("Please select a flow folder to begin")

    def log_message(self, message, level="info"):
        """Add message to log with timestamp and level."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        if level == "error":
            color = "red"
            prefix = "ERROR"
        elif level == "warning":
            color = "yellow"
            prefix = "WARN"
        elif level == "success":
            color = "green"
            prefix = "SUCCESS"
        else:
            color = "white"
            prefix = "INFO"
        
        log_entry = f"[{timestamp}] {prefix}: {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        
        # Insert with color
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, log_entry)
        end_pos = self.log_text.index(tk.END)
        
        # Apply color tag
        tag_name = f"level_{level}_{timestamp}"
        self.log_text.tag_add(tag_name, start_pos, end_pos)
        self.log_text.tag_config(tag_name, foreground=color)
        
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
        
        self.log_text.configure(state=tk.DISABLED)
        
        # Keep only last 500 lines
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 500:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.delete("1.0", f"{len(lines)-500}.0")
            self.log_text.configure(state=tk.DISABLED)

    def draw_flow_diagram(self):
        """Draw the complete flow diagram with nodes and connections."""
        if not self.builder:
            self.show_canvas_message("No flow configuration loaded")
            return
        
        self.canvas.delete("all")
        self.node_widgets.clear()
        self.connection_lines.clear()
        
        # Update total nodes label
        self.total_nodes_label.configure(text=f"Total: {self.total_nodes}")
        
        # Calculate layout
        positions = self.calculate_node_positions()
        
        # Draw connections first (so they appear behind nodes)
        self.draw_connections(positions)
        
        # Draw nodes
        self.draw_nodes(positions)
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def calculate_node_positions(self):
        """Calculate optimal positions for all nodes using a hierarchical layout."""
        positions = {}
        
        # Simple grid layout for now - can be enhanced with proper graph layout algorithms
        nodes_per_row = 4
        node_width = 150
        node_height = 100
        spacing_x = 200
        spacing_y = 150
        margin = 50
        
        row = 0
        col = 0
        
        # Position nodes in a grid
        for node in self.builder.builtNodes.values():
            x = margin + (col * spacing_x)
            y = margin + (row * spacing_y)
            
            positions[node.ID] = {
                'x': x, 'y': y, 
                'width': node_width, 'height': node_height,
                'center_x': x + node_width // 2,
                'center_y': y + node_height // 2
            }
            
            col += 1
            if col >= nodes_per_row:
                col = 0
                row += 1
        
        return positions

    def draw_nodes(self, positions):
        """Draw all nodes on the canvas."""
        for node in self.builder.builtNodes.values():
            pos = positions[node.ID]
            self.draw_single_node(node, pos)

    def draw_single_node(self, node, pos):
        """Draw a single node with current status styling."""
        x, y = pos['x'], pos['y']
        width, height = pos['width'], pos['height']
        
        # Determine node color based on status
        if node.ID in self.failed_nodes:
            color = self.node_colors['failed']
            text_color = 'white'
        elif node.ID in self.completed_nodes:
            color = self.node_colors['completed']
            text_color = 'white'
        elif self.current_node and node.ID == self.current_node.ID:
            color = self.node_colors['current']
            text_color = 'white'
        else:
            color = self.node_colors['idle']
            text_color = 'black'
        
        # Draw main node rectangle
        node_rect = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=color, outline='black', width=2,
            tags=f"node_{node.ID}"
        )
        
        # Draw node name
        name_text = self.canvas.create_text(
            x + width // 2, y + 20,
            text=node.Name, fill=text_color,
            font=("Arial", 10, "bold"),
            width=width - 10,
            tags=f"node_{node.ID}"
        )
        
        # Draw node ID
        id_text = self.canvas.create_text(
            x + width // 2, y + 40,
            text=f"ID: {node.ID}", fill=text_color,
            font=("Arial", 8),
            tags=f"node_{node.ID}"
        )
        
        # Draw experiment type
        exp_type = node.Experiment.get('Test Type', 'Unknown')
        type_text = self.canvas.create_text(
            x + width // 2, y + 60,
            text=f"Type: {exp_type}", fill=text_color,
            font=("Arial", 8),
            tags=f"node_{node.ID}"
        )
        
        # Draw status indicator (small square in corner)
        status_size = 15
        status_rect = self.canvas.create_rectangle(
            x + width - status_size - 5, y + 5,
            x + width - 5, y + status_size + 5,
            fill='white', outline='black',
            tags=f"node_{node.ID}"
        )
        
        # Store widget references
        self.node_widgets[node.ID] = {
            'rect': node_rect,
            'name': name_text,
            'id': id_text,
            'type': type_text,
            'status': status_rect,
            'position': pos
        }

    def draw_connections(self, positions):
        """Draw connections between nodes."""
        for node in self.builder.builtNodes.values():
            if not node.outputNodeMap:
                continue
                
            start_pos = positions[node.ID]
            start_x = start_pos['center_x']
            start_y = start_pos['y'] + start_pos['height']
            
            for port, next_node in node.outputNodeMap.items():
                end_pos = positions[next_node.ID]
                end_x = end_pos['center_x']
                end_y = end_pos['y']
                
                # Choose color based on port
                color = self.connection_colors.get(port, '#666666')
                
                # Draw connection line with arrow
                line = self.canvas.create_line(
                    start_x, start_y, end_x, end_y,
                    fill=color, width=3, arrow=tk.LAST,
                    arrowshape=(10, 12, 3),
                    tags=f"connection_{node.ID}_{next_node.ID}"
                )
                
                # Draw port label
                mid_x = (start_x + end_x) // 2
                mid_y = (start_y + end_y) // 2
                
                port_label = self.canvas.create_text(
                    mid_x, mid_y,
                    text=str(port), fill=color,
                    font=("Arial", 8, "bold"),
                    tags=f"connection_{node.ID}_{next_node.ID}"
                )
                
                self.connection_lines[f"{node.ID}_{next_node.ID}"] = {
                    'line': line,
                    'label': port_label,
                    'port': port
                }

    def start_execution(self):
        """Start the flow execution in a separate thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Reset counters
        self.completed_count = 0
        self.failed_count = 0
        self.completed_nodes.clear()
        self.failed_nodes.clear()
        
        # Update UI
        self.start_button.configure(state=tk.DISABLED)
        self.pause_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.NORMAL)
        
        self.log_message("Starting flow execution...", level="success")
        
        # Start execution thread
        self.execution_thread = threading.Thread(target=self.execute_flow, daemon=True)
        self.execution_thread.start()

    def execute_flow(self):
        """Execute the flow and send updates to UI thread."""
        try:
            # Override executor's log method to send updates to UI
            original_log = self.executor.log_execution
            self.executor.log_execution = self.thread_safe_log
            
            # Execute the flow
            current_node = self.root_node
            node_count = 0
            
            while current_node is not None and node_count < 50 and self.is_running:
                node_count += 1
                
                # Update current node
                self.update_queue.put(('current_node', current_node))
                
                # Execute node
                start_time = time.time()
                current_node.run_experiment()
                execution_time = time.time() - start_time
                
                # Update node status
                if 'FAIL' in current_node.runStatusHistory:
                    self.update_queue.put(('node_failed', current_node))
                else:
                    self.update_queue.put(('node_completed', current_node))
                
                # Get next node
                next_node = current_node.get_next_node()
                current_node = next_node
                
                if not self.is_running:
                    break
            
            # Execution completed
            self.update_queue.put(('execution_complete', None))
            
        except Exception as e:
            self.update_queue.put(('execution_error', str(e)))

    def thread_safe_log(self, message):
        """Thread-safe logging method."""
        self.update_queue.put(('log', message))

    def process_updates(self):
        """Process updates from the execution thread."""
        try:
            while True:
                update_type, data = self.update_queue.get_nowait()
                
                if update_type == 'current_node':
                    self.update_current_node(data)
                elif update_type == 'node_completed':
                    self.update_node_completed(data)
                elif update_type == 'node_failed':
                    self.update_node_failed(data)
                elif update_type == 'log':
                    self.log_message(data)
                elif update_type == 'execution_complete':
                    self.execution_completed()
                elif update_type == 'execution_error':
                    self.execution_error(data)
                    
        except queue.Empty:
            pass
        
        # Schedule next update
        if self.is_running or not self.update_queue.empty():
            self.root.after(100, self.process_updates)

    def update_current_node(self, node):
        """Update the current executing node."""
        self.current_node = node
        
        # Update UI labels
        self.current_node_label.configure(text=f"Node: {node.Name} ({node.ID})")
        self.current_experiment_label.configure(text=f"Experiment: {node.Experiment.get('Test Name', 'Unknown')}")
        self.current_status_label.configure(text="Status: Executing")
        
        # Redraw the specific node
        if node.ID in self.node_widgets:
            self.redraw_node(node)
        
        self.log_message(f"Executing node: {node.Name} ({node.ID})")

    def update_node_completed(self, node):
        """Update node as completed."""
        self.completed_nodes.add(node.ID)
        self.completed_count += 1
        
        # Update statistics
        self.completed_nodes_label.configure(text=f"✓ Completed: {self.completed_count}")
        self.update_progress()
        
        # Redraw node
        self.redraw_node(node)
        
        # Log results
        summary = node.get_execution_summary()
        self.log_message(f"Node completed: {node.Name} - {summary['pass_count']} pass, {summary['fail_count']} fail", level="success")

    def update_node_failed(self, node):
        """Update node as failed."""
        self.failed_nodes.add(node.ID)
        self.failed_count += 1
        
        # Update statistics
        self.failed_nodes_label.configure(text=f"✗ Failed: {self.failed_count}")
        self.update_progress()
        
        # Redraw node
        self.redraw_node(node)
        
        self.log_message(f"Node failed: {node.Name}", level="error")

    def redraw_node(self, node):
        """Redraw a specific node with updated status."""
        if node.ID not in self.node_widgets:
            return
        
        widget_info = self.node_widgets[node.ID]
        pos = widget_info['position']
        
        # Remove old node elements
        self.canvas.delete(f"node_{node.ID}")
        
        # Redraw with new status
        self.draw_single_node(node, pos)

    def update_progress(self):
        """Update overall progress."""
        if self.total_nodes > 0:
            progress = ((self.completed_count + self.failed_count) / self.total_nodes) * 100
            self.progress_var.set(progress)
            self.progress_label.configure(text=f"{int(progress)}%")
        
        # Update timing
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            elapsed_str = self.format_time(elapsed)
            self.elapsed_time_label.configure(text=f"Elapsed: {elapsed_str}")
            
            # Calculate ETA
            if self.completed_count + self.failed_count > 0:
                avg_time_per_node = elapsed / (self.completed_count + self.failed_count)
                remaining_nodes = self.total_nodes - (self.completed_count + self.failed_count)
                eta_seconds = remaining_nodes * avg_time_per_node
                eta_str = self.format_time(eta_seconds)
                self.eta_label.configure(text=f"ETA: {eta_str}")

    def format_time(self, seconds):
        """Format seconds to MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def execution_completed(self):
        """Handle execution completion."""
        self.is_running = False
        
        # Update UI
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.DISABLED)
        
        self.current_status_label.configure(text="Status: Completed")
        
        total_time = (datetime.now() - self.start_time).total_seconds()
        self.log_message(f"Flow execution completed in {self.format_time(total_time)}", level="success")
        self.log_message(f"Results: {self.completed_count} completed, {self.failed_count} failed")

    def execution_error(self, error_msg):
        """Handle execution error."""
        self.is_running = False
        
        # Update UI
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.DISABLED)
        
        self.current_status_label.configure(text="Status: Error")
        self.log_message(f"Execution error: {error_msg}", level="error")

    def pause_execution(self):
        """Pause execution (placeholder for future implementation)."""
        self.log_message("Pause functionality not yet implemented", level="warning")

    def stop_execution(self):
        """Stop execution."""
        self.is_running = False
        self.log_message("Execution stopped by user", level="warning")

    def clear_log(self):
        """Clear the log."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.log_message("Log cleared")

    def save_log(self):
        """Save log to file."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Execution Log"
            )
            if file_path:
                log_content = self.log_text.get("1.0", tk.END)
                with open(file_path, 'w') as f:
                    f.write(log_content)
                self.log_message(f"Log saved to: {file_path}", level="success")
        except Exception as e:
            self.log_message(f"Error saving log: {str(e)}", level="error")

    def on_canvas_click(self, event):
        """Handle canvas click events."""
        # Find clicked item
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        # Check if it's a node
        for tag in tags:
            if tag.startswith("node_"):
                node_id = tag.split("_", 1)[1]
                self.show_node_details(node_id)
                break

    def show_node_details(self, node_id):
        """Show detailed information about a node."""
        node = self.builder.builtNodes.get(node_id)
        if not node:
            return
        
        # Create popup window with node details
        popup = tk.Toplevel(self.root)
        popup.title(f"Node Details: {node.Name}")
        popup.geometry("400x300")
        
        # Node information
        info_frame = ttk.LabelFrame(popup, text="Node Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_frame, text=f"ID: {node.ID}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Name: {node.Name}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Type: {type(node).__name__}").pack(anchor="w")
        
        # Experiment details
        exp_frame = ttk.LabelFrame(popup, text="Experiment Configuration", padding=10)
        exp_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        exp_text = tk.Text(exp_frame, height=10, width=50)
        exp_scrollbar = ttk.Scrollbar(exp_frame, orient="vertical", command=exp_text.yview)
        exp_text.configure(yscrollcommand=exp_scrollbar.set)
        
        # Display experiment configuration
        for key, value in node.Experiment.items():
            exp_text.insert(tk.END, f"{key}: {value}\n")
        
        exp_text.pack(side="left", fill="both", expand=True)
        exp_scrollbar.pack(side="right", fill="y")

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling on canvas."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def run(self):
        """Start the UI main loop."""
        self.root.mainloop()

# Standalone function to start the UI
def start_automation_flow_ui(framework=None):
    """
    Start the automation flow UI.
    """
    interface = FlowProgressInterface(framework=framework)
    interface.run()

def start_automation_flow(structure_path, flows_path, ini_file_path, framework):
    """
    Start the automation flow with enhanced Framework integration.
    """
    try:
        print("Starting Automation Flow...")
        print(f"Structure: {structure_path}")
        print(f"Flows: {flows_path}")
        print(f"Config: {ini_file_path}")
        
        # Build the flow
        builder = FlowTestBuilder(structure_path, flows_path, ini_file_path, Framework=framework)
        executor = builder.build_flow(rootID='BASELINE')
        
        # Execute the flow
        print("Executing flow...")
        executor.execute()
        
        # Generate report
        report = executor.get_execution_report()
        print(f"\nFlow completed in {report['total_time']:.1f} seconds")
        print("Execution log:")
        for log_entry in report['execution_log']:
            print(f"  {log_entry}")
            
    except Exception as e:
        print(f"Error in automation flow: {e}")
        raise

# Main execution
if __name__ == '__main__':
    # Start the UI without pre-loading any files
    start_automation_flow_ui(framework=None)