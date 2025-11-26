"""
Managers Package for S2TFlow
Provides VoltageManager, FrequencyManager, and ProductStrategy base class.

Usage:
    from managers import VoltageManager, FrequencyManager, ProductStrategy
    
    # Or import individually
    from managers.voltage_manager import VoltageManager
    from managers.frequency_manager import FrequencyManager
    from managers.product_strategy import ProductStrategy
"""

from .voltage_manager import VoltageManager
from .frequency_manager import FrequencyManager
from .product_strategy import ProductStrategy

__all__ = ['VoltageManager', 'FrequencyManager', 'ProductStrategy']
