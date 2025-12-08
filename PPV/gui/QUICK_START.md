# PPV Experiment Builder - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Launch the Tool

**Option A: From PPV Tools Hub**
```bash
cd c:\Git\Automation\Automation\PPV
python run.py
```
Then click the **"Experiment Builder"** card.

**Option B: Standalone**
```bash
cd c:\Git\Automation\Automation\PPV
python run_experiment_builder.py
```

### Step 2: Create Your First Experiment

1. **Click the `+` button** in the left panel
2. A new experiment appears: `New_Experiment_1`
3. **Edit the experiment:**
   - Navigate to **"Basic Info"** tab
   - Change **Test Name** to something meaningful (e.g., `My_First_Test`)
   - Select **Test Mode**: `Mesh` or `Slice`
   - Select **Test Type**: `Loops`, `Sweep`, or `Shmoo`

### Step 3: Configure Test Parameters

**Switch to "Test Config" tab:**
- Set **COM Port** (e.g., `8`)
- Set **IP Address** (e.g., `192.168.0.2`)
- Browse for **TTL Folder** (click 📁 button)
- Set **Test Time** (seconds, e.g., `30`)
- Set **Loops** (number of iterations, e.g., `10`)
- Check **Reset** if you want to reset between tests

**Switch to "Voltage/Freq" tab:**
- Select **Voltage Type** (e.g., `vbump`)
- Set **Voltage IA** (e.g., `1.0`)
- Set **Voltage CFC** (e.g., `0.9`)

### Step 4: Preview and Export

1. **Click "JSON Preview" tab** to see generated JSON
2. **Click "Export to JSON"** at the bottom
3. **Choose save location** and filename
4. **Done!** Your experiment is ready for the Control Panel

---

## 📥 Import Existing Experiments

### From Excel File

1. **Click "Import from Excel"**
2. **Select your .xlsx file**
3. Excel format:
   - One sheet per experiment
   - Column A: Field names
   - Column B: Values
4. Choose **Merge** or **Replace**

**Need an Excel template?**
```bash
cd c:\Git\Automation\Automation\PPV\gui
python create_excel_template.py
```
This creates `Experiment_Template_Sample.xlsx` with examples.

### From JSON File

1. **Click "Import from JSON"**
2. **Select your .json file**
3. Choose **Merge** or **Replace**

---

## 🎯 Common Tasks

### Duplicate an Experiment
1. Select experiment in left panel
2. Click **📋** button
3. A copy is created with `_copy` suffix

### Delete an Experiment
1. Select experiment in left panel
2. Click **-** button
3. Confirm deletion

### Search Experiments
- Type in the **Search** box at the top of the left panel
- List filters in real-time

### Rename an Experiment
1. Select experiment
2. Go to **"Basic Info"** tab
3. Change **Test Name** field
4. Experiment key updates automatically

### Validate All Experiments
1. **Click "Validate All"** at the bottom
2. Review any issues in the popup
3. Fix highlighted problems

---

## 📋 Field Reference

### Essential Fields

| Field | Tab | Description | Example |
|-------|-----|-------------|---------|
| Experiment | Basic Info | Enable/Disable | `Enabled` |
| Test Name | Basic Info | Unique identifier | `Loop_Test_1` |
| Test Mode | Basic Info | Execution mode | `Mesh` |
| Test Type | Basic Info | Type of test | `Loops` |
| COM Port | Test Config | Serial port | `8` |
| IP Address | Test Config | Network address | `192.168.0.2` |
| Test Time | Test Config | Duration (sec) | `30` |
| Loops | Test Config | Iterations | `10` |
| Voltage Type | Voltage/Freq | Control type | `vbump` |
| Voltage IA | Voltage/Freq | IA voltage | `1.0` |
| Content | Content | Content type | `Linux` |

### Test Types Explained

**Loops**: Run the same test multiple times
- Set **Loops** field (e.g., `10`)
- Test repeats N times

**Sweep**: Vary a single parameter
- Set **Type** (Voltage or Frequency)
- Set **Domain** (IA or CFC)
- Set **Start**, **End**, **Steps**
- Example: Voltage sweep from 0.8V to 1.2V in 0.05V steps

**Shmoo**: 2D characterization
- Set **ShmooFile** path
- Set **ShmooLabel** identifier
- Requires shmoo configuration file

---

## 🔧 Troubleshooting

### Problem: Import fails from Excel
**Solution**: Check Excel format
- Each sheet = one experiment
- Column A = field names
- Column B = values
- No merged cells

### Problem: JSON export doesn't work
**Solution**: 
- Check write permissions on target folder
- Close any programs with the file open
- Try a different location

### Problem: Validation errors
**Solution**: Common fixes
- COM Port: Must be 0-256
- IP Address: Must be IPv4 format (e.g., 192.168.0.2)
- Numeric fields: Remove text, use numbers only
- Required fields: Test Name, Test Mode, Test Type

### Problem: Can't find exported JSON
**Solution**: 
- Check the "Save As" dialog location
- Default location is where you last saved
- Search for `.json` files by date

---

## 💡 Pro Tips

1. **Start with a Template**: Create one good experiment, then duplicate it for variations
2. **Use Descriptive Names**: `VoltSweep_IA_0.8_1.2` is better than `Test1`
3. **Validate Often**: Run "Validate All" before exporting
4. **Check JSON Preview**: Review the JSON tab to catch formatting issues
5. **Save Incrementally**: Export to JSON regularly to avoid losing work
6. **Organize by Type**: Use prefixes like `Loop_`, `Sweep_`, `Shmoo_` for easy searching
7. **Keep a Master File**: Maintain one JSON with all your experiment templates

---

## 📚 Next Steps

1. **Read the full README**: `EXPERIMENT_BUILDER_README.md`
2. **Generate Excel template**: Run `create_excel_template.py`
3. **Test with Control Panel**: Load your JSON in the Debug Framework Control Panel
4. **Explore PPV Tools**: Check out other tools in the PPV Tools Hub

---

## 🆘 Need Help?

- **Validation errors**: Check the "Validate All" report for specific issues
- **Field descriptions**: Hover over fields for tooltips
- **Example experiments**: Import the sample Excel template
- **JSON structure**: View the "JSON Preview" tab
- **Control Panel compatibility**: Ensure your JSON matches the expected format

---

**Happy Experimenting! 🎉**

*PPV Experiment Builder - Making experiment configuration simple and efficient.*
