from abc import ABC, abstractmethod
from typing import List
from ..core.interfaces import ITestStrategy
from ..configurations.test_configurations import TestResult

class TestStrategy(ITestStrategy):
    """Abstract base class for different test strategies"""
    
    @abstractmethod
    def execute(self, executor, halt_controller=None) -> List[TestResult]:
        """Execute the test strategy"""
        pass