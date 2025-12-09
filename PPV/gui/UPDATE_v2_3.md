# ExperimentBuilder v2.3 - Configuration-Driven Field Enabling

## Release Date: December 8, 2025

---

## 🎯 Changes Summary

### 1. **Moved Pseudo Config to Advanced Configuration Section** ✅

**Previous Location:** Test Configuration section  
**New Location:** Advanced Configuration section (grouped with Disable 2 Cores and Disable 1 Core)

**Why:** Pseudo Config is a product-specific advanced feature, similar to Disable Cores fields. Grouping them together makes more logical sense.

**New Field Order in Advanced Configuration:**
1. Configuration (Mask)
2. Boot Breakpoint
3. **Pseudo Config** ⬅️ MOVED HERE
4. Disable 2 Cores
5. Disable 1 Core
6. Check Core
7. Stop on Fail
8. Fuse File
9. Bios File

---

### 2. **Configuration-Driven Field Enabling** ✅

**New Feature:** `field_enable_config` in JSON configuration files

Instead of hardcoding product-specific field logic in Python, it's now defined in the configuration files. This makes it easy to modify which fields are enabled for each product without touching code.

### Configuration Format

```json
"field_enable_config": {
    "Field Name": ["Product1", "Product2"],
    "Another Field": ["Product3"]
}
```

### Current Configuration (All Three Files)

```json
"field_enable_config": {
    "Pseudo Config": ["GNR"],
    "Disable 2 Cores": ["CWF"],
    "Disable 1 Core": ["DMR"],
    "Core License": ["GNR", "DMR"]
}
```

---

## 📋 Product-Specific Field Matrix

| Field | GNR | CWF | DMR | Location |
|-------|-----|-----|-----|----------|
| **Pseudo Config** | ✅ | ❌ | ❌ | Advanced Configuration |
| **Disable 2 Cores** | ❌ | ✅ | ❌ | Advanced Configuration |
| **Disable 1 Core** | ❌ | ❌ | ✅ | Advanced Configuration |
| **Core License** | ✅ | ❌ | ✅ | Test Configuration |

**Legend:**
- ✅ = Field enabled (black text, normal state)
- ❌ = Field grayed out (gray text, disabled state)

---

## 🔧 Implementation Details

### Code Changes

#### ExperimentBuilder.py

**Modified `update_conditional_sections()` method:**

```python
# Gray out product-specific fields based on config
field_enable_config = self.config_template.get('field_enable_config', {})

# Apply product-specific field enabling from config
for field_name, field_info in widgets.items():
    if field_name in field_enable_config:
        enabled_products = field_enable_config[field_name]
        if current_product in enabled_products:
            # Enable field
        else:
            # Gray out field
```

**Benefits:**
1. **Centralized Configuration:** All field enabling rules in JSON
2. **Easy Modification:** Change product rules without editing Python code
3. **Backwards Compatible:** Falls back to legacy hardcoded logic if config missing
4. **Scalable:** Easy to add new products or fields

---

## 🎨 UI Changes

### Advanced Configuration Section

**Before:**
```
🔹 Advanced Configuration
  - Configuration (Mask)
  - Boot Breakpoint
  - Disable 2 Cores (CWF only)
  - Disable 1 Core (DMR only)
  - Check Core
  - Stop on Fail
  - Fuse File
  - Bios File
```

**After:**
```
🔹 Advanced Configuration
  - Configuration (Mask)
  - Boot Breakpoint
  - Pseudo Config (GNR only)      ⬅️ NEW POSITION
  - Disable 2 Cores (CWF only)
  - Disable 1 Core (DMR only)
  - Check Core
  - Stop on Fail
  - Fuse File
  - Bios File
```

### Test Configuration Section

**Before:**
```
🔹 Test Configuration
  ...
  - Core License
  - 600W Unit
  - Pseudo Config (GNR only)      ⬅️ OLD POSITION
```

**After:**
```
🔹 Test Configuration
  ...
  - Core License
  - 600W Unit
```

---

## 📝 Configuration File Updates

### All Three Files Updated:
- `PPV/configs/GNRControlPanelConfig.json`
- `PPV/configs/CWFControlPanelConfig.json`
- `PPV/configs/DMRControlPanelConfig.json`

### Added Section:

```json
"field_enable_config": {
    "Pseudo Config": ["GNR"],
    "Disable 2 Cores": ["CWF"],
    "Disable 1 Core": ["DMR"],
    "Core License": ["GNR", "DMR"]
}
```

---

## 🎓 How to Add New Product-Specific Fields

### Example: Adding "New Feature X" for GNR and DMR only

**Step 1:** Add field to data_types (if not already present)
```json
"data_types": {
    "New Feature X": ["bool"],
    ...
}
```

**Step 2:** Add to field_enable_config in all three files
```json
"field_enable_config": {
    "Pseudo Config": ["GNR"],
    "Disable 2 Cores": ["CWF"],
    "Disable 1 Core": ["DMR"],
    "Core License": ["GNR", "DMR"],
    "New Feature X": ["GNR", "DMR"]  // NEW
}
```

**Step 3:** Field automatically grays out for CWF, enabled for GNR/DMR

**No Python code changes needed!**

---

## 🧪 Testing Checklist

### Pseudo Config Location
- [ ] Open ExperimentBuilder
- [ ] Create new experiment
- [ ] Verify Pseudo Config is in Advanced Configuration section
- [ ] Verify it appears after Boot Breakpoint and before Disable 2 Cores
- [ ] Verify it's NOT in Test Configuration section

### Product-Specific Field Graying (Config-Driven)
- [ ] Set Product to GNR
  - [ ] Pseudo Config enabled (black)
  - [ ] Disable 2 Cores grayed out
  - [ ] Disable 1 Core grayed out
  - [ ] Core License enabled (black)
  
- [ ] Set Product to CWF
  - [ ] Pseudo Config grayed out
  - [ ] Disable 2 Cores enabled (black)
  - [ ] Disable 1 Core grayed out
  - [ ] Core License grayed out
  
- [ ] Set Product to DMR
  - [ ] Pseudo Config grayed out
  - [ ] Disable 2 Cores grayed out
  - [ ] Disable 1 Core enabled (black)
  - [ ] Core License enabled (black)

### Configuration Loading
- [ ] Switch between GNR/CWF/DMR
- [ ] Verify field enabling/graying updates immediately
- [ ] Create multiple experiments with different products
- [ ] Export to JSON and verify product-specific fields have correct values

---

## 🔄 Legacy Compatibility

### Fallback Mechanism

If `field_enable_config` is missing from JSON (old config files), the system falls back to hardcoded logic:

```python
if not field_enable_config:
    # Use legacy hardcoded field enabling logic
    if 'Pseudo Config' in widgets:
        if current_product == 'GNR':
            # Enable
        else:
            # Gray out
    # ... etc
```

This ensures old configuration files still work without modification.

---

## 📊 Benefits of Configuration-Driven Approach

### For Users
1. **Transparency:** Field enabling rules visible in JSON files
2. **Customization:** Easy to modify for specific workflows
3. **Documentation:** Config file serves as reference

### For Developers
1. **Maintainability:** No more hardcoded if/else chains
2. **Scalability:** Add new products by creating new JSON file
3. **Testing:** Field rules can be tested by modifying config without code changes
4. **Separation of Concerns:** Configuration separate from logic

### For Future Products
Adding a new product (e.g., "XYZ"):

1. Copy existing config JSON
2. Update PRODUCT field to "XYZ"
3. Modify field_enable_config as needed
4. Add "XYZ" to Product dropdown in Python
5. Done!

No complex code modifications required.

---

## 📦 Files Modified

### Python Files
- `PPV/gui/ExperimentBuilder.py`
  - Moved Pseudo Config field creation
  - Enhanced `update_conditional_sections()` with config-driven logic
  - Added legacy fallback for backwards compatibility

### Configuration Files
- `PPV/configs/GNRControlPanelConfig.json`
  - Added `field_enable_config` section
  
- `PPV/configs/CWFControlPanelConfig.json`
  - Added `field_enable_config` section
  
- `PPV/configs/DMRControlPanelConfig.json`
  - Added `field_enable_config` section

### Documentation Files
- `PPV/configs/README.md`
  - Added Field Enable Configuration section
  - Added examples and usage guide

---

## 🔮 Future Enhancements

### Potential Extensions

1. **Field Visibility Control:** Add `field_visibility_config` to completely hide fields instead of graying
2. **Conditional Sections:** Extend config to control section visibility by product
3. **Field Validation:** Add `field_validation_config` for product-specific value ranges
4. **Dynamic Options:** Allow dropdown options to vary by product (already partially implemented)
5. **Multi-Product Support:** Allow fields to be enabled for combinations (e.g., "GNR and CWF only")

### Example: Field Visibility Config

```json
"field_visibility_config": {
    "Pseudo Config": ["GNR"],
    "Disable 2 Cores": ["CWF"]
}
```

Fields not in the list for current product would be completely hidden from UI.

---

## ✅ Verification

All requested changes implemented:
- ✅ Pseudo Config moved to Advanced Configuration section
- ✅ Pseudo Config grouped with Disable 2/1 Core fields
- ✅ Configuration file created for enabling/disabling fields
- ✅ field_enable_config added to all three product JSON files
- ✅ Easy to modify which fields are enabled by product
- ✅ No code changes needed to add new product-specific fields

---

## 📚 Related Documentation

- Main tool guide: `PPV/gui/QUICK_REFERENCE_v2_1.md`
- Configuration guide: `PPV/configs/README.md`
- Previous updates: `PPV/gui/UPDATE_v2_2.md`
- Changelog: `PPV/gui/CHANGELOG_v2_1.md`

---

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**ExperimentBuilder Version:** v2.3
