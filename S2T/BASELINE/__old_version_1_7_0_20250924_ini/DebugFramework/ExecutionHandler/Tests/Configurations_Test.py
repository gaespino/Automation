"""
Tests for Configuration Classes
"""
import pytest
from unittest.mock import Mock, patch

from framework.core.configurations import (
    TestConfiguration, DragonConfiguration, LinuxConfiguration,
    SystemToTesterConfig, TestResult, FrameworkConfigurationManager
)
from framework.core.enums import ContentType, TestTarget, VoltageType
from framework.core.exceptions import ConfigurationError

class TestTestConfiguration:
    """Test TestConfiguration class"""
    
    def test_default_configuration_is_valid(self):
        """Test that default configuration is valid"""
        config = TestConfiguration()
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_empty_name_raises_error(self):
        """Test that empty name raises configuration error"""
        with pytest.raises(ConfigurationError):
            TestConfiguration(name="")
    
    def test_negative_time_raises_error(self):
        """Test that negative time raises configuration error"""
        with pytest.raises(ConfigurationError):
            TestConfiguration(ttime=-1)
    
    def test_invalid_voltage_ranges(self):
        """Test voltage validation"""
        with pytest.raises(ConfigurationError):
            TestConfiguration(volt_IA=3.0)  # Too high
        
        with pytest.raises(ConfigurationError):
            TestConfiguration(volt_CFC=0.1)  # Too low
    
    def test_invalid_frequency_ranges(self):
        """Test frequency validation"""
        with pytest.raises(ConfigurationError):
            TestConfiguration(freq_ia=50)  # Too low
        
        with pytest.raises(ConfigurationError):
            TestConfiguration(freq_cfc=7000)  # Too high
    
    def test_valid_configuration_passes(self):
        """Test that valid configuration passes validation"""
        config = TestConfiguration(
            name="Test Config",
            ttime=60,
            volt_IA=1.2,
            volt_CFC=1.1,
            freq_ia=2000,
            freq_cfc=1800
        )
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0

class TestDragonConfiguration:
    """Test DragonConfiguration class"""
    
    def test_default_dragon_config_is_valid(self):
        """Test default dragon configuration"""
        config = DragonConfiguration()
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_ulx_cpu_without_path_fails(self):
        """Test that ULX CPU without path fails validation"""
        config = DragonConfiguration(ulx_cpu="test_cpu")
        is_valid, errors = config.validate()
        assert not is_valid
        assert "ULX path required" in errors[0]
    
    def test_invalid_apic_cdie_fails(self):
        """Test invalid APIC CDIE values"""
        config = DragonConfiguration(apic_cdie=5)
        is_valid, errors = config.validate()
        assert not is_valid
        assert "APIC CDIE must be between 0 and 3" in errors[0]

class TestLinuxConfiguration:
    """Test LinuxConfiguration class"""
    
    def test_default_linux_config_is_valid(self):
        """Test default linux configuration"""
        config = LinuxConfiguration()
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_negative_wait_time_fails(self):
        """Test negative wait time fails validation"""
        config = LinuxConfiguration(linux_wait_time=-10)
        is_valid, errors = config.validate()
        assert not is_valid
        assert "wait time must be non-negative" in errors[0]

class TestSystemToTesterConfig:
    """Test SystemToTesterConfig class"""
    
    def test_default_s2t_config_is_valid(self):
        """Test default S2T configuration"""
        config = SystemToTesterConfig()
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_negative_retry_times_fails(self):
        """Test negative retry times fails validation"""
        config = SystemToTesterConfig(BOOTSCRIPT_RETRY_TIMES=-1)
        is_valid, errors = config.validate()
        assert not is_valid
        assert "Retry times must be non-negative" in errors[0]

class TestTestResult:
    """Test TestResult class"""
    
    def test_test_result_creation(self):
        """Test TestResult creation and serialization"""
        result = TestResult(
            status="PASS",
            name="Test1",
            scratchpad="test_data",
            seed="12345",
            iteration=1
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['status'] == "PASS"
        assert result_dict['name'] == "Test1"
        assert result_dict['scratchpad'] == "test_data"
        assert result_dict['seed'] == "12345"
        assert result_dict['iteration'] == 1
        assert 'timestamp' in result_dict

class TestFrameworkConfigurationManager:
    """Test FrameworkConfigurationManager class"""
    
    def test_validate_config_with_valid_data(self):
        """Test configuration validation with valid data"""
        manager = FrameworkConfigurationManager()
        
        config_data = {
            'name': 'Test Config',
            'ttime': 30,
            'volt_IA': 1.2,
            'freq_ia': 2000
        }
        
        is_valid, errors = manager.validate_config(config_data)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_config_with_invalid_data(self):
        """Test configuration validation with invalid data"""
        manager = FrameworkConfigurationManager()
        
        config_data = {
            'name': '',  # Invalid empty name
            'ttime': -1,  # Invalid negative time
        }
        
        is_valid, errors = manager.validate_config(config_data)
        assert not is_valid
        assert len(errors) > 0

# Fixtures for testing
@pytest.fixture
def sample_test_config():
    """Sample test configuration for testing"""
    return TestConfiguration(
        name="Sample Test",
        ttime=60,
        content=ContentType.DRAGON,
        target=TestTarget.MESH,
        volt_type=VoltageType.VBUMP,
        volt_IA=1.2,
        volt_CFC=1.1,
        freq_ia=2000,
        freq_cfc=1800
    )

@pytest.fixture
def sample_dragon_config():
    """Sample dragon configuration for testing"""
    return DragonConfiguration(
        dragon_pre_cmd="pre_command",
        dragon_post_cmd="post_command",
        ulx_path="/path/to/ulx",
        ulx_cpu="test_cpu",
        apic_cdie=1
    )