# ConfigsLoader Migration Guide

## Overview
The `ConfigsLoader` module has been refactored to provide cleaner access to product configurations through a centralized `ProductConfiguration` class.

---

## ✅ New Pattern (Recommended)

### **Import the config object:**
```python
from users.gaespino.dev.S2T.ConfigsLoader import config
```

### **Access configuration values:**
```python
# Product information
product_name = config.PRODUCT_CONFIG
product_chop = config.PRODUCT_CHOP
selected_product = config.SELECTED_PRODUCT

# Configuration values
max_cores = config.MAXCORESCHIP
max_logical = config.MAXLOGICAL
chip_config = config.CHIPCONFIG

# Mappings
log2phy = config.classLogical2Physical
phy2log = config.physical2ClassLogical
phy2colrow = config.phys2colrow

# DMR specific
mods_per_cbb = config.MODS_PER_CBB
max_cbbs = config.MAX_CBBS
max_imhs = config.MAX_IMHS

# Fuses
fuses = config.FUSES
debug_mask = config.DEBUGMASK
fuses_600w = config.FUSES_600W_COMP

# Framework variables
license_dict = config.LICENSE_DICT
license_levels = config.LICENSE_LEVELS
bootscript_data = config.BOOTSCRIPT_DATA

# Get functions and registers (lazy loaded)
product_functions = config.get_functions()
product_registers = config.get_registers()
```

---

## 🔄 Migration Examples

### **Before (Old Pattern):**
```python
import users.gaespino.dev.S2T.ConfigsLoader as LoadConfig

PRODUCT_CONFIG = LoadConfig.PRODUCT_CONFIG
PRODUCT_CHOP = LoadConfig.PRODUCT_CHOP
CONFIG = LoadConfig.CONFIG
ConfigFile = LoadConfig.ConfigFile
CORESTRING = LoadConfig.CORESTRING
CORETYPES = LoadConfig.CORETYPES
CHIPCONFIG = LoadConfig.CHIPCONFIG
MAXCORESCHIP = LoadConfig.MAXCORESCHIP
MAXLOGICAL = LoadConfig.MAXLOGICAL
# ... 30+ more lines ...

pf = LoadConfig.LoadFunctions()
reg = LoadConfig.LoadRegisters()
```

### **After (New Pattern):**
```python
from users.gaespino.dev.S2T.ConfigsLoader import config

# Use config object directly throughout your code
# No need to create local copies unless you want shortcuts
product_name = config.PRODUCT_CONFIG
max_cores = config.MAXCORESCHIP

# Get functions/registers when needed
pf = config.get_functions()
reg = config.get_registers()
```

### **Alternative (Creating Local Shortcuts):**
```python
from users.gaespino.dev.S2T.ConfigsLoader import config

# Create local shortcuts only for frequently used values
PRODUCT_CONFIG = config.PRODUCT_CONFIG
MAXCORESCHIP = config.MAXCORESCHIP
CORETYPES = config.CORETYPES
pf = config.get_functions()

# Use shortcuts in your code
if PRODUCT_CONFIG == 'DMR':
    # do something
```

---

## 🎯 Benefits

### **1. Reduced Boilerplate**
- **Before:** 40+ lines of repetitive assignments in each file
- **After:** 1 import line, access values as needed

### **2. Single Source of Truth**
- All configuration in one place
- No duplicate variable declarations
- Easier to maintain and update

### **3. Lazy Loading**
- Functions and registers loaded only when needed
- Better performance for scripts that don't use them

### **4. Better Organization**
- Clear namespace: `config.ATTRIBUTE_NAME`
- Self-documenting code
- IDE autocomplete support

### **5. Easier Testing**
- Can mock the config object
- No need to mock 40+ individual variables

---

## 📦 Available Attributes

### **Product Identification:**
- `config.PRODUCT_CONFIG` - Full product name
- `config.PRODUCT_CHOP` - Product chop
- `config.PRODUCT_VARIANT` - Product variant
- `config.SELECTED_PRODUCT` - Product without variant
- `config.ROOT_PATH` - Module root path
- `config.PRODUCT_PATH` - Product-specific path

### **Configuration:**
- `config.CONFIG` - Full configuration dictionary
- `config.ConfigFile` - Configuration file path
- `config.CORESTRING` - Core string identifier
- `config.CORETYPES` - All core types dictionary
- `config.CHIPCONFIG` - Current chip configuration
- `config.MAXCORESCHIP` - Maximum cores per chip
- `config.MAXLOGICAL` - Maximum logical cores
- `config.MAXPHYSICAL` - Maximum physical cores
- `config.classLogical2Physical` - Logical to physical mapping
- `config.physical2ClassLogical` - Physical to logical mapping
- `config.Physical2apicIDAssignmentOrder10x5` - APIC ID assignment
- `config.phys2colrow` - Physical to column/row mapping
- `config.skip_physical_modules` - Modules to skip

### **DMR Specific:**
- `config.MODS_PER_CBB` - Modules per CBB
- `config.MODS_PER_COMPUTE` - Modules per compute
- `config.MODS_ACTIVE_PER_CBB` - Active modules per CBB
- `config.MAX_CBBS` - Maximum CBBs
- `config.MAX_IMHS` - Maximum IMHs

### **Fuses:**
- `config.FUSES` - All fuses dictionary
- `config.DEBUGMASK` - Debug masks
- `config.PSEUDOCONDFIGS` - Pseudo configurations
- `config.BURINFUSES` - Burn-in fuses
- `config.FUSE_INSTANCE` - Fuse instance
- `config.CFC_RATIO_CURVES` - CFC ratio curves
- `config.CFC_VOLTAGE_CURVES` - CFC voltage curves
- `config.IA_RATIO_CURVES` - IA ratio curves
- `config.IA_RATIO_CONFIG` - IA ratio configuration
- `config.IA_VOLTAGE_CURVES` - IA voltage curves
- `config.FUSES_600W_COMP` - 600W compute fuses
- `config.FUSES_600W_IO` - 600W IO fuses
- `config.HIDIS_COMP` - HT disable compute fuses
- `config.HTDIS_IO` - HT disable IO fuses
- `config.VP2INTERSECT` - VP2INTERSECT configuration

### **Framework Variables:**
- `config.FRAMEWORKVARS` - All framework variables
- `config.LICENSE_DICT` - License dictionary
- `config.LICENSE_S2T_MENU` - License S2T menu
- `config.LICENSE_LEVELS` - License levels
- `config.SPECIAL_QDF` - Special QDF configuration
- `config.VALIDCLASS` - Valid class configurations
- `config.CUSTOMS` - Custom configurations
- `config.VALIDROWS` - Valid rows
- `config.VALIDCOLS` - Valid columns
- `config.BOOTSCRIPT_DATA` - Bootscript data
- `config.ATE_MASKS` - ATE masks
- `config.ATE_CONFIG` - ATE configuration
- `config.DIS2CPM_MENU` - Disable 2CPM menu
- `config.DIS2CPM_DICT` - Disable 2CPM dictionary
- `config.RIGHT_HEMISPHERE` - Right hemisphere config
- `config.LEFT_HEMISPHERE` - Left hemisphere config

### **Framework Features:**
- `config.FRAMEWORK_FEATURES` - All framework features

### **Methods:**
- `config.get_functions()` - Get product-specific functions
- `config.get_registers()` - Get product-specific registers
- `config.reload()` - Reload all product-specific modules

---

## 🔧 Backward Compatibility

**All existing code continues to work!**

The old pattern is still supported through a backward compatibility layer:

```python
import users.gaespino.dev.S2T.ConfigsLoader as LoadConfig

# These still work
PRODUCT_CONFIG = LoadConfig.PRODUCT_CONFIG
pf = LoadConfig.LoadFunctions()
```

This allows gradual migration without breaking existing scripts.

---

## 📝 Migration Checklist

### **For New Scripts:**
- ✅ Use `from ConfigsLoader import config`
- ✅ Access values via `config.ATTRIBUTE_NAME`
- ✅ Use `config.get_functions()` and `config.get_registers()`

### **For Existing Scripts (Optional Migration):**
1. Replace import: `import ConfigsLoader as LoadConfig` → `from ConfigsLoader import config`
2. Remove variable assignment blocks (40+ lines)
3. Update references: `ATTRIBUTE` → `config.ATTRIBUTE`
4. Update function calls: `LoadConfig.LoadFunctions()` → `config.get_functions()`

---

## 🎓 Example: Full File Refactoring

### **Before:**
```python
import users.gaespino.dev.S2T.ConfigsLoader as LoadConfig

PRODUCT_CONFIG = LoadConfig.PRODUCT_CONFIG
PRODUCT_CHOP = LoadConfig.PRODUCT_CHOP
CONFIG = LoadConfig.CONFIG
ConfigFile = LoadConfig.ConfigFile
CORESTRING = LoadConfig.CORESTRING
CORETYPES = LoadConfig.CORETYPES
CHIPCONFIG = LoadConfig.CHIPCONFIG
MAXCORESCHIP = LoadConfig.MAXCORESCHIP
MAXLOGICAL = LoadConfig.MAXLOGICAL
MAXPHYSICAL = LoadConfig.MAXPHYSICAL
# ... 30 more lines ...

pf = LoadConfig.LoadFunctions()

def my_function():
    if PRODUCT_CONFIG == 'DMR':
        cores = MAXCORESCHIP
        pf.do_something()
```

### **After:**
```python
from users.gaespino.dev.S2T.ConfigsLoader import config

def my_function():
    if config.PRODUCT_CONFIG == 'DMR':
        cores = config.MAXCORESCHIP
        config.get_functions().do_something()
```

**Result:** From ~50 lines to ~7 lines! 🎉

---

## 🚀 Next Steps

1. **Try it in new scripts** - Use the `config` object pattern
2. **Optionally migrate existing scripts** - Remove boilerplate, use `config` object
3. **Report issues** - If something doesn't work as expected

The backward compatibility layer ensures nothing breaks during migration!
