# Quick Start Guide: Using the Refactored S2TFlow

This guide shows you how to quickly start using the new manager-based architecture.

## 1. Import the New Components

```python
# In SetTesterRegs.py or your test script
from ConfigsLoader import config
from managers import VoltageManager, FrequencyManager

# Get the product strategy
strategy = config.get_strategy()
```

## 2. Initialize Managers in S2TFlow

```python
class S2TFlow:
    def __init__(self, config, dpm, stc, scm, **kwargs):
        # Get product strategy
        self.strategy = config.get_strategy()
        
        # Initialize voltage manager
        self.voltage_mgr = VoltageManager(
            product_strategy=self.strategy,
            dpm_module=dpm,
            menus=self.Menus,  # Your existing menu dict
            features=config.FRAMEWORK_FEATURES
        )
        
        # Initialize frequency manager
        self.frequency_mgr = FrequencyManager(
            product_strategy=self.strategy,
            stc_module=stc,
            menus=self.Menus,
            features=config.FRAMEWORK_FEATURES
        )
        
        # ... rest of your init code
```

## 3. Replace Voltage Configuration

### Old Code (Remove)
```python
def set_voltage(self):
    computes = self.computes
    # ... 200+ lines of voltage configuration
    if self.use_ate_volt == False:
        if not external:
            print("Set System Voltage?")
            # ... many more lines
```

### New Code (Add)
```python
def set_voltage(self):
    # Initialize voltage tables
    self.voltage_mgr.init_voltage_tables(
        mode=self.mode,
        safe_volts_pkg=stc.All_Safe_RST_PKG,
        safe_volts_cdie=stc.All_Safe_RST_CDIE
    )
    
    # Configure voltage
    configured = self.voltage_mgr.configure_voltage(
        use_ate_volt=self.use_ate_volt,
        external=self.external,
        fastboot=self.fastboot,
        core_string=self.strategy.get_core_string(),
        input_func=input
    )
    
    if configured:
        # Get results back
        volt_dict = self.voltage_mgr.get_voltage_dict()
        self.volt_config = volt_dict['volt_config']
        self.custom_volt = volt_dict['custom_volt']
        self.vbumps_volt = volt_dict['vbumps_volt']
        self.ppvc_fuses = volt_dict['ppvc_fuses']
```

## 4. Replace Frequency Configuration

### Old Code (Remove)
```python
def set_frequency(self):
    if self.core_freq == None:
        # ... manual prompts
    if self.mesh_freq == None:
        # ... more prompts
```

### New Code (Add)
```python
def set_frequency(self):
    # Try ATE frequency first
    ate_configured = self.frequency_mgr.configure_ate_frequency(
        mode=self.mode,
        core_string=self.strategy.get_core_string(),
        input_func=input
    )
    
    # Fall back to manual if needed
    if not ate_configured:
        self.frequency_mgr.configure_manual_frequency(input_func=input)
    
    # Get results
    freq_dict = self.frequency_mgr.get_frequency_dict()
    self.core_freq = freq_dict['core_freq']
    self.mesh_freq = freq_dict['mesh_freq']
    self.io_freq = freq_dict['io_freq']
```

## 5. Use Product Strategy

### Old Code (Remove)
```python
# Product conditionals scattered throughout
if self.product == 'DMR':
    domains = ['cbb0', 'cbb1', 'cbb2', 'cbb3']
    core_string = 'MODULE'
elif self.product == 'GNR':
    domains = ['compute0', 'compute1', 'compute2']
    core_string = 'CORE'
```

### New Code (Add)
```python
# Strategy provides everything
domains = self.strategy.get_voltage_domains()
core_string = self.strategy.get_core_string()
domain_type = self.strategy.get_domain_display_name()

# Works for all products automatically!
print(f"Available {domain_type}s:")
for domain in domains:
    print(f"  {domain}")
```

## 6. Update Configuration Save/Load

### Old Code (Update)
```python
def save_config(self, file_path):
    config = {
        'mode': self.mode,
        # ... individual voltage fields
        'core_volt': self.core_volt,
        'mesh_cfc_volt': self.mesh_cfc_volt,
        # ... individual frequency fields
        'core_freq': self.core_freq,
        'mesh_freq': self.mesh_freq,
    }
```

### New Code (Better)
```python
def save_config(self, file_path):
    config = {
        'product': self.strategy.get_product_name(),
        'mode': self.mode,
        # Manager handles all voltage details
        'voltage': self.voltage_mgr.get_voltage_dict(),
        # Manager handles all frequency details
        'frequency': self.frequency_mgr.get_frequency_dict(),
        # ... other settings
    }
```

## 7. Test With All Products

```python
# Run your existing tests - they should work with all products:
# - GNR: compute-based, bigcore, "CORE"
# - CWF: compute-based, atomcore, "MODULE"
# - DMR: CBB-based, bigcore, "MODULE"

# The strategy automatically adapts the behavior
```

## Common Patterns

### Get Product-Specific Values
```python
# Instead of checking product name:
domains = self.strategy.get_voltage_domains()
max_cores = self.strategy.get_max_cores()
core_type = self.strategy.get_core_type()
```

### Validate Core/Module IDs
```python
# Instead of manual range checks:
if self.strategy.validate_core_id(core_id, id_type='physical'):
    # Valid core
```

### Check Product Capabilities
```python
# Instead of product conditionals:
if self.strategy.supports_600w_config():
    # Handle 600W configuration

if self.strategy.has_hdc_at_core():
    # HDC is at core level (atomcore)
else:
    # HDC is at uncore level (bigcore)
```

### Get Bootscript Configuration
```python
# Instead of hardcoded values:
bs_config = self.strategy.get_bootscript_config()
segment = bs_config['segment']
compute_config = bs_config['config']
```

## Testing Checklist

- [ ] Import managers successfully
- [ ] Strategy loads for current product
- [ ] Voltage configuration works
- [ ] Frequency configuration works
- [ ] Save/load configuration works
- [ ] Product-specific features work correctly
- [ ] Test with GNR (if available)
- [ ] Test with CWF (if available)
- [ ] Test with DMR (if available)

## Troubleshooting

### Import Errors
```python
# If managers can't be imported, add to path:
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'managers'))
```

### Strategy Returns None
```python
# Check that product is recognized:
strategy = config.get_strategy()
if strategy is None:
    print(f"No strategy for product: {config.PRODUCT_CONFIG}")
    # Add strategy to ConfigsLoader.get_strategy()
```

### Voltage/Frequency Not Configuring
```python
# Check feature flags:
print(config.FRAMEWORK_FEATURES['use_ate_volt'])
print(config.FRAMEWORK_FEATURES['use_ate_freq'])

# Make sure features are enabled for your product
```

## Examples

See these files for complete examples:
- **`S2TFlow_Refactoring_Example.py`** - Full refactored class example
- **`REFACTORING_GUIDE.md`** - Detailed migration guide
- **`REFACTORING_SUMMARY.md`** - Architecture summary

## Need Help?

1. Check `REFACTORING_GUIDE.md` for detailed explanations
2. Look at `S2TFlow_Refactoring_Example.py` for working code
3. Review strategy implementations in `product_specific/*/strategy.py`
4. Check manager implementations in `managers/*.py`

---

**Start small**: Migrate one method at a time, test thoroughly, then move to the next!
