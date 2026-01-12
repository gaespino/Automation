"""
Framework Exception Classes
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

print(' -- Debug Framework Exceptions -- rev 1.7')

#########################################################
######		Exception Handling -- WIP
#########################################################

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
