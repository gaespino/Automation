"""
Framework Exception Classes
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class BootFailureType(Enum):
    REGACC_FAILURE = "regacc_failure"
    GENERAL_FAILURE = "general_failure"
    TIMEOUT_FAILURE = "timeout_failure"
    CONFIGURATION_FAILURE = "config_failure"
    USER_CANCEL = "user_cancel"

class TestExecutionError(Exception):
    """Custom exception for test execution errors"""
    
    def __init__(
        self, 
        message: str, 
        failure_type: Optional[BootFailureType] = None, 
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.failure_type = failure_type
        self.original_exception = original_exception
        self.context = context or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization"""
        return {
            'message': str(self),
            'failure_type': self.failure_type.value if self.failure_type else None,
            'original_exception': str(self.original_exception) if self.original_exception else None,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }

class ConfigurationError(TestExecutionError):
    """Raised when configuration is invalid"""
    pass

class ExecutionTimeoutError(TestExecutionError):
    """Raised when execution times out"""
    pass