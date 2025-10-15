"""
Framework Enums
"""
from enum import Enum

print(' -- Debug Framework Variables Configuration -- rev 1.7')

#########################################################
######		Debug Framework Configuration Code
#########################################################

# Enums for better type safety
class ContentType(Enum):
	DRAGON = "Dragon"
	LINUX = "Linux"
	PYSVCONSOLE = "PYSVConsole"
	BOOTBREAKS = "BootBreaks"
	CUSTOM = 'Custom' # Custom EFI TTL no need for Linux, that one is Custom by default

class ExecutionMode(Enum):
	CONTINUOUS = "continuous"
	STEP_BY_STEP = "step_by_step"

class TestTarget(Enum):
	MESH = "mesh"
	SLICE = "slice"

class VoltageType(Enum):
	VBUMP = "vbump"
	PPVC = "ppvc"
	FIXED = "fixed"

class TestStatus(Enum):
	SUCCESS = "Success"
	STARTED = "Started"
	CANCELLED = "CANCELLED"
	FAILED = "Failed"
	EXECUTION_FAIL = 'ExecutionFAIL'
	PYTHON_FAIL = 'PythonFail'
	PASS = "PASS"
	FAIL = "FAIL"

class TestType(Enum):
	SWEEP = "Sweep"
	SHMOO = "Shmoo"
	LOOPS = "Loops"

