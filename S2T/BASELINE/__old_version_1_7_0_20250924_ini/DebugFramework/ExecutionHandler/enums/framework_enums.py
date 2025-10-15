from enum import Enum

class ContentType(Enum):
    DRAGON = "Dragon"
    LINUX = "Linux"
    PYSVCONSOLE = "PYSVConsole"
    BOOTBREAKS = "BootBreaks"
    CUSTOM = 'Custom'

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
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    EXECUTION_FAIL = 'ExecutionFail'
    PYTHON_FAIL = 'PythonFail'

class TestType(Enum):
    SWEEP = "Sweep"
    SHMOO = "Shmoo"
    LOOPS = "Loops"

class ContentValues(Enum):
    PRODUCT = "GNR"  # This should be imported from s2t.SELECTED_PRODUCT
    ULX_CPU = "GNR_B0"  # This should be from ULX_CPU_DICT