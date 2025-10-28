# S2TFlow Refactoring Guide

## Overview

This document describes the architectural refactoring of the S2TFlow class to enable easier product integration and maintenance. The refactoring introduces **managers** for voltage and frequency handling, and a **strategy pattern** for product-specific implementations.

## Table of Contents

1. [Motivation](#motivation)
2. [Architecture Overview](#architecture-overview)
3. [New Components](#new-components)
4. [Product Strategy Pattern](#product-strategy-pattern)
5. [Migration Guide](#migration-guide)
6. [Adding New Products](#adding-new-products)
7. [Examples](#examples)

---

## Motivation

### Problems with Original Design

The original `S2TFlow` class had several issues:

1. **Monolithic voltage/frequency configuration** - 500+ lines of inline voltage and frequency logic
2. **Product-specific conditionals scattered throughout** - Hard to track which code applies to which product
3. **Duplicate logic** - Similar operations repeated for GNR, CWF, DMR
4. **Tight coupling** - Product differences (computes vs CBBs) hardcoded everywhere
5. **Difficult to extend** - Adding a new product required changes in many places

### Goals of Refactoring

1. **Separation of concerns** - Voltage, frequency, and product-specific logic in separate modules
2. **Reusability** - Common voltage/frequency operations shared across products
3. **Extensibility** - Easy to add new products by implementing a strategy
4. **Maintainability** - Product differences isolated in strategy implementations
5. **Testability** - Managers and strategies can be tested independently

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       S2TFlow Class                         │
│  (Orchestrates flow, delegates to managers and strategy)   │
└────────────┬─────────────────────────┬──────────────────────┘
             │                         │
   ┌─────────▼──────────┐   ┌─────────▼──────────┐
   │  VoltageManager    │   │ FrequencyManager   │
   │                    │   │                    │
   │ - Fixed voltage    │   │ - ATE frequency    │
   │ - Voltage bumps    │   │ - Manual frequency │
   │ - PPVC fuses       │   │ - Ratio calc       │
   │ - Uncore voltages  │   │ - Validation       │
   └─────────┬──────────┘   └─────────┬──────────┘
             │                         │
             │    ┌────────────────────▼──────────┐
             └────►   ProductStrategy (Abstract)  │
                  │                                │
                  │ - Domain structure (ABC)      │
                  │ - Core/module management      │
                  │ - Product capabilities        │
                  └────────┬───────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
   ┌─────▼──────┐   ┌─────▼──────┐   ┌──────▼──────┐
   │GNRStrategy │   │CWFStrategy │   │ DMRStrategy │
   │            │   │            │   │             │
   │- Computes  │   │- Computes  │   │- CBBs       │
   │- Bigcore   │   │- Atomcore  │   │- Bigcore    │
   │- CORE      │   │- MODULE    │   │- MODULE     │
   └────────────┘   └────────────┘   └─────────────┘
```

---

## New Components

### 1. VoltageManager (`managers/voltage_manager.py`)

**Responsibilities:**
- Initialize voltage tables and safe values
- Configure fixed voltages
- Configure voltage bumps (vbumps)
- Configure PPVC fuses
- Manage uncore (CFC/HDC) voltages
- Validate voltage ranges

**Key Methods:**
```python
voltage_mgr.init_voltage_tables(mode='mesh', safe_volts_pkg, safe_volts_cdie)
voltage_mgr.configure_voltage(use_ate_volt, external, fastboot, ...)
voltage_mgr.configure_uncore_voltages(vbumps, fixed, external, ...)
voltage_mgr.check_vbumps(value)
voltage_mgr.get_voltage_dict()  # Get all voltage settings
voltage_mgr.set_from_dict(dict) # Restore from saved config
```

**Benefits:**
- All voltage logic in one place
- Reusable across slice and mesh modes
- Product differences handled via strategy
- Easy to add new voltage options

### 2. FrequencyManager (`managers/frequency_manager.py`)

**Responsibilities:**
- Display ATE frequency tables
- Configure ATE frequencies
- Configure manual frequencies
- Handle flow ID for multi-frequency configs
- Validate frequency values

**Key Methods:**
```python
freq_mgr.display_ate_frequencies(mode='mesh', core_string='Core')
freq_mgr.configure_ate_frequency(mode, core_string, input_func)
freq_mgr.configure_manual_frequency(input_func)
freq_mgr.get_ratios_for_ate(ate_freq, flowid, mode)
freq_mgr.get_frequency_dict()  # Get all frequency settings
freq_mgr.set_from_dict(dict)   # Restore from saved config
```

**Benefits:**
- Centralized frequency management
- Consistent ATE and manual frequency handling
- Product-specific frequency tables from STC module
- Clean separation from voltage logic

### 3. ProductStrategy (`managers/product_strategy.py`)

**Abstract base class defining the interface for product-specific implementations.**

**Key Abstract Methods:**
```python
# Product identification
get_product_name() -> str
get_core_type() -> str  # 'bigcore' or 'atomcore'
get_core_string() -> str  # 'CORE' or 'MODULE'

# Domain structure
get_voltage_domains() -> List[str]  # ['compute0', ...] or ['cbb0', ...]
get_domain_display_name() -> str  # 'Compute' or 'CBB'
format_domain_name(domain) -> str

# Core management
logical_to_physical(logical_id) -> int
physical_to_logical(physical_id) -> int
physical_to_colrow(physical_id) -> List[int]

# Product capabilities
has_hdc_at_core() -> bool
supports_600w_config() -> bool
supports_hyperthreading() -> bool
supports_2cpm() -> bool

# Configuration
get_bootscript_config() -> Dict
get_valid_ate_masks() -> List[str]
init_voltage_config() -> Dict
```

**Strategy Pattern Benefits:**
- Isolates product differences
- Easy to add new products (just implement interface)
- No product-specific conditionals in main code
- Consistent API across all products

### 4. Concrete Strategies

#### GNRStrategy (`product_specific/gnr/strategy.py`)
- Uses `compute0`, `compute1`, `compute2` domains
- Bigcore architecture
- HDC at uncore level
- Supports 600W configuration
- "CORE" terminology

#### CWFStrategy (`product_specific/cwf/strategy.py`)
- Uses `compute0`, `compute1`, `compute2` domains
- Atomcore architecture
- HDC at core (L2) level
- "MODULE" terminology
- AtomID mapping support

#### DMRStrategy (`product_specific/dmr/strategy.py`)
- Uses `cbb0`, `cbb1`, `cbb2`, `cbb3` domains (AP) or `cbb0`, `cbb1` (SP)
- Bigcore architecture
- HDC at uncore level
- "MODULE" terminology
- CBB-specific methods: `get_modules_per_cbb()`, `get_max_cbbs()`, etc.

---

## Product Strategy Pattern

### Why Strategy Pattern?

The strategy pattern allows us to:
1. **Encapsulate product-specific behavior** in separate classes
2. **Select the appropriate strategy at runtime** based on detected product
3. **Avoid conditional logic** scattered throughout the codebase
4. **Make adding new products straightforward** - just implement the interface

### Before (Hardcoded Product Logic)

```python
# OLD CODE - Product logic mixed into main class
def set_voltage(self):
    # Different domain names per product
    if self.product == 'DMR':
        domains = ['cbb0', 'cbb1', 'cbb2', 'cbb3']
        domain_type = 'CBB'
    else:
        domains = ['compute0', 'compute1', 'compute2']
        domain_type = 'Compute'
    
    # Different core strings
    if self.product == 'GNR':
        core_string = 'CORE'
    else:
        core_string = 'MODULE'
    
    # Different HDC locations
    if self.product == 'CWF':
        hdc_at_core = True
    else:
        hdc_at_core = False
    
    # ... more product-specific logic ...
```

### After (Strategy Pattern)

```python
# NEW CODE - Product logic in strategy
def set_voltage(self):
    # Strategy provides product-specific info
    domains = self.strategy.get_voltage_domains()
    domain_type = self.strategy.get_domain_display_name()
    core_string = self.strategy.get_core_string()
    hdc_at_core = self.strategy.has_hdc_at_core()
    
    # Rest of logic is product-agnostic
    self.voltage_mgr.configure_voltage(...)
```

---

## Migration Guide

### Step 1: Update ConfigsLoader Usage

```python
# OLD
from ConfigsLoader import config
computes = sv.socket0.computes.name

# NEW
from ConfigsLoader import config
strategy = config.get_strategy()
domains = strategy.get_voltage_domains()  # Works for computes or CBBs
```

### Step 2: Replace Inline Voltage Logic

```python
# OLD - 200+ lines of inline voltage configuration
def set_voltage(self):
    if self.use_ate_volt == False:
        print("Set System Voltage?")
        print("\t> 1. No")
        print("\t> 2. Fixed Voltage")
        # ... 200 more lines ...
        
# NEW - Delegated to manager
def set_voltage(self):
    self.voltage_mgr.init_voltage_tables(
        mode=self.mode,
        safe_volts_pkg=self.stc.All_Safe_RST_PKG,
        safe_volts_cdie=self.stc.All_Safe_RST_CDIE
    )
    
    self.voltage_mgr.configure_voltage(
        use_ate_volt=self.use_ate_volt,
        external=self.external,
        fastboot=self.fastboot,
        core_string=self.strategy.get_core_string(),
        input_func=input
    )
    
    # Get results
    volt_dict = self.voltage_mgr.get_voltage_dict()
    self.volt_config = volt_dict['volt_config']
```

### Step 3: Replace Inline Frequency Logic

```python
# OLD - Mixed ATE and manual frequency logic
def set_frequency(self):
    if self.use_ate_freq:
        print("ATE frequencies:")
        # Display frequency table
        # Get user input
        # Calculate ratios
        # ... many lines ...
    else:
        # Manual frequency input
        # ... more lines ...

# NEW - Delegated to manager
def set_frequency(self):
    # Try ATE first
    ate_configured = self.frequency_mgr.configure_ate_frequency(
        mode=self.mode,
        core_string=self.strategy.get_core_string(),
        input_func=input
    )
    
    if not ate_configured:
        # Fall back to manual
        self.frequency_mgr.configure_manual_frequency(input_func=input)
    
    # Get results
    freq_dict = self.frequency_mgr.get_frequency_dict()
    self.core_freq = freq_dict['core_freq']
    self.mesh_freq = freq_dict['mesh_freq']
    self.io_freq = freq_dict['io_freq']
```

### Step 4: Replace Product-Specific Conditionals

```python
# OLD - Conditionals everywhere
if self.product == 'DMR':
    print("Available CBBs:")
    for cbb in cbbs:
        print(f"  {cbb}")
else:
    print("Available Computes:")
    for compute in computes:
        print(f"  {compute}")

# NEW - Strategy handles it
print(f"Available {self.strategy.get_domain_display_name()}s:")
for domain in self.strategy.get_voltage_domains():
    print(f"  {domain}")
```

### Step 5: Update Save/Load Configuration

```python
# OLD - Manual voltage/frequency saving
def save_config(self):
    config = {
        'core_volt': self.core_volt,
        'mesh_cfc_volt': self.mesh_cfc_volt,
        # ... many individual fields ...
    }

# NEW - Manager handles details
def save_config(self):
    config = {
        'voltage': self.voltage_mgr.get_voltage_dict(),
        'frequency': self.frequency_mgr.get_frequency_dict(),
        # ... other settings ...
    }
```

---

## Adding New Products

### Steps to Add a New Product (e.g., "NPU")

#### 1. Create Product Configuration

Create `product_specific/npu/configs.py`:

```python
CONFIG_PRODUCT = 'NPU'

class configurations:
    def __init__(self, product):
        self.product = product
        # ... configuration methods ...
    
    def init_product_specific(self):
        # Define NPU-specific structure
        CORETYPES = {
            'NPU': {
                'core': 'neuralcore',
                'config': 'AP',
                'maxcores': 256,
                'maxlogcores': 512,
                # NPU-specific fields
                'modules_per_tile': 16,
                'max_tiles': 16
            }
        }
        # ... more configuration ...
```

#### 2. Create Product Strategy

Create `product_specific/npu/strategy.py`:

```python
from product_strategy import ProductStrategy

class NPUStrategy(ProductStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.product_config = config.CORETYPES[config.PRODUCT_CONFIG]
    
    def get_product_name(self) -> str:
        return 'NPU'
    
    def get_core_type(self) -> str:
        return 'neuralcore'
    
    def get_core_string(self) -> str:
        return 'NEURON'  # NPU uses "NEURON" terminology
    
    def get_voltage_domains(self) -> List[str]:
        # NPU uses tile-based structure
        max_tiles = self.product_config['max_tiles']
        return [f'tile{i}' for i in range(max_tiles)]
    
    def get_domain_display_name(self) -> str:
        return 'Tile'
    
    # ... implement all other required methods ...
    
    def has_hdc_at_core(self) -> bool:
        return False  # NPU doesn't have traditional HDC
    
    # NPU-specific method
    def get_modules_per_tile(self) -> int:
        return self.product_config['modules_per_tile']
```

#### 3. Register Strategy in ConfigsLoader

Edit `ConfigsLoader.py`:

```python
def get_strategy(self):
    if self._strategy is None:
        try:
            if 'GNR' in SELECTED_PRODUCT:
                from gnr.strategy import GNRStrategy
                self._strategy = GNRStrategy(self)
            elif 'CWF' in SELECTED_PRODUCT:
                from cwf.strategy import CWFStrategy
                self._strategy = CWFStrategy(self)
            elif 'DMR' in SELECTED_PRODUCT:
                from dmr.strategy import DMRStrategy
                self._strategy = DMRStrategy(self)
            elif 'NPU' in SELECTED_PRODUCT:  # ADD THIS
                from npu.strategy import NPUStrategy
                self._strategy = NPUStrategy(self)
            else:
                raise ValueError(f"No strategy for: {SELECTED_PRODUCT}")
        except Exception as e:
            print(f"Warning: Could not load strategy: {e}")
    return self._strategy
```

#### 4. Use in S2TFlow

That's it! The rest of the code automatically adapts:

```python
# This code now works for NPU without any changes
flow = S2TFlow(config=config, ...)

# Automatically uses "NEURON" terminology
flow.set_frequency()  # Displays "NEURON Frequency"

# Automatically uses tile0, tile1, ... domains
flow.set_voltage()  # Configures tile-based voltages

# Displays "Available Tiles:"
flow.display_available_cores(array)
```

---

## Examples

### Example 1: Voltage Configuration

```python
# Initialize S2TFlow with managers
flow = S2TFlowRefactored(
    config=config,
    dpm_module=dpm,
    stc_module=stc,
    scm_module=scm
)

# Configure voltage - works for all products
flow.set_voltage()

# For GNR: Uses compute0/compute1/compute2, "CORE" terminology
# For CWF: Uses compute0/compute1/compute2, "MODULE" terminology, HDC at core
# For DMR: Uses cbb0/cbb1/cbb2/cbb3, "MODULE" terminology
```

### Example 2: Quick Voltage Bumps (External Tool)

```python
# Set voltage bumps programmatically
flow.set_voltage_quick(
    core_vbump=0.1,  # +100mV on core
    mesh_vbump=0.05  # +50mV on uncore
)

# Works for all products:
# - GNR: Applies to computes
# - CWF: Applies to computes, HDC at core level
# - DMR: Applies to CBBs
```

### Example 3: ATE Frequency Configuration

```python
# Configure using ATE frequencies
flow.frequency_mgr.configure_ate_frequency(
    mode='mesh',
    core_string=flow.strategy.get_core_string()
)

# Displays appropriate frequency table for product
# Handles multi-frequency configs (F5, F6, F7) automatically
```

### Example 4: Product-Agnostic Core Display

```python
# Display available cores/modules
flow.display_available_cores(array)

# GNR output:
# ┌──────────┬──────┬───────────────┐
# │ Compute  │ Type │ Physical Cores│
# ├──────────┼──────┼───────────────┤
# │ compute0 │ CORES│ 0, 1, 2, ...  │
# └──────────┴──────┴───────────────┘

# DMR output:
# ┌──────┬──────┬─────────────────┐
# │ CBB  │ Type │ Physical Modules│
# ├──────┼──────┼─────────────────┤
# │ cbb0 │ MODS │ 0, 1, 2, ...    │
# └──────┴──────┴─────────────────┘
```

### Example 5: Save and Load Configuration

```python
# Save configuration
flow.save_config('my_config.json')

# Saved config includes:
# - Product name (for validation)
# - All voltage settings (from VoltageManager)
# - All frequency settings (from FrequencyManager)
# - Other flow settings

# Load configuration
flow.load_config('my_config.json')

# Automatically restores manager states
# Validates product compatibility
```

---

## Benefits Summary

### For Developers

1. **Less code duplication** - Voltage/frequency logic written once
2. **Easier debugging** - Logic isolated in managers
3. **Faster development** - Add features in one place
4. **Better testing** - Managers and strategies testable independently

### For Product Integration

1. **Clear integration path** - Implement strategy interface
2. **No impact on existing code** - New products don't break old ones
3. **Documented differences** - Strategy documents product capabilities
4. **Validation built-in** - Strategy validates product-specific constraints

### For Maintenance

1. **Centralized logic** - Voltage changes in VoltageManager, frequency in FrequencyManager
2. **Easier refactoring** - Can change manager internals without touching S2TFlow
3. **Better documentation** - Each component has clear responsibilities
4. **Reduced complexity** - S2TFlow orchestrates instead of implementing

---

## Migration Checklist

- [ ] Update imports to include managers
- [ ] Initialize VoltageManager and FrequencyManager in `__init__`
- [ ] Replace inline voltage configuration with `voltage_mgr.configure_voltage()`
- [ ] Replace inline frequency configuration with `frequency_mgr.configure_ate_frequency()`
- [ ] Replace product conditionals with strategy method calls
- [ ] Update `save_config()` to use manager `get_*_dict()` methods
- [ ] Update `load_config()` to use manager `set_from_dict()` methods
- [ ] Test with each product (GNR, CWF, DMR)
- [ ] Update documentation and examples

---

## Reference Files

- **VoltageManager**: `managers/voltage_manager.py`
- **FrequencyManager**: `managers/frequency_manager.py`
- **ProductStrategy**: `managers/product_strategy.py`
- **GNRStrategy**: `product_specific/gnr/strategy.py`
- **CWFStrategy**: `product_specific/cwf/strategy.py`
- **DMRStrategy**: `product_specific/dmr/strategy.py`
- **ConfigsLoader**: `ConfigsLoader.py` (updated)
- **Example**: `S2TFlow_Refactoring_Example.py`

---

## Next Steps

1. **Gradual migration** - Migrate one method at a time to minimize risk
2. **Testing** - Test each migrated method with all products
3. **Documentation** - Update method docstrings as you migrate
4. **Code review** - Review changes for consistency with patterns
5. **Performance** - Profile to ensure no performance regression

---

## Questions?

For questions or clarifications about the refactoring:
1. Review `S2TFlow_Refactoring_Example.py` for complete examples
2. Check strategy implementations for product-specific details
3. Look at manager classes for voltage/frequency operations

---

*Last updated: [Date]*
*Version: 0.1*
