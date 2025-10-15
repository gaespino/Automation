# mock_framework.py
"""Mock Framework module to avoid import dependencies"""

from unittest.mock import Mock, MagicMock
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import threading
import queue

# Mock enums that would normally come from Framework
class ContentType(Enum):
    DRAGON = "dragon"
    LINUX = "linux"
    CUSTOM = "custom"
    BOOTBREAKS = "bootbreaks"
    PYSVCONSOLE = "pysvconsole"

class TestTarget(Enum):
    MESH = "mesh"
    SLICE = "slice"

class VoltageType(Enum):
    SVID = "svid"
    FIVR = "fivr"

class TestStatus(Enum):
    SUCCESS = "PASS"
    FAILED = "FAIL"
    CANCELLED = "CANCELLED"
    EXECUTION_FAIL = "ExecutionFAIL"
    PASS = "PASS"

class ExecutionCommand(Enum):
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    END_EXPERIMENT = "end_experiment"
    STEP_CONTINUE = "step_continue"
    EMERGENCY_STOP = "emergency_stop"

class StatusEventType(Enum):
    EXPERIMENT_START = "experiment_start"
    ITERATION_START = "iteration_start"
    ITERATION_PROGRESS = "iteration_progress"
    ITERATION_COMPLETE = "iteration_complete"
    ITERATION_FAILED = "iteration_failed"
    ITERATION_CANCELLED = "iteration_cancelled"
    STRATEGY_PROGRESS = "strategy_progress"
    STRATEGY_COMPLETE = "strategy_complete"
    EXPERIMENT_COMPLETE = "experiment_complete"
    EXPERIMENT_FAILED = "experiment_failed"
    EXECUTION_HALTED = "execution_halted"
    EXECUTION_RESUMED = "execution_resumed"
    EXECUTION_CANCELLED = "execution_cancelled"
    EXECUTION_ENDED = "execution_ended"

# Mock configuration classes
@dataclass
class MockTestConfiguration:
    name: str = "MockTest"
    tnumber: int = 1
    visual: str = "MOCK123"
    qdf: str = "MockQDF"
    bucket: str = "MockBucket"
    content: ContentType = ContentType.DRAGON
    target: TestTarget = TestTarget.MESH
    volt_type: VoltageType = VoltageType.SVID
    freq_ia: int = 2400
    freq_cfc: int = 2000
    volt_IA: float = 1.0
    volt_CFC: float = 1.0
    mask: str = "0"
    reset: bool = True
    fastboot: bool = False
    pseudo: bool = False
    dis2CPM: int = 0
    corelic: int = 0
    passstring: str = "PASS"
    failstring: str = "FAIL"
    tfolder: str = ""
    log_file: str = ""
    ser_log_file: str = ""
    script_file: str = ""
    macro_folder: str = ""
    ttl_files_dict: Dict = None
    ttl_path: str = ""
    extMask: Dict = None
    cancel_flag: Any = None
    execution_cancelled: bool = False
    execution_ended: bool = False
    experiment_name: str = ""
    strategy_type: str = ""

@dataclass
class MockSystemToTesterConfig:
    AFTER_MRC_POST: int = 30
    EFI_POST: int = 60
    LINUX_POST: int = 120
    BOOTSCRIPT_RETRY_TIMES: int = 3
    BOOTSCRIPT_RETRY_DELAY: int = 10
    MRC_POSTCODE_WT: int = 5
    EFI_POSTCODE_WT: int = 10
    MRC_POSTCODE_CHECK_COUNT: int = 3
    EFI_POSTCODE_CHECK_COUNT: int = 5
    BOOT_STOP_POSTCODE: str = "0x00"
    BOOT_POSTCODE_WT: int = 15
    BOOT_POSTCODE_CHECK_COUNT: int = 10

# Mock execution state
class MockExecutionState:
    def __init__(self):
        self._state = {
            'execution_active': False,
            'current_experiment': None,
            'current_iteration': 0,
            'total_iterations': 0,
            'waiting_for_step': False,
            'step_mode_enabled': False,
            'framework_ready': True
        }
        self._commands = set()
        self._callbacks = {}
        
    def get_state(self, key):
        return self._state.get(key, False)
    
    def set_state(self, key, value):
        self._state[key] = value
    
    def update_state(self, **kwargs):
        self._state.update(kwargs)
    
    def is_cancelled(self):
        return ExecutionCommand.CANCEL in self._commands
    
    def is_ended(self):
        return ExecutionCommand.END_EXPERIMENT in self._commands
    
    def is_paused(self):
        return ExecutionCommand.PAUSE in self._commands
    
    def cancel(self, reason="", callback=None):
        self._commands.add(ExecutionCommand.CANCEL)
        if callback:
            callback("Cancel acknowledged")
        return True
    
    def end_experiment(self, callback=None):
        self._commands.add(ExecutionCommand.END_EXPERIMENT)
        if callback:
            callback("End acknowledged")
        return True
    
    def pause(self, callback=None):
        self._commands.add(ExecutionCommand.PAUSE)
        if callback:
            callback("Pause acknowledged")
        return True
    
    def resume(self, callback=None):
        if ExecutionCommand.PAUSE in self._commands:
            self._commands.remove(ExecutionCommand.PAUSE)
        if callback:
            callback("Resume acknowledged")
        return True
    
    def clear_all_commands(self):
        self._commands.clear()
    
    def has_command(self, command):
        return command in self._commands
    
    def get_active_commands(self):
        return list(self._commands)
    
    def prepare_for_execution(self):
        self.clear_all_commands()
        self._state['execution_active'] = False
        return True
    
    def finalize_execution(self, reason="completed"):
        self._state['execution_active'] = False
        self.clear_all_commands()

# Mock status manager
class MockStatusUpdateManager:
    def __init__(self, status_reporter=None, logger=None):
        self.status_reporter = status_reporter
        self.logger = logger or print
        self.enabled = status_reporter is not None
        self.context = {}
    
    def update_context(self, **kwargs):
        self.context.update(kwargs)
    
    def send_update(self, event_type, **kwargs):
        if self.enabled and self.status_reporter:
            status_data = {
                'type': event_type.value if hasattr(event_type, 'value') else str(event_type),
                'data': kwargs,
                'timestamp': '2024-01-01 12:00:00'
            }
            self.status_reporter.report_status(status_data)
    
    def disable(self):
        self.enabled = False

# Mock Framework class
class MockFramework:
    def __init__(self, upload_to_database=True, status_reporter=None):
        self.upload_to_database = upload_to_database
        self.config = MockTestConfiguration()
        self.s2t_config = MockSystemToTesterConfig()
        self.status_manager = MockStatusUpdateManager(status_reporter)
        self.execution_state = MockExecutionState()
        self.current_experiment_name = None
        
    def RecipeExecutor(self, data, S2T_BOOT_CONFIG=None, extmask=None, 
                      summary=True, cancel_flag=None, experiment_name=None):
        """Mock recipe executor"""
        if experiment_name:
            self.current_experiment_name = experiment_name
        
        # Simulate different test results based on test type
        test_type = data.get('Test Type', 'Loops')
        if test_type == 'Loops':
            loops = data.get('Loops', 5)
            return ['PASS'] * loops
        elif test_type == 'Sweep':
            start = data.get('Start', 16)
            end = data.get('End', 32)
            step = data.get('Steps', 4)
            count = int((end - start) / step) + 1
            return ['PASS'] * count
        elif test_type == 'Shmoo':
            return ['PASS'] * 25  # Default shmoo size
        else:
            return ['PASS']
    
    def end_experiment(self):
        return self.execution_state.end_experiment()
    
    def halt_execution(self):
        return self.execution_state.pause()
    
    def continue_execution(self):
        return self.execution_state.resume()
    
    def cancel_execution(self):
        return self.execution_state.cancel()
    
    def get_execution_state(self):
        return {
            'is_running': self.execution_state.get_state('execution_active'),
            'current_iteration': self.execution_state.get_state('current_iteration'),
            'total_iterations': self.execution_state.get_state('total_iterations'),
            'experiment_name': self.current_experiment_name,
            'end_requested': self.execution_state.is_ended()
        }

# Mock Framework API
class MockFrameworkExternalAPI:
    def __init__(self, framework):
        self.framework = framework
    
    def execute_experiment(self, experiment_data, s2t_config=None, extmask=None, experiment_name=None):
        return self.framework.RecipeExecutor(
            experiment_data, s2t_config, extmask, experiment_name=experiment_name
        )
    
    def halt_execution(self):
        success = self.framework.halt_execution()
        return {'success': success, 'message': 'Halt command sent' if success else 'Failed'}
    
    def continue_execution(self):
        success = self.framework.continue_execution()
        return {'success': success, 'message': 'Continue command sent' if success else 'Failed'}
    
    def end_experiment(self):
        success = self.framework.end_experiment()
        return {'success': success, 'message': 'End command sent' if success else 'Failed'}
    
    def cancel_experiment(self):
        success = self.framework.cancel_execution()
        return {'success': success, 'message': 'Cancel command sent' if success else 'Failed'}
    
    def get_current_state(self):
        return self.framework.get_execution_state()
    
    def _set_upload_to_db(self, value):
        self.framework.upload_to_database = value
    
    def _update_unit_data(self):
        pass  # Mock implementation

# Mock Framework Manager
class MockFrameworkInstanceManager:
    def __init__(self, framework_class=None):
        self.framework_class = framework_class or MockFramework
        self._current_framework = None
        self._current_api = None
    
    def create_framework_instance(self, status_reporter=None, execution_state=None):
        self._current_framework = self.framework_class(status_reporter=status_reporter)
        if execution_state:
            self._current_framework.execution_state = execution_state
        self._current_api = MockFrameworkExternalAPI(self._current_framework)
        return self._current_api
    
    def get_current_api(self):
        return self._current_api
    
    def cleanup_current_instance(self, msg="cleanup"):
        self._current_framework = None
        self._current_api = None

# Mock utilities
class MockFrameworkUtils:
    @staticmethod
    def system_2_tester_default():
        return {
            'AFTER_MRC_POST': 30,
            'EFI_POST': 60,
            'LINUX_POST': 120,
            'BOOTSCRIPT_RETRY_TIMES': 3,
            'BOOTSCRIPT_RETRY_DELAY': 10
        }
    
    @staticmethod
    def Recipes(file_path):
        # Return mock experiment data
        return {
            'Mock_Experiment_1': {
                'Experiment': 'Enabled',
                'Test Name': 'Mock Test 1',
                'Test Mode': 'Normal',
                'Test Type': 'Loops',
                'Loops': 5,
                'External Mask': None
            },
            'Mock_Experiment_2': {
                'Experiment': 'Disabled',
                'Test Name': 'Mock Test 2',
                'Test Mode': 'Debug',
                'Test Type': 'Sweep',
                'Type': 'frequency',
                'Domain': 'ia',
                'Start': 16,
                'End': 32,
                'Steps': 4,
                'External Mask': None
            }
        }
    
    @staticmethod
    def refresh_ipc():
        pass  # Mock implementation

# Mock global execution state
mock_execution_state = MockExecutionState()

# Mock functions that would normally fail on import
def OpenExperiment(file_path):
    """Mock experiment loader"""
    return MockFrameworkUtils.Recipes(file_path)

def Convert_xlsx_to_json(file_path, experiments):
    """Mock converter"""
    pass

# Configuration for S2T
S2T_CONFIGURATION = MockFrameworkUtils.system_2_tester_default()