from typing import List, Optional
from ..core.interfaces import IContentBuilder
from .configurations import DragonConfiguration, LinuxConfiguration

class TestContentBuilder(IContentBuilder):
    """Utility class for processing and creating content files"""
    
    def __init__(self, data, dragon_config=None, linux_config=None, 
                 custom_config=None, logger=None, flow=None, core=None):
        self.logger = print if logger is None else logger
        self._data = data
        self._dragon_config = dragon_config
        self._linux_config = linux_config
        self._custom_config = custom_config
        self._flow = flow
        self._core = core

    def generate_ttl_configuration(self, content):
        self.logger(f">>> Generating TTL Config for: {content}", 1)
        if content.lower() == 'dragon':
            config = self.generate_dragon_config()
        elif content.lower() == 'linux':
            config = self.generate_linux_config()
        elif content.lower() == 'custom':
            config = self.generate_custom_config()
        else:
            config = None
        return config
    
    def generate_dragon_config(self) -> Optional[DragonConfiguration]:
        if self._dragon_config is None:
            self.logger(">>> Dragon Configuration not selected", 3)
            return None
        
        self.logger(">>> Generating Dragon TTL Configuration", 1)
        if self._flow and self._flow.upper() == "SLICE" and self._core:
            # Import here to avoid circular dependencies
            import users.gaespino.dev.S2T.dpmChecks as dpm
            apic_cdie = dpm.get_compute_index(self._core)
            self.logger(f">>> Setting APIC CDIE to compute: {apic_cdie}", 1)
            setattr(self._dragon_config, 'apic_cdie', apic_cdie)
        else:
            self.logger(f">>> APIC CDIE is not required when using flow: {self._flow.upper()}", 1)
        
        self._generate_config(self._dragon_config)
        return self._dragon_config
            
    def generate_linux_config(self) -> Optional[LinuxConfiguration]:
        if self._linux_config is None:
            self.logger(">>> Linux Configuration not selected", 3)
            return None
        
        self.logger(">>> Generating Linux TTL Configuration", 1)
        self._generate_config(self._linux_config)
        return self._linux_config

    def generate_custom_config(self) -> Optional[object]:
        if self._custom_config is None:
            self.logger(">>> Custom Configuration not selected", 3)
            return None
        
        self.logger(">>> Generating Custom TTL Configuration", 1)
        self._generate_config(self._custom_config)
        return self._custom_config

    def _generate_config(self, config) -> List:
        for key, value in self._data.items():
            print(key, ' : ', value)
            if hasattr(config, key):
                setattr(config, key, value)
        return config