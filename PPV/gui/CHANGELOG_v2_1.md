# ExperimentBuilder v2.1 Enhancement Changelog

## Release Date: 2025

## Overview
This release adds product-specific validation, enhanced UI controls, and improved workflow management based on user feedback.

---

## 🎯 Major Enhancements

### 1. Clean Startup Experience
- **No Default Experiment**: Application now starts with empty experiment tabs
- **User-Initiated Creation**: Experiments are only created when user clicks "+ New Experiment"
- **Cleaner Workflow**: Matches user expectation of starting from scratch

**Technical Changes:**
- Modified `populate_default_data()` to skip auto-creation of "Baseline" experiment
- Added comments explaining the design decision

---

### 2. Experiment Enable/Disable with Visual Feedback
- **Enhanced Description**: "Experiment" field now clearly states "DISABLED experiments are grayed out and will NOT run"
- **Visual Graying**: When set to "Disabled", entire experiment tab grays out
- **Selective Graying**: Experiment dropdown remains enabled for easy re-enabling
- **Conditional Preservation**: Re-enabling respects Test Type and Content conditions

**Technical Changes:**
- Added `gray_out_experiment(widgets)` method
- Added `enable_experiment(widgets)` method
- Enhanced `update_conditional_sections()` to check Experiment state
- Field widgets set to `state='disabled'` and labels to `fg='#cccccc'` when grayed

---

### 3. Per-Experiment Action Buttons
- **Clear Button**: Resets current experiment to default values
  - Confirmation dialog before clearing
  - Preserves experiment name
  - One-click reset for quick cleanup

- **Apply Template Button**: Applies selected template to current experiment
  - Uses Templates panel selection
  - Keeps current experiment name
  - Quick template application without navigation

**Technical Changes:**
- Added buttons to toolbar in `create_right_panel()`
- Added `clear_current_experiment()` method
- Added `apply_template_to_current()` method
- Color-coded buttons: Clear (warning yellow), Apply Template (success green)

---

### 4. Merlin Section Tied to Dragon Content
- **Conditional Display**: Merlin section only enabled when Content = "Dragon"
- **Logical Grouping**: Merlin tools are Dragon-specific, now properly grouped
- **Section Marking**: Shows "(Conditional)" when disabled

**Technical Changes:**
- Modified `update_conditional_sections()` to add Merlin logic
- Merlin fields: "Merlin Name", "Merlin Drive", "Merlin Path"
- Same enable/disable mechanism as Linux and Dragon sections

---

### 5. Product-Specific Core License Options
- **GNR/DMR Support**: 7 dropdown options with clear labels
  - 1: SSE/128
  - 2: AVX2/256 Light
  - 3: AVX2/256 Heavy
  - 4: AVX3/512 Light
  - 5: AVX3/512 Heavy
  - 6: TMUL Light
  - 7: TMUL Heavy
- **CWF Support**: No dropdown (field remains text entry)
- **Dynamic Loading**: Options update when product changes

**Technical Changes:**
- Added `get_core_license_options()` method
- Returns list of 7 options for GNR/DMR, empty list for CWF
- Updated Core License field to use `self.get_core_license_options()`
- Enhanced field description: "GNR/DMR: Core license setting (1-7)"

---

### 6. Product-Specific Configuration Mask Options
- **Mesh Mode Options**: RowPass1/2/3, FirstPass, SecondPass, ThirdPass
  - Can be left blank for full chip operation
- **Slice Mode**: Core number input (numeric)
  - GNR: 0-179
  - CWF: 0-179
  - DMR: 0-128
  - Cannot be blank in Slice mode
- **Helpful Description**: "Mesh: Mask options | Slice: Core number (GNR:0-179, CWF:0-179, DMR:0-128)"

**Technical Changes:**
- Added `get_config_mask_options()` method
- Returns Mesh options for all products (same across GNR/CWF/DMR)
- Updated Configuration (Mask) field to use dropdown with validation hints
- Description clearly differentiates Mesh vs Slice requirements

---

### 7. Disable 1 Core Field (DMR-Specific)
- **New Field**: "Disable 1 Core" for DMR platform
- **Dropdown Options**: 0x1, 0x2
- **Product Awareness**: Only relevant for DMR, but visible for all products
- **Clear Labeling**: "DMR only - Disable 1 core (leave blank if not used)"

**Technical Changes:**
- Added "Disable 1 Core" to `data_types` in `get_default_template()`
- Added field to Advanced Configuration section
- Positioned after "Disable 2 Cores" field
- Uses dropdown with hex values

---

### 8. Enhanced Field Descriptions
- **Pseudo Config**: Now labeled "GNR only - Disable HT for Pseudo Mesh Content"
- **Disable 2 Cores**: Now labeled "CWF only - Disable 2 cores (leave blank if not used)"
- **Disable 1 Core**: Labeled "DMR only - Disable 1 core (leave blank if not used)"
- **Core License**: Now shows "(1-7)" to indicate expected range

---

## 📊 Field Summary

### Total Fields: 76
- **Base Fields**: 74 (from previous release)
- **Added in v2.1**: 1 (Disable 1 Core)
- **Enhanced**: 4 (Core License, Configuration Mask, Pseudo Config, Disable 2 Cores)

### Product-Specific Fields
| Field | GNR | CWF | DMR | Notes |
|-------|-----|-----|-----|-------|
| Core License | ✅ (7 options) | ❌ | ✅ (7 options) | Dropdown with SSE to TMUL options |
| Pseudo Config | ✅ | ❌ | ❌ | Boolean, HT control |
| Disable 2 Cores | ❌ | ✅ | ❌ | Dropdown: 0x3, 0xc, 0x9, 0xa, 0x5 |
| Disable 1 Core | ❌ | ❌ | ✅ | Dropdown: 0x1, 0x2 |
| Configuration Mask | ✅ | ✅ | ✅ | All products, range varies in Slice mode |

---

## 🎨 UI Improvements

### Toolbar Enhancements
**Before:**
- + New Experiment
- ✕ Delete
- 📋 Duplicate

**After:**
- + New Experiment
- ✕ Delete
- 📋 Duplicate
- 🗑 Clear (NEW)
- 📄 Apply Template (NEW)

### Visual Feedback
- Disabled experiments show grayed-out fields and labels
- Section headers show "(Conditional)" when inactive
- Color-coded buttons for quick visual identification
- Tooltips/descriptions explain field usage by product

---

## 🔧 Technical Implementation

### New Methods
1. `get_config_mask_options()` - Returns Mesh mode options
2. `get_core_license_options()` - Returns Core License options for GNR/DMR
3. `clear_current_experiment()` - Resets experiment to defaults
4. `apply_template_to_current()` - Applies template to current experiment
5. `gray_out_experiment(widgets)` - Visually disables experiment fields
6. `enable_experiment(widgets)` - Re-enables experiment fields

### Modified Methods
1. `populate_default_data()` - Removed Baseline auto-creation
2. `create_basic_info_section()` - Updated Experiment field description
3. `create_test_config_section()` - Added Core License dropdown, updated Pseudo Config label
4. `create_advanced_section()` - Added Configuration Mask dropdown, Disable 1/2 Core fields
5. `create_right_panel()` - Added Clear and Apply Template buttons
6. `update_conditional_sections()` - Added Merlin logic and Experiment graying logic

### Data Structure Changes
- Added "Disable 1 Core" to `data_types` dictionary
- Core License field now uses dynamic options list
- Configuration Mask field now uses dynamic options list

---

## 🧪 Testing Recommendations

### 1. Startup Testing
- [ ] Verify no experiments are created on launch
- [ ] Confirm "Product" dropdown defaults to "GNR"
- [ ] Check Unit Data fields are empty/default

### 2. Product Switching
- [ ] Switch between GNR, CWF, DMR
- [ ] Verify Core License shows 7 options for GNR/DMR, none for CWF
- [ ] Verify Configuration Mask shows Mesh options for all products
- [ ] Check product-specific field labels are correct

### 3. Experiment Management
- [ ] Create new experiment - verify default values
- [ ] Set Experiment to "Disabled" - verify graying
- [ ] Re-enable experiment - verify fields restore
- [ ] Test Clear button - confirm reset
- [ ] Test Apply Template button - confirm template loads

### 4. Conditional Sections
- [ ] Switch Test Type to Sweep/Shmoo - verify Sweep/Shmoo section enables
- [ ] Switch Content to Linux - verify Linux section enables
- [ ] Switch Content to Dragon - verify Dragon AND Merlin sections enable
- [ ] Switch Content to None/Empty - verify both sections disable

### 5. Field Validation
- [ ] Core License (GNR) - select option 1-7, verify value saves
- [ ] Core License (CWF) - verify field is text entry, not dropdown
- [ ] Core License (DMR) - select option 1-7, verify value saves
- [ ] Configuration Mask Mesh - select RowPass/FirstPass options
- [ ] Configuration Mask Slice - enter core number (test ranges: GNR 0-179, DMR 0-128)
- [ ] Disable 2 Cores (CWF) - select hex value
- [ ] Disable 1 Core (DMR) - select hex value
- [ ] Pseudo Config (GNR) - toggle boolean

### 6. Template Workflow
- [ ] Create experiment, configure fields
- [ ] Save as template named "default"
- [ ] Create new experiment, click Apply Template
- [ ] Select "default" template, verify it applies
- [ ] Click Clear, verify fields reset

### 7. Export Testing
- [ ] Configure experiments with product-specific fields
- [ ] Export to JSON
- [ ] Verify "Disable 1 Core" appears in JSON
- [ ] Verify Core License values are correct (1-7 format)
- [ ] Verify Configuration Mask values are correct

---

## 📝 Configuration File Changes

### Updated Files
- `PPV/configs/GNRControlPanelConfig.json` - Added "Disable 1 Core" to data_types
- `PPV/configs/CWFControlPanelConfig.json` - Added "Disable 1 Core" to data_types
- `PPV/configs/DMRControlPanelConfig.json` - Added "Disable 1 Core" to data_types

### Field Count: 76
All config files now contain 76 field definitions (74 base + Fuse File + Bios File + Disable 1 Core)

---

## 🐛 Known Issues / Future Enhancements

### Potential Improvements
1. **Runtime Validation**: Add validation to prevent saving when:
   - Configuration Mask is blank in Slice mode
   - Core number exceeds product range (GNR/CWF: 179, DMR: 128)

2. **Field Visibility**: Consider hiding product-specific fields when not applicable
   - Hide Pseudo Config when Product ≠ GNR
   - Hide Disable 2 Cores when Product ≠ CWF
   - Hide Disable 1 Core when Product ≠ DMR

3. **Template Validation**: Warn user when applying template from different product

4. **Export Validation**: Add warnings for product-specific fields with values when product doesn't match

---

## 🎓 User Guide Updates Needed

### New Workflows to Document
1. Starting fresh (no default experiment)
2. Using Clear vs Delete
3. Apply Template workflow
4. Understanding grayed-out experiments
5. Product-specific field usage
6. Configuration Mask: Mesh vs Slice modes
7. Core License selection guide

### Updated Screenshots Needed
1. Empty startup (no Baseline)
2. Toolbar with Clear and Apply Template buttons
3. Disabled experiment (grayed out)
4. Core License dropdown (GNR/DMR)
5. Configuration Mask dropdown
6. Advanced section with Disable 1/2 Core fields
7. Merlin section conditional display

---

## 📦 Version History

### v2.1 (Current)
- No default experiment on startup
- Experiment Enabled/Disabled graying
- Clear and Apply Template buttons
- Merlin tied to Dragon content
- Product-specific Core License options
- Product-specific Configuration Mask validation
- Added Disable 1 Core field for DMR
- Enhanced field descriptions for product awareness

### v2.0
- Excel-like interface (tabs = experiments)
- Product selection (GNR/CWF/DMR)
- Config files in PPV/configs folder
- Left panel: Unit Data + Templates
- 74 fields in 9 sections
- Conditional sections (Sweep/Shmoo, Linux, Dragon)
- Fuse File and Bios File fields

### v1.0
- Initial release
- 6 feature-based tabs
- 74 fields
- Basic import/export

---

## 👥 Credits
- **User Feedback**: Clean startup, product-specific validation requirements
- **Development**: Implementation of all v2.1 enhancements
- **Testing**: Pending comprehensive testing

---

## 📞 Support
For issues or questions about v2.1 enhancements:
1. Check field descriptions in UI (hover/tooltip)
2. Review product-specific field table in this document
3. Verify product selection matches your hardware
4. Check Configuration Mask mode (Mesh vs Slice)

---

**End of Changelog**
