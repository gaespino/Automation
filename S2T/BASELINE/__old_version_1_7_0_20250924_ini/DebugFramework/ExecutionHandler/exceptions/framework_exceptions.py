from enum import Enum

class BootFailureType(Enum):
    REGACC_FAILURE = "regacc_failure"
    GENERAL_FAILURE = "general_failure"
    TIMEOUT_FAILURE = "timeout_failure"
    CONFIGURATION_FAILURE = "config_failure"
    USER_CANCEL = "user_cancel"

class TestExecutionError(Exception):
    """Custom exception for test execution errors"""
    def __init__(self, message: str, failure_type: BootFailureType = None, original_exception: Exception = None):
        super().__init__(message)
        self.failure_type = failure_type
        self.original_exception = original_exception

class FrameworkConfigurationError(Exception):
    """Exception for framework configuration errors"""
    pass

class StrategyExecutionError(Exception):
    """Exception for strategy execution errors"""
    pass