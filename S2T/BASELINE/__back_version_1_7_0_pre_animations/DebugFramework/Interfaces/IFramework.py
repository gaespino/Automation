"""
Framework Interfaces
Defines all interfaces used across the framework for dependency injection and abstraction.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

# ==================== STATUS REPORTING ====================

class IStatusReporter(ABC):
    """Interface for status reporting across the framework"""
    
    @abstractmethod
    def report_status(self, status_data: Dict[str, Any]) -> None:
        """
        Report status update to the UI or logging system
        
        Args:
            status_data: Dictionary containing status information with keys:
                - type: str - Type of status update
                - timestamp: str - ISO timestamp
                - data: Dict[str, Any] - Status-specific data
        """
        pass

# ==================== SYSTEM CONTROL ====================

class ISystemController(ABC):
    """Interface for system control operations"""
    
    @abstractmethod
    def reboot_unit(self, **kwargs) -> bool:
        """Reboot the test unit"""
        pass
    
    @abstractmethod
    def refresh_ipc(self) -> bool:
        """Refresh IPC connection"""
        pass
    
    @abstractmethod
    def power_control(self, state: str, **kwargs) -> bool:
        """Control unit power (on/off/cycle)"""
        pass

# ==================== FILE HANDLING ====================

class IFileHandler(ABC):
    """Interface for file operations"""
    
    @abstractmethod
    def create_log_folder(self, path: str) -> str:
        """Create log folder and return path"""
        pass
    
    @abstractmethod
    def copy_files(self, source: str, destination: str, **kwargs) -> bool:
        """Copy files from source to destination"""
        pass
    
    @abstractmethod
    def load_configuration(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        pass

# ==================== TEST EXECUTION ====================

class ITestExecutor(ABC):
    """Interface for test execution"""
    
    @abstractmethod
    def execute_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test"""
        pass
    
    @abstractmethod
    def cancel_execution(self) -> bool:
        """Cancel current test execution"""
        pass
    
    @abstractmethod
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        pass

# ==================== CONFIGURATION MANAGEMENT ====================

class IConfigurationManager(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def load_config(self, source: str) -> Dict[str, Any]:
        """Load configuration from source"""
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], destination: str) -> bool:
        """Save configuration to destination"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration and return (is_valid, errors)"""
        pass

# ==================== UI INTERFACES ====================

class IUIController(ABC):
    """Interface for UI control operations"""
    
    @abstractmethod
    def update_status(self, message: str, status_type: str = "info") -> None:
        """Update UI status display"""
        pass
    
    @abstractmethod
    def update_progress(self, progress: float, message: str = "") -> None:
        """Update progress display (0.0 to 1.0)"""
        pass
    
    @abstractmethod
    def show_error(self, message: str, title: str = "Error") -> None:
        """Show error message to user"""
        pass
    
    @abstractmethod
    def show_confirmation(self, message: str, title: str = "Confirm") -> bool:
        """Show confirmation dialog and return user choice"""
        pass

# ==================== THREAD MANAGEMENT ====================

class IThreadManager(ABC):
    """Interface for thread management"""
    
    @abstractmethod
    def start_background_task(self, task_func, *args, **kwargs) -> str:
        """Start background task and return task ID"""
        pass
    
    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel background task"""
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        pass

# ==================== DATA INTERFACES ====================

class IDataRepository(ABC):
    """Interface for data storage and retrieval"""
    
    @abstractmethod
    def save_test_results(self, results: Dict[str, Any]) -> str:
        """Save test results and return result ID"""
        pass
    
    @abstractmethod
    def load_test_results(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Load test results by ID"""
        pass
    
    @abstractmethod
    def query_results(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query results by criteria"""
        pass

# ==================== LOGGING ====================

class ILogger(ABC):
    """Interface for logging operations"""
    
    @abstractmethod
    def log(self, message: str, level: int = 1) -> None:
        """Log message with level (1=info, 2=warning, 3=error)"""
        pass
    
    @abstractmethod
    def log_exception(self, exception: Exception, context: str = "") -> None:
        """Log exception with context"""
        pass

# ==================== ENUMS AND CONSTANTS ====================

class ExecutionState(Enum):
    """Execution states for the framework"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StatusType(Enum):
    """Status update types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    PROGRESS = "progress"

# ==================== FACTORY INTERFACES ====================

class IFrameworkFactory(ABC):
    """Factory interface for creating framework components"""
    
    @abstractmethod
    def create_status_reporter(self) -> IStatusReporter:
        """Create status reporter instance"""
        pass
    
    @abstractmethod
    def create_system_controller(self) -> ISystemController:
        """Create system controller instance"""
        pass
    
    @abstractmethod
    def create_file_handler(self) -> IFileHandler:
        """Create file handler instance"""
        pass