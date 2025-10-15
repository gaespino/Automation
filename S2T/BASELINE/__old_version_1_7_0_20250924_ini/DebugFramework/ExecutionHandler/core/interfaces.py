from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

class IStatusReporter(ABC):
    """Interface for status reporting"""
    
    @abstractmethod
    def report_status(self, status_data: Dict[str, Any]) -> None:
        """Report status update"""
        pass

class ITestStrategy(ABC):
    """Interface for test execution strategies"""
    
    @abstractmethod
    def execute(self, executor, halt_controller=None) -> List:
        """Execute the test strategy"""
        pass

class IContentBuilder(ABC):
    """Interface for content builders"""
    
    @abstractmethod
    def generate_ttl_configuration(self, content: str) -> Any:
        """Generate TTL configuration for given content type"""
        pass

class IResultProcessor(ABC):
    """Interface for result processing"""
    
    @abstractmethod
    def create_shmoo_data(self, results: List, test_type: str) -> tuple:
        """Create shmoo data from results"""
        pass