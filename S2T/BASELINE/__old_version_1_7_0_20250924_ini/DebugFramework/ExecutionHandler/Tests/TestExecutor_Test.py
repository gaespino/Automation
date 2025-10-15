"""
Tests for TestExecutor Class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import threading
import time

from framework.core.test_executor import TestExecutor
from framework.core.configurations import TestConfiguration, SystemToTesterConfig
from framework.core.enums import TestStatus
from framework.core.exceptions import TestExecutionError
from framework.interfaces.framework_interfaces import ILogger, IStatusReporter

class MockLogger(ILogger):
    """Mock logger for testing"""
    
    def __init__(self):
        self.messages = []
        self.exceptions = []
    
    def log(self, message: str, level: int = 1) -> None:
        self.messages.append((message, level))
    
    def log_exception(self, exception: Exception, context: str = "") -> None:
        self.exceptions.append((exception, context))

class MockStatusReporter(IStatusReporter):
    """Mock status reporter for testing"""
    
    def __init__(self):
        self.status_updates = []
    
    def report_status(self, status_data: dict) -> None:
        self.status_updates.append(status_data)

class TestTestExecutor:
    """Test TestExecutor class"""
    
    @pytest.fixture
    def mock_logger(self):
        return MockLogger()
    
    @pytest.fixture
    def mock_status_reporter(self):
        return MockStatusReporter()
    
    @pytest.fixture
    def sample_config(self):
        return TestConfiguration(name="Test Executor Test")
    
    @pytest.fixture
    def sample_s2t_config(self):
        return SystemToTesterConfig()
    
    @pytest.fixture
    def test_executor(self, sample_config, sample_s2t_config, mock_logger, mock_status_reporter):
        return TestExecutor(
            config=sample_config,
            s2t_config=sample_s2t_config,
            logger=mock_logger,
            status_reporter=mock_status_reporter
        )
    
    def test_executor_initialization(self, test_executor, mock_logger):
        """Test executor initializes correctly"""
        assert test_executor.config.name == "Test Executor Test"
        assert test_executor.current_status == TestStatus.SUCCESS
        assert len(mock_logger.messages) > 0  # Should have setup messages
    
    def test_invalid_configuration_raises_error(self, mock_logger, mock_status_reporter):
        """Test that invalid configuration raises error during initialization"""
        invalid_config = TestConfiguration(name="", ttime=-1)  # Invalid config
        s2t_config = SystemToTesterConfig()
        
        with pytest.raises(TestExecutionError):
            TestExecutor(
                config=invalid_config,
                s2t_config=s2t_config,
                logger=mock_logger,
                status_reporter=mock_status_reporter
            )
    
    def test_cancel_execution(self, test_executor):
        """Test execution cancellation"""
        cancel_flag = threading.Event()
        test_executor.cancel_flag = cancel_flag
        
        result = test_executor.cancel_execution()
        
        assert result is True
        assert cancel_flag.is_set()
    
    def test_get_execution_status(self, test_executor):
        """Test getting execution status"""
        status = test_executor.get_execution_status()
        
        assert 'current_status' in status
        assert 'test_name' in status
        assert 'iteration' in status
        assert status['test_name'] == "Test Executor Test"
    
    @patch('framework.core.test_executor.time.time')
    def test_execute_test_success(self, mock_time, test_executor, mock_status_reporter):
        """Test successful test execution"""
        mock_time.return_value = 1000.0
        
        # Mock the execute_single_test method to return success
        with patch.object(test_executor, 'execute_single_test') as mock_execute:
            from framework.core.configurations import TestResult
            mock_result = TestResult(
                status=TestStatus.SUCCESS.value,
                name="Test Executor Test",
                iteration=1
            )
            mock_execute.return_value = mock_result
            
            result = test_executor.execute_test({})
            
            assert result['status'] == TestStatus.SUCCESS.value
            assert result['name'] == "Test Executor Test"
            assert 'execution_time' in result
    
    def test_execute_test_with_exception(self, test_executor, mock_logger):
        """Test test execution with exception"""
        # Mock execute_single_test to raise an exception
        with patch.object(test_executor, 'execute_single_test') as mock_execute:
            mock_execute.side_effect = Exception("Test exception")
            
            result = test_executor.execute_test({})
            
            assert result['status'] == TestStatus.FAILED.value
            assert 'error_details' in result
            assert len(mock_logger.exceptions) > 0
    
    def test_status_updates_sent(self, test_executor, mock_status_reporter):
        """Test that status updates are sent correctly"""
        test_executor._send_status_update('test_event', {'data': 'test'})
        
        assert len(mock_status_reporter.status_updates) > 0
        update = mock_status_reporter.status_updates[-1]
        assert update['type'] == 'test_event'
        assert update['data']['data'] == 'test'
        assert 'timestamp' in update
    
    def test_cancellation_check(self, test_executor):
        """Test cancellation checking"""
        cancel_flag = threading.Event()
        test_executor.cancel_flag = cancel_flag
        
        # Should not raise when not cancelled
        test_executor._check_cancellation()
        
        # Should raise when cancelled
        cancel_flag.set()
        with pytest.raises(InterruptedError):
            test_executor._check_cancellation()
    
    def test_configuration_update_from_dict(self, test_executor):
        """Test updating configuration from dictionary"""
        config_dict = {
            'name': 'Updated Name',
            'ttime': 120,
            'volt_IA': 1.5
        }
        
        test_executor._update_config_from_dict(config_dict)
        
        assert test_executor.config.name == 'Updated Name'
        assert test_executor.config.ttime == 120
        assert test_executor.config.volt_IA == 1.5

class TestTestExecutorIntegration:
    """Integration tests for TestExecutor"""
    
    def test_full_execution_cycle(self):
        """Test full execution cycle with mocked dependencies"""
        logger = MockLogger()
        status_reporter = MockStatusReporter()
        config = TestConfiguration(name="Integration Test")
        s2t_config = SystemToTesterConfig()
        
        executor = TestExecutor(
            config=config,
            s2t_config=s2t_config,
            logger=logger,
            status_reporter=status_reporter
        )
        
        # Mock the actual test execution parts
        with patch.object(executor, 'execute_single_test') as mock_execute:
            from framework.core.configurations import TestResult
            mock_result = TestResult(
                status=TestStatus.SUCCESS.value,
                name="Integration Test",
                iteration=1
            )
            mock_execute.return_value = mock_result
            
            result = executor.execute_test({})
            
            # Verify the full cycle worked
            assert result['status'] == TestStatus.SUCCESS.value
            assert len(logger.messages) > 0
            assert len(status_reporter.status_updates) >= 0  # May have status updates
    
    def test_concurrent_execution_safety(self):
        """Test that executor is safe for concurrent operations"""
        logger = MockLogger()
        status_reporter = MockStatusReporter()
        config = TestConfiguration(name="Concurrent Test")
        s2t_config = SystemToTesterConfig()
        
        executor = TestExecutor(
            config=config,
            s2t_config=s2t_config,
            logger=logger,
            status_reporter=status_reporter
        )
        
        # Test concurrent status updates
        def send_updates():
            for i in range(10):
                executor._send_status_update(f'event_{i}', {'data': i})
                time.sleep(0.01)
        
        threads = [threading.Thread(target=send_updates) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have received all updates without errors
        assert len(status_reporter.status_updates) == 30