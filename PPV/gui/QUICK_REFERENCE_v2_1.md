# ExperimentBuilder v2.1 - Quick Reference Guide

## 🚀 What's New in v2.1

### Clean Startup
- Application now starts **without any pre-loaded experiments**
- Click **"+ New Experiment"** to create your first experiment
- No more unwanted "Baseline" experiment

---

## 🎛️ New Toolbar Buttons

### 🗑 Clear Button
**Purpose**: Reset current experiment to default values

**How to Use**:
1. Select the experiment tab you want to reset
2. Click **🗑 Clear** button in toolbar
3. Confirm the action in the dialog
4. All fields reset to defaults (experiment name preserved)

**When to Use**:
- Quick cleanup after testing
- Start fresh without deleting the experiment
- Faster than manually clearing each field

---

### 📄 Apply Template Button
**Purpose**: Apply a saved template to the current experiment

**How to Use**:
1. Select the experiment tab you want to update
2. Select a template from the **Templates** panel on the left
3. Click **📄 Apply Template** button in toolbar
4. Template values apply instantly (experiment name preserved)

**When to Use**:
- Quickly configure new experiments with standard settings
- Copy configuration from one experiment to another
- Maintain consistency across multiple tests

---

## 🔴 Experiment Enable/Disable Feature

### Visual Feedback
When you set **Experiment** field to **"Disabled"**:
- ✅ Entire experiment tab **grays out**
- ✅ All fields become non-editable (except Experiment dropdown)
- ✅ Labels turn gray (#cccccc)
- ✅ Experiment will **NOT run** during execution

### How to Use
1. In any experiment tab, find the **Experiment** field (first field)
2. Change dropdown from **"Enabled"** to **"Disabled"**
3. Watch all fields gray out automatically
4. To re-enable, simply change back to **"Enabled"**

### Why This Matters
- Visually see which experiments will run
- Temporarily disable experiments without deleting them
- Keep experimental configurations while focusing on others

---

## 🐉 Merlin Section (Dragon-Tied)

### New Behavior
**Merlin Configuration** section is now **tied to Dragon content**

### Rules
- **Content = "Dragon"** → Merlin section **ENABLED**
- **Content ≠ "Dragon"** → Merlin section **DISABLED** (shows "Conditional")

### Why
Merlin tools are Dragon-specific, so the section only enables when relevant.

---

## 🎯 Product-Specific Features

### Core License (GNR/DMR Only)

**Location**: Test Configuration section

**GNR/DMR Dropdown Options**:
1. 1: SSE/128
2. 2: AVX2/256 Light
3. 3: AVX2/256 Heavy
4. 4: AVX3/512 Light
5. 5: AVX3/512 Heavy
6. 6: TMUL Light
7. 7: TMUL Heavy

**CWF**: Text entry (no dropdown)

**How to Use**:
1. Set **Product** to GNR or DMR in Unit Data panel
2. Go to **Test Configuration** section
3. Click **Core License** dropdown
4. Select your desired license (1-7)

---

### Configuration Mask

**Location**: Advanced Configuration section

**Two Modes**:

#### 1. Mesh Mode
**Options** (dropdown):
- RowPass1
- RowPass2
- RowPass3
- FirstPass
- SecondPass
- ThirdPass
- *(Can be blank for full chip)*

**When to Use**: Testing specific mesh passes

#### 2. Slice Mode
**Input**: Core number (numeric)

**Ranges by Product**:
- **GNR**: 0-179
- **CWF**: 0-179
- **DMR**: 0-128

**Rules**: **Cannot be blank** in Slice mode

**How to Use**:
1. Set **Test Mode** to "Mesh" or "Slice"
2. If Mesh: Select pass option from dropdown (or leave blank)
3. If Slice: Enter core number within range

---

### Disable 2 Cores (CWF Only)

**Location**: Advanced Configuration section

**Dropdown Options**:
- 0x3
- 0xc
- 0x9
- 0xa
- 0x5

**How to Use**:
1. Set **Product** to CWF
2. Select hex value from dropdown
3. Leave blank if not using

---

### Disable 1 Core (DMR Only)

**Location**: Advanced Configuration section

**Dropdown Options**:
- 0x1
- 0x2

**How to Use**:
1. Set **Product** to DMR
2. Select hex value from dropdown
3. Leave blank if not using

---

### Pseudo Config (GNR Only)

**Location**: Test Configuration section

**Type**: Boolean (checkbox)

**Purpose**: Disable HT for Pseudo Mesh Content

**How to Use**:
1. Set **Product** to GNR
2. Check box to enable
3. Only applies to Pseudo Mesh content

---

## 📋 Product Field Summary

| Field | GNR | CWF | DMR |
|-------|-----|-----|-----|
| **Core License** | ✅ Dropdown (1-7) | ❌ Text | ✅ Dropdown (1-7) |
| **Pseudo Config** | ✅ Boolean | ❌ N/A | ❌ N/A |
| **Disable 2 Cores** | ❌ N/A | ✅ Dropdown | ❌ N/A |
| **Disable 1 Core** | ❌ N/A | ❌ N/A | ✅ Dropdown |
| **Configuration Mask** | ✅ All modes | ✅ All modes | ✅ All modes |

**Tip**: Field descriptions show product applicability (e.g., "GNR only", "DMR only")

---

## 🔄 Conditional Sections Reference

### When Each Section Enables

| Section | Condition | Fields |
|---------|-----------|--------|
| **Sweep/Shmoo** | Test Type = "Sweep" OR "Shmoo" | Type, Domain, Start, End, Steps, ShmooFile, ShmooLabel |
| **Linux Config** | Content = "Linux" | Linux Path, Pre/Post Commands, Pass/Fail Strings, Content Lines |
| **Dragon Config** | Content = "Dragon" | Dragon Path, ULX Path, Product Chop, VVAR fields, Content Line |
| **Merlin Config** | Content = "Dragon" | Merlin Name, Drive, Path |

**Visual Indicator**: Disabled sections show **(Conditional)** in header

---

## 🎬 Common Workflows

### Workflow 1: Starting a New Project
1. Launch ExperimentBuilder (starts empty)
2. Set **Product** in Unit Data panel (GNR/CWF/DMR)
3. Fill in Unit Data fields (Visual ID, Bucket, etc.)
4. Click **+ New Experiment**
5. Configure experiment fields
6. Click **Apply Unit Data** to share Unit Data across experiments

---

### Workflow 2: Creating Multiple Similar Experiments
1. Create and configure first experiment
2. Click **Save Template** in Templates panel
3. Name it (e.g., "default")
4. Click **+ New Experiment** for each additional experiment
5. For each new experiment:
   - Select it (click its tab)
   - Select "default" template in Templates panel
   - Click **📄 Apply Template**
   - Modify Test Name and specific fields

---

### Workflow 3: Temporarily Disabling Experiments
1. Select experiment tab you want to disable
2. Set **Experiment** field to "Disabled"
3. Watch fields gray out
4. Experiment will be skipped during execution
5. To re-enable, set back to "Enabled"

---

### Workflow 4: Resetting an Experiment
**Option A: Clear (keeps experiment)**
1. Select experiment tab
2. Click **🗑 Clear** button
3. Confirm
4. Fields reset to defaults

**Option B: Delete (removes experiment)**
1. Select experiment tab
2. Click **✕ Delete** button
3. Confirm
4. Experiment tab removed

---

## ⚠️ Important Notes

### Configuration Mask Validation
- **Mesh Mode**: Can be blank (full chip)
- **Slice Mode**: **MUST** have core number
- Check product-specific core ranges (GNR/CWF: 0-179, DMR: 0-128)

### Product-Specific Fields
- Fields labeled "GNR only", "CWF only", "DMR only" are product-specific
- **Leave blank** if not using that product
- Values only apply when Product matches

### Template Best Practices
- Save templates with descriptive names
- Create separate templates for each Product
- Review template before applying (may overwrite current values)
- Use "default" for your standard configuration

### Experiment Names
- Each experiment needs unique Test Name
- Clear and Apply Template preserve Test Name
- Duplicate creates new name automatically (appends _1, _2, etc.)

---

## 🆘 Troubleshooting

### Q: Fields are grayed out and I can't edit
**A**: Check if Experiment is set to "Disabled". Change to "Enabled".

### Q: Merlin section is disabled
**A**: Set Content to "Dragon" to enable Merlin section.

### Q: Core License doesn't show dropdown
**A**: Verify Product is set to GNR or DMR (not CWF).

### Q: Configuration Mask won't accept my value
**A**: 
- **Mesh Mode**: Use dropdown options or leave blank
- **Slice Mode**: Enter numeric core number within range

### Q: Can't see my product-specific fields
**A**: All fields are visible, but check field descriptions for product applicability.

### Q: Export JSON doesn't include new field
**A**: Verify field has a value. Blank fields may not export.

---

## 📚 Related Documentation
- Full changelog: `CHANGELOG_v2_1.md`
- Installation guide: `INSTALLATION.md`
- Field reference: See config files in `PPV/configs/`

---

## 💡 Tips & Tricks

1. **Quick Template Application**: Select template, then click Apply Template (no need to open template menu)

2. **Experiment Organization**: Use Test Name prefix for grouping (e.g., "Sweep_Test1", "Sweep_Test2")

3. **Product Switching**: Change Product in Unit Data, then Apply Unit Data to all experiments

4. **Clear vs Delete**: Use Clear when you want to reconfigure, Delete when experiment is no longer needed

5. **Conditional Section Testing**: Change Test Type and Content to see sections enable/disable dynamically

6. **Visual Validation**: Look for grayed sections marked "(Conditional)" - these won't be used in current configuration

---

**Last Updated**: 2025 (v2.1)
**Document Version**: 1.0
