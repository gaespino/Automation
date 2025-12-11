# Deploy Universal Tool - UI Updates

## New UI Section: Deployment Manifest

A new section has been added to the "Source Configuration" panel:

```
┌─────────────────────────────────────────────────────────────────┐
│ Source Configuration                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Product: ⦿ GNR  ○ CWF  ○ DMR    ☑ Auto-save configuration     │
│                                                                 │
│ Source:  ⦿ BASELINE  ○ BASELINE_DMR  ○ PPV                    │
│                                                                 │
│ Deploy:  ⦿ DebugFramework  ○ S2T  ○ PPV                       │
│                                                                 │
│ Target:  /path/to/target   [Select Target...]                  │
│                                                                 │
│ Import Replacement CSV: None                                    │
│          [Load CSV...]  [Clear]  [Generate...]                  │
│                                                                 │
│ File Rename CSV: None                                          │
│          [Load CSV...]  [Clear]  [Generate...]                  │
│                                                                 │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Deployment Manifest: None (all files included)            │ │ ← NEW!
│ │         [Load Manifest...]  [Clear]  [Auto-Load]          │ │ ← NEW!
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Button Functions

### 🔵 Load Manifest... (Manual Selection)
```
┌──────────────────────────────────┐
│ Select Deployment Manifest       │
├──────────────────────────────────┤
│                                  │
│ 📁 DEVTOOLS/                     │
│   ├─ deployment_manifest_        │
│   │    debugframework.json       │ ← Click to load
│   ├─ deployment_manifest_        │
│   │    s2t.json                  │
│   └─ deployment_manifest_        │
│        ppv.json                  │
│                                  │
│        [Open]  [Cancel]          │
└──────────────────────────────────┘
```

### 🔴 Auto-Load (Recommended)
Automatically detects deployment type and loads correct manifest:

**When Deploy = DebugFramework:**
```
✓ Automatically loads: deployment_manifest_debugframework.json
✓ Label changes to: "debugframework"
✓ Shows popup: "Automatically loaded manifest for DebugFramework"
```

**When Deploy = S2T:**
```
✓ Automatically loads: deployment_manifest_s2t.json
✓ Label changes to: "s2t"
✓ Shows popup: "Automatically loaded manifest for S2T"
```

**When Deploy = PPV:**
```
✓ Automatically loads: deployment_manifest_ppv.json
✓ Label changes to: "ppv"
✓ Shows popup: "Automatically loaded manifest for PPV"
```

### ⚪ Clear
```
✓ Removes manifest filtering
✓ Label changes to: "None (all files included)"
✓ Next scan will show ALL files (including test/mock files)
```

## Visual State Changes

### State 1: No Manifest Loaded (Default)
```
Deployment Manifest: None (all files included)
         [Load Manifest...]  [Clear]  [Auto-Load]
                                       ↑
                                  Click here!
```

### State 2: Manifest Loaded
```
Deployment Manifest: debugframework
         [Load Manifest...]  [Clear]  [Auto-Load]
                             ↑
                    Click to remove filtering
```

## Status Bar Updates

The status bar now shows filtering information:

### Before Manifest Feature
```
Status: Found 95 files for GNR
```

### After Manifest Feature (Manifest Loaded)
```
Status: Found 80 files for GNR (manifest excluded 15)
        └─────┬──────┘             └────────┬────────┘
         Ready for                 Test/mock files
         deployment                automatically filtered
```

### With Both Filters Active
```
Status: Found 80 files for GNR (manifest excluded 15) (product filtered 5)
        └─────┬──────┘             └────────┬────────┘  └────────┬────────┘
         Ready                     Test/mock              Other product
         deployment                excluded               files excluded
```

## Popup Messages

### Success: Manifest Loaded
```
┌─────────────────────────────────────────┐
│ ℹ Manifest Loaded                       │
├─────────────────────────────────────────┤
│                                         │
│ Loaded deployment manifest:             │
│ deployment_manifest_debugframework.json │
│                                         │
│ Module: DebugFramework                  │
│ Description: Production deployment...   │
│ Exclude Files: 8                        │
│ Exclude Patterns: 7                     │
│ Include Directories: 9                  │
│                                         │
│              [OK]                       │
└─────────────────────────────────────────┘
```

### Success: Auto-Loaded
```
┌─────────────────────────────────────────┐
│ ℹ Auto-Loaded Manifest                  │
├─────────────────────────────────────────┤
│                                         │
│ Automatically loaded manifest for       │
│ DebugFramework                          │
│                                         │
│ Module: DebugFramework                  │
│ Exclude Files: 8                        │
│ Exclude Patterns: 7                     │
│                                         │
│ Test/mock/development files will be     │
│ automatically excluded.                 │
│                                         │
│              [OK]                       │
└─────────────────────────────────────────┘
```

### Warning: Manifest Not Found
```
┌─────────────────────────────────────────┐
│ ⚠ Manifest Not Found                    │
├─────────────────────────────────────────┤
│                                         │
│ Manifest file not found:                │
│ deployment_manifest_debugframework.json │
│                                         │
│ Please create the manifest or use       │
│ 'Load Manifest...' to select a         │
│ different file.                         │
│                                         │
│              [OK]                       │
└─────────────────────────────────────────┘
```

## File List Visual Changes

### Before (No Manifest)
```
Files:
├─ DebugFramework/
│  ├─ ☑ SystemDebug.py          (Production) ✅
│  ├─ ☐ TestRun.py               (Test) ⚠️
│  ├─ ☑ TestFramework.py         (Production) ✅
│  ├─ ☐ TestMocks.py             (Test) ⚠️
│  ├─ ☐ HardwareMocks.py         (Mock) ⚠️
│  └─ ☑ FileHandler.py           (Production) ✅
└─ UI/
   ├─ ☑ ControlPanel.py          (Production) ✅
   ├─ ☐ MockControlPanel.py      (Mock) ⚠️
   └─ ☐ TestControlPanel.py      (Test) ⚠️

Status: Found 95 files for GNR
        ↑ Includes test/mock files! ⚠️
```

### After (Manifest Loaded)
```
Files:
├─ DebugFramework/
│  ├─ ☑ SystemDebug.py          (Production) ✅
│  ├─ ☑ TestFramework.py         (Production) ✅
│  └─ ☑ FileHandler.py           (Production) ✅
└─ UI/
   └─ ☑ ControlPanel.py          (Production) ✅

Status: Found 80 files for GNR (manifest excluded 15)
        ↑ Only production files! ✅
        
Note: TestRun.py, TestMocks.py, HardwareMocks.py,
      MockControlPanel.py, and TestControlPanel.py
      are automatically excluded
```

## Configuration Save/Load

### Save Behavior
When you click "Save Config" or have "Auto-save" enabled:

```
Config saved for GNR:
├─ Source Type: BASELINE
├─ Deployment Type: DebugFramework
├─ Target Base: /path/to/target
├─ Replacement CSV: import_replacement_gnr.csv
├─ Rename CSV: file_rename_gnr.csv
└─ Manifest File: deployment_manifest_debugframework.json  ← NEW!
```

### Load Behavior
When you switch products or restart the tool:

```
Loading config for GNR...
✓ Restored source type
✓ Restored deployment type
✓ Restored target path
✓ Restored CSV files
✓ Restored manifest file  ← NEW!
✓ Label updated: "debugframework"
```

## Complete Workflow Visualization

### Step-by-Step UI Changes

**Step 1: Initial State**
```
Deployment Manifest: None (all files included)
Status: Select source, deployment type, and target to begin
```

**Step 2: After Selecting Deployment Type**
```
Deploy: ⦿ DebugFramework
Deployment Manifest: None (all files included)  ← Click Auto-Load
Status: Configuration changed. Click 'Scan Files' to compare.
```

**Step 3: After Auto-Load**
```
Deployment Manifest: debugframework  ← Loaded!
Status: Configuration changed. Click 'Scan Files' to compare.

[Popup appears with manifest info]
```

**Step 4: After Scan**
```
Deployment Manifest: debugframework
Files: 80 items shown (test files hidden)
Status: Found 80 files for GNR (manifest excluded 15)  ← Filtering active!
```

**Step 5: Ready to Deploy**
```
Selected: 80 file(s)
Status: Selected 80 file(s)

[Deploy Selected] button ready
```

## Visual Indicators

### Manifest Label Colors (Conceptual)
```
None (all files included)    → Gray/Default (⚠️ Warning state)
debugframework              → Green (✅ Active filtering)
s2t                        → Green (✅ Active filtering)
ppv                        → Green (✅ Active filtering)
```

### Status Messages
```
Normal:  "Found 80 files for GNR"
Warning: "Found 0 files" (check manifest)
Good:    "Found 80 files (manifest excluded 15)" ✓
```

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════╗
║         DEPLOYMENT MANIFEST QUICK REFERENCE               ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Button           Action                                  ║
║  ─────────────────────────────────────────────────────   ║
║  Load Manifest    Browse for manifest JSON file           ║
║  Clear            Remove manifest filtering               ║
║  Auto-Load        ★ Automatically load correct manifest   ║
║                                                           ║
║  Label States                                             ║
║  ─────────────────────────────────────────────────────   ║
║  None             No filtering (⚠️ test files included)   ║
║  debugframework   ✅ DebugFramework filtering active      ║
║  s2t             ✅ S2T filtering active                  ║
║  ppv             ✅ PPV filtering active                  ║
║                                                           ║
║  Pro Tip: Always click "Auto-Load" before scanning!      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

## Before vs After Comparison

### Before Enhancement
```
┌─────────────────────────────────────────────┐
│ Manual Review Required                      │
├─────────────────────────────────────────────┤
│                                             │
│ 1. Scan shows ALL files (95 files)         │
│ 2. Manually identify test files            │
│ 3. Deselect each test file individually    │
│ 4. Easy to miss TestRun.py or Mock files   │
│ 5. Risk of deploying test code ⚠️           │
│                                             │
│ Time: 5-10 minutes                          │
│ Error Risk: High                            │
└─────────────────────────────────────────────┘
```

### After Enhancement
```
┌─────────────────────────────────────────────┐
│ Automatic Filtering                         │
├─────────────────────────────────────────────┤
│                                             │
│ 1. Click "Auto-Load" button                │
│ 2. Click "Scan Files"                      │
│ 3. Only production files shown (80 files)  │
│ 4. Test files automatically hidden         │
│ 5. Safe deployment guaranteed ✅            │
│                                             │
│ Time: 30 seconds                            │
│ Error Risk: Zero                            │
└─────────────────────────────────────────────┘
```

---

**Remember**: Always look for the manifest label to show module name, not "None"!
