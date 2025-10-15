from typing import Dict, Any
from ..strategies.loop_strategy import LoopTestStrategy
from ..strategies.sweep_strategy import SweepTestStrategy
from ..strategies.shmoo_strategy import ShmooTestStrategy
from ..content.content_builder import TestContentBuilder
from ..execution.test_executor import TestExecutor

class StrategyFactory:
    """Factory for creating test strategies"""
    
    @staticmethod
    def create_strategy(strategy_type: str, **kwargs):
        """Create strategy based on type"""
        if strategy_type.lower() == 'loops':
            return LoopTestStrategy(kwargs.get('loops', 5))
        elif strategy_type.lower() == 'sweep':
            return SweepTestStrategy(
                kwargs.get('ttype', 'frequency'),
                kwargs.get('domain', 'ia'),
                kwargs.get('start', 16),
                kwargs.get('end', 39),
                kwargs.get('step', 4)
            )
        elif strategy_type.lower() == 'shmoo':
            return ShmooTestStrategy(
                kwargs.get('x_config', {}),
                kwargs.get('y_config', {})
            )
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

class ContentBuilderFactory:
    """Factory for creating content builders"""
    
    @staticmethod
    def create_builder(data, dragon_config=None, linux_config=None, 
                      custom_config=None, logger=None, flow=None, core=None):
        """Create content builder"""
        return TestContentBuilder(
            data=data,
            dragon_config=dragon_config,
            linux_config=linux_config,
            custom_config=custom_config,
            logger=logger,
            flow=flow,
            core=core
        )

class ExecutorFactory:
    """Factory for creating test executors"""
    
    @staticmethod
    def create_executor(config, s2t_config, cancel_flag=None):
        """Create test executor"""
        return TestExecutor(
            config=config,
            s2t_config=s2t_config,
            cancel_flag=cancel_flag
        )