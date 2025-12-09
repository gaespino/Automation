# ExperimentBuilder v2.2 Update - Bug Fixes & Workflow Improvements

## Release Date: December 8, 2025

---

## 🎯 Changes Summary

### 1. **Auto-Apply Unit Data** ✅
**Previous Behavior**: Required clicking "Apply to Current Experiment" button
**New Behavior**: Unit Data automatically applies to ALL experiments in real-time

**Changes:**
- Removed "Apply to Current Experiment" button
- Added info label: "Unit Data applies to all experiments automatically"
- Unit Data widgets now have `FocusOut` and `ComboboxSelected` event bindings
- Changes propagate immediately to all experiment tabs

**Why This Matters:**
- Unit Data is shared across all experiments (Product, Visual ID, Bucket, COM Port, IP Address)
- No need to manually apply - just change the value and it updates everywhere
- Prevents inconsistency between experiments

---

### 2. **Fixed Tooltip Bug** ✅
**Issue**: Tooltips sometimes remained visible after cursor left widget
**Root Cause**: Tooltip window not properly destroyed and reference not cleared

**Fix:**
```python
def on_leave(event):
    if hasattr(widget, 'tooltip'):
        try:
            widget.tooltip.destroy()
            del widget.tooltip  # Clear reference
        except:
            pass
```

**Result**: Tooltips now properly disappear when cursor leaves widget

---

### 3. **Reorganized Section Order** ✅
**Previous Order:**
1. Basic Information
2. Test Configuration
3. Voltage & Frequency
4. ...
5. Advanced Configuration

**New Order:**
1. Basic Information
2. **Advanced Configuration** ⬅️ MOVED HERE
3. Test Configuration
4. Voltage & Frequency
5. ...

**Why**: Advanced Configuration contains critical fields (Configuration Mask, Check Core, Disable Cores) that should be near the top for easier access

---

### 4. **Product-Specific Field Graying** ✅
**New Behavior**: Fields not used by current product are grayed out and disabled

| Field | Enabled For | Grayed For |
|-------|-------------|------------|
| **Pseudo Config** | GNR | CWF, DMR |
| **Disable 2 Cores** | CWF | GNR, DMR |
| **Disable 1 Core** | DMR | GNR, CWF |
| **Core License** | GNR, DMR | CWF |

**Visual Feedback:**
- Disabled: `state='disabled'`, `fg='#cccccc'` (gray)
- Enabled: `state='normal'`, `fg='black'`

**Why**: Prevents users from entering values in fields that won't be used by their selected product

---

### 5. **Test Type-Specific Field Logic** ✅
**Improved conditional field behavior based on Test Type selection**

#### Test Type: **Loops**
- **Enabled**: Loops field
- **Disabled**: All Sweep/Shmoo fields

#### Test Type: **Sweep**
- **Enabled**: Type, Domain, Start, End, Steps
- **Disabled**: ShmooFile, ShmooLabel, Loops

#### Test Type: **Shmoo**
- **Enabled**: ShmooFile, ShmooLabel
- **Disabled**: Type, Domain, Start, End, Steps, Loops

**Implementation:**
```python
if test_type == 'Loops':
    # Enable Loops field only
elif test_type == 'Sweep':
    # Enable Sweep fields (Type, Domain, Start, End, Steps)
    # Disable Shmoo fields
elif test_type == 'Shmoo':
    # Enable Shmoo fields (ShmooFile, ShmooLabel)
    # Disable Sweep fields
```

**Why**: Each Test Type uses different parameters - only show relevant fields

---

### 6. **Default Values for Voltage/Frequency Fields** ✅
**Changed default values from 0/0.0 to None (empty string)**

| Field | Type | Old Default | New Default |
|-------|------|-------------|-------------|
| Voltage IA | float | 0.0 | "" (empty) |
| Voltage CFC | float | 0.0 | "" (empty) |
| Frequency IA | int | 0 | "" (empty) |
| Frequency CFC | int | 0 | "" (empty) |
| Check Core | int | 0 | "" (empty) |

**Why**: These fields are optional - empty is more accurate than 0 (which could be a valid value)

**Implementation:**
```python
elif field_type == "int":
    if field in ["Frequency IA", "Frequency CFC", "Check Core"]:
        data[field] = ""
    else:
        data[field] = 0
elif field_type == "float":
    if field in ["Voltage IA", "Voltage CFC"]:
        data[field] = ""
    else:
        data[field] = 0.0
```

---

### 7. **Voltage Type Default Value** ✅
**Default**: `vbump` (was already set, now confirmed)

**Other Options**: fixed, ppvc

**Why**: `vbump` is the most common voltage control type

---

## 🔄 Updated Conditional Logic Flow

### On Test Type Change:
```
Loops → Enable: Loops field
      → Disable: All Sweep/Shmoo fields

Sweep → Enable: Type, Domain, Start, End, Steps
      → Disable: ShmooFile, ShmooLabel, Loops

Shmoo → Enable: ShmooFile, ShmooLabel
      → Disable: Type, Domain, Start, End, Steps, Loops
```

### On Product Change:
```
GNR → Enable: Pseudo Config, Core License
    → Disable: Disable 2 Cores, Disable 1 Core

CWF → Enable: Disable 2 Cores
    → Disable: Pseudo Config, Disable 1 Core, Core License

DMR → Enable: Disable 1 Core, Core License
    → Disable: Pseudo Config, Disable 2 Cores
```

### On Content Change:
```
Linux → Enable: Linux section
      → Disable: Dragon, Merlin sections

Dragon → Enable: Dragon, Merlin sections
       → Disable: Linux section

Other → Disable: All conditional sections
```

---

## 📊 Field State Matrix

### Test Configuration Fields
| Field | Loops | Sweep | Shmoo |
|-------|-------|-------|-------|
| Loops | ✅ | ❌ | ❌ |
| Type | ❌ | ✅ | ❌ |
| Domain | ❌ | ✅ | ❌ |
| Start | ❌ | ✅ | ❌ |
| End | ❌ | ✅ | ❌ |
| Steps | ❌ | ✅ | ❌ |
| ShmooFile | ❌ | ❌ | ✅ |
| ShmooLabel | ❌ | ❌ | ✅ |

### Product-Specific Fields
| Field | GNR | CWF | DMR |
|-------|-----|-----|-----|
| Pseudo Config | ✅ | ❌ | ❌ |
| Core License | ✅ | ❌ | ✅ |
| Disable 2 Cores | ❌ | ✅ | ❌ |
| Disable 1 Core | ❌ | ❌ | ✅ |
| Configuration Mask | ✅ | ✅ | ✅ |

---

## 🧪 Testing Checklist

### Unit Data Auto-Apply
- [ ] Change Visual ID - verify all experiments update
- [ ] Change Bucket - verify all experiments update
- [ ] Change COM Port - verify all experiments update
- [ ] Change IP Address - verify all experiments update
- [ ] Create new experiment - verify Unit Data is pre-populated
- [ ] No "Apply" button should be visible

### Tooltip Behavior
- [ ] Hover over field - tooltip appears
- [ ] Move cursor away - tooltip disappears immediately
- [ ] Hover over multiple fields rapidly - no lingering tooltips

### Section Order
- [ ] Basic Information is first
- [ ] Advanced Configuration is second (moved up)
- [ ] Test Configuration is third

### Product-Specific Graying
- [ ] Set Product to GNR - verify Pseudo Config and Core License enabled, others grayed
- [ ] Set Product to CWF - verify Disable 2 Cores enabled, others grayed
- [ ] Set Product to DMR - verify Disable 1 Core and Core License enabled, others grayed
- [ ] Grayed fields should have gray text labels and disabled state

### Test Type Conditional Fields
- [ ] Set Test Type to Loops - verify only Loops field enabled
- [ ] Set Test Type to Sweep - verify Sweep fields enabled, Shmoo fields grayed
- [ ] Set Test Type to Shmoo - verify Shmoo fields enabled, Sweep fields grayed
- [ ] Switch between types - verify fields update correctly

### Default Values
- [ ] Create new experiment - verify Voltage IA is empty (not 0.0)
- [ ] Verify Voltage CFC is empty
- [ ] Verify Frequency IA is empty (not 0)
- [ ] Verify Frequency CFC is empty
- [ ] Verify Check Core is empty
- [ ] Verify Voltage Type defaults to "vbump"

---

## 🐛 Bug Fixes

### Issue 1: Tooltips Don't Go Away
**Status**: ✅ FIXED
**Solution**: Added proper tooltip destruction and reference cleanup

### Issue 2: Advanced Configuration Hard to Find
**Status**: ✅ FIXED
**Solution**: Moved section to position #2 (right after Basic Information)

### Issue 3: Can Edit Product-Specific Fields Regardless of Product
**Status**: ✅ FIXED
**Solution**: Added product-based field graying logic

### Issue 4: Test Type Doesn't Control Field Availability
**Status**: ✅ FIXED
**Solution**: Enhanced conditional logic for Loops/Sweep/Shmoo

### Issue 5: Voltage/Frequency Fields Default to 0
**Status**: ✅ FIXED
**Solution**: Changed defaults to empty string for optional fields

---

## 📝 Code Changes Summary

### Modified Methods:
1. `create_tooltip()` - Added try/except and reference cleanup
2. `create_experiment_tab()` - Reordered section creation
3. `create_left_panel()` - Added auto-apply info label and event bindings
4. `create_default_experiment_data()` - Updated default values logic
5. `update_conditional_sections()` - Added Test Type and Product logic
6. `auto_apply_unit_data()` - NEW method for automatic unit data propagation
7. `apply_unit_data()` - Changed to call `auto_apply_unit_data()`

### Lines Changed: ~50 lines modified/added

---

## 🎓 User Impact

### Workflow Improvements:
1. **Less Manual Work**: No need to click "Apply" for Unit Data
2. **Visual Clarity**: Grayed fields clearly show what's not used
3. **Fewer Errors**: Can't accidentally configure unused fields
4. **Better Organization**: Important fields (Advanced Config) near the top
5. **Smarter UI**: Fields enable/disable based on Test Type

### What Users Will Notice:
- Unit Data changes apply instantly to all experiments
- Fields gray out automatically based on Product
- Sweep/Shmoo fields only show when relevant Test Type is selected
- Loops field only enabled for Loops Test Type
- Tooltips behave properly (no more stuck tooltips)
- Advanced Configuration moved up in section order

---

## 🔮 Future Enhancements (Not Implemented)

### Potential Improvements:
1. **Field Hiding**: Completely hide product-specific fields instead of graying
2. **Validation**: Prevent saving if grayed fields have values
3. **Visual Indicators**: Show "(GNR only)", "(CWF only)" in field labels
4. **Export Filtering**: Exclude grayed field values from JSON export
5. **Template Validation**: Warn when loading template from different product

---

## 📦 Version History

### v2.2 (Current - December 8, 2025)
- Auto-apply Unit Data to all experiments
- Fixed tooltip bug (lingering tooltips)
- Moved Advanced Configuration to position #2
- Product-specific field graying (Pseudo Config, Disable Cores, Core License)
- Test Type conditional logic (Loops/Sweep/Shmoo)
- Default empty values for Voltage/Frequency/Check Core
- Voltage Type defaults to "vbump"

### v2.1 (Previous)
- No default experiment on startup
- Experiment Enabled/Disabled graying
- Clear and Apply Template buttons
- Merlin tied to Dragon content
- Product-specific options

### v2.0
- Excel-like interface
- Product selection
- Left panel with Unit Data + Templates

### v1.0
- Initial release

---

## ✅ Verification

All requested changes have been implemented:
- ✅ Unit Data always applied to all experiments
- ✅ No "Apply to current experiment" button
- ✅ Tooltips fixed (don't stick)
- ✅ Advanced Configuration after Basic Configuration
- ✅ Product-specific fields grayed when not used
- ✅ Test Type Loops works with Loops field
- ✅ Test Type Sweep works with Type, Domain, Start, End, Steps
- ✅ Test Type Shmoo works with ShmooFile, ShmooLabel
- ✅ Voltage IA/CFC, Frequency IA/CFC, Check Core default to None (empty)
- ✅ Voltage Type defaults to "vbump"

---

**Document Version**: 1.0
**Last Updated**: December 8, 2025
