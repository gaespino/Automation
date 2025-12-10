# Universal Deployment Tool - Visual Guide

## 🖼️ GUI Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Universal Deployment Tool                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Source Configuration                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Source:  ( BASELINE )  ( BASELINE_DMR )  ( PPV )                      │  │
│  │ Deploy:  ( DebugFramework )  ( S2T )  ( PPV* )                        │  │
│  │ Target:  Not selected               [Select Target...]                │  │
│  │ Import CSV: None                    [Load CSV...] [Clear]             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────┬──────────────────────────────────────────────┐│
│ │ FILE LIST                 │ DETAILS & DIFF                                ││
│ │                           │                                               ││
│ │ [Scan] [Select All]       │ ┌───────────────────────────────────────────┐││
│ │                           │ │ File Details                               │││
│ │ Filter: [_________]       │ │ File: DebugFramework/SystemDebug.py       │││
│ │ ☐ Show only changes       │ │ Status: Minor changes                     │││
│ │ ☐ Show only selected      │ │ Similarity: 85%                           │││
│ │ ☐ Show replacements       │ │                                           │││
│ │                           │ │ Import Replacements:                      │││
│ │ ☑ Status Similar Replace  │ │   from DebugFramework.SystemDebug import  │││
│ │ ▼ DebugFramework/         │ │     → from DebugFramework.GNR...          │││
│ │   ☑ SystemDebug.py        │ └───────────────────────────────────────────┘││
│ │     Minor  85%    2 rules │                                               ││
│ │   ☐ TestFramework.py      │ ┌───────────────────────────────────────────┐││
│ │     New    -      -       │ │ Changes Preview                            │││
│ │   ☑ FileHandler.py        │ │                                            │││
│ │     Minimal 95%   1 rule  │ │ --- current: SystemDebug.py                │││
│ │ ▼ S2T/                    │ │ +++ new: SystemDebug.py                    │││
│ │   ☑ dpmChecks.py          │ │ @@ -1,5 +1,5 @@                            │││
│ │     Minor  78%    3 rules │ │ -from DebugFramework.SystemDebug import    │││
│ │   ☐ CoreManipulation.py   │ │ +from DebugFramework.GNRSystemDebug import │││
│ │     Identical 100% -      │ │                                            │││
│ │                           │ │  def initialize():                         │││
│ │                           │ │      # code...                             │││
│ │                           │ │                                            │││
│ │                           │ └───────────────────────────────────────────┘││
│ └───────────────────────────┴──────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ Selected 3 file(s) (2 with import replacements)    [Export] [Deploy]        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🎨 Visual Elements

### Header Section
```
┌─────────────────────────────────────────────────────────────┐
│ Source Configuration                                         │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Source: Select where to deploy FROM                      ││
│ │   ● BASELINE       → Base implementation                 ││
│ │   ○ BASELINE_DMR   → DMR-specific variant                ││
│ │   ○ PPV            → Performance validation tools        ││
│ │                                                           ││
│ │ Deploy: Select what to deploy                            ││
│ │   ● DebugFramework → Framework files only                ││
│ │   ○ S2T            → S2T files only                      ││
│ │   ○ PPV            → PPV files (PPV source only)         ││
│ │                                                           ││
│ │ Target: C:\...\ProductName\DebugFramework [Change...]    ││
│ │                                                           ││
│ │ Import CSV: import_replacement_gnr.csv [Load...] [Clear] ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### File List Controls
```
┌─────────────────────────────────────────┐
│ [Scan Files] [Select All] [Deselect All]│
│                                          │
│ Filter: [dpm___________] 🔍              │
│                                          │
│ ☑ Show only changes                      │
│ ☐ Show only selected                     │
│ ☑ Show files with replacements           │
└─────────────────────────────────────────┘
```

### File Tree View
```
☑  File                    Status       Similar  Replacements
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▼  DebugFramework/
   ☑  SystemDebug.py       Minor        85%      2 rules     🟠
   ☐  TestFramework.py     New          -        -           🔵
   ☑  FileHandler.py       Minimal      95%      1 rule      🟢
   ☐  S2TMocks.py          Identical    100%     -           ⚫

▼  S2T/
   ☑  dpmChecks.py         Minor        78%      3 rules     🟠
   ☐  CoreManipulation.py  Major        25%      2 rules     🔴
   ☑  ConfigsLoader.py     Minimal      92%      -           🟢
```

### Status Colors Legend
```
🔵 Blue      = New File        (doesn't exist in target)
🟢 Green     = Minimal Changes (90-100% similar)
🟠 Orange    = Minor Changes   (30-90% similar)
🔴 Red       = Major Changes   (<30% similar - ⚠️ review!)
⚫ Gray      = Identical       (100% match - can skip)
```

### Details Panel
```
┌────────────────────────────────────────────────────┐
│ File Details                                        │
│ ───────────────────────────────────────────────────│
│ File: DebugFramework/SystemDebug.py                 │
│ Status: Minor changes (85% similar)                 │
│ Source: C:\...\BASELINE\DebugFramework\SystemDebug.py│
│ Target: C:\...\GNR\DebugFramework\SystemDebug.py   │
│                                                      │
│ Import Replacements (2 rules will be applied):      │
│   • from DebugFramework.SystemDebug import          │
│     → from DebugFramework.GNRSystemDebug import     │
│                                                      │
│   • users.gaespino.dev.DebugFramework.SystemDebug   │
│     → users.gaespino.DebugFramework.GNRSystemDebug  │
└────────────────────────────────────────────────────┘
```

### Diff Viewer
```
┌──────────────────────────────────────────────────────┐
│ Changes Preview                                       │
│ ─────────────────────────────────────────────────────│
│ 🔄 Import replacements will be applied:              │
│   • from DebugFramework.SystemDebug import           │
│     → from DebugFramework.GNRSystemDebug import      │
│                                                       │
│ --- current: SystemDebug.py                          │
│ +++ new: SystemDebug.py                              │
│ @@ -1,10 +1,10 @@                                    │
│  import sys                                          │
│  import os                                           │
│ -from DebugFramework.SystemDebug import Config       │
│ +from DebugFramework.GNRSystemDebug import Config    │
│  from typing import Optional                         │
│                                                       │
│  class SystemDebug:                                  │
│ -    module_path = "users.gaespino.dev..."          │
│ +    module_path = "users.gaespino..."              │
│      def __init__(self):                             │
│          pass                                        │
└──────────────────────────────────────────────────────┘

Color Coding:
  Blue text   = Headers (file names, line numbers)
  Green text  = Added lines (start with +)
  Red text    = Removed lines (start with -)
  Purple text = Replacement info
  Black text  = Context (unchanged)
```

### Status Bar
```
┌─────────────────────────────────────────────────────────────┐
│ Selected 3 file(s) (2 with import replacements)             │
│                                          [Export] [Deploy]   │
└─────────────────────────────────────────────────────────────┘
```

## 🖱️ Interactive Elements

### Checkboxes
```
Click behaviors:
  ☐  → ☑  (Select file)
  ☑  → ☐  (Deselect file)

Click on column header:
  Toggles ALL visible files
```

### Directory Nodes
```
▼ DebugFramework/    (Expanded - click to collapse)
  ☑ SystemDebug.py
  ☐ FileHandler.py

► DebugFramework/    (Collapsed - click to expand)
```

### File Row
```
Click on:
  Checkbox  → Toggle selection
  File name → Show details/diff
  Row       → Select and show details
```

## 📱 Responsive Behavior

### Source Changes
```
Change: BASELINE → BASELINE_DMR
Effect: 
  - Scan cleared
  - File list emptied
  - Status: "Configuration changed. Click 'Scan Files'..."
```

### Deployment Type Changes
```
Change: DebugFramework → S2T
Effect:
  - Scan cleared
  - Different subdirectory scanned
  - PPV option enabled/disabled based on source
```

### Target Selection
```
Click: "Select Target..."
Dialog: Directory browser opens
Select: Choose folder
Effect: Target updated, ready to scan
```

### CSV Loading
```
Click: "Load CSV..."
Dialog: File browser opens
Select: import_replacement_gnr.csv
Effect:
  - Rules loaded
  - Label updated
  - Files rescanned if already scanned
  - Replacement column populated
```

## 🎭 Dialog Examples

### Deployment Confirmation
```
┌──────────────────────────────────────────┐
│ Confirm Deployment                        │
├──────────────────────────────────────────┤
│ Deploy 5 file(s) to:                     │
│ C:\...\GNR\DebugFramework                │
│                                           │
│ Import replacements will be applied to    │
│ 3 file(s)                                │
│ Total replacement rules: 8                │
│                                           │
│ A backup will be created before           │
│ deployment.                               │
│                                           │
│            [Yes]        [No]              │
└──────────────────────────────────────────┘
```

### Major Changes Warning
```
┌──────────────────────────────────────────┐
│ ⚠️  Major Changes                         │
├──────────────────────────────────────────┤
│ WARNING: 2 file(s) have major changes    │
│ (< 30% similarity)                        │
│                                           │
│ Files:                                    │
│   • CoreManipulation.py (25%)            │
│   • dpmChecks.py (28%)                   │
│                                           │
│ These files may have significant          │
│ differences. Please review carefully.     │
│                                           │
│ Do you want to continue?                  │
│                                           │
│            [Yes]        [No]              │
└──────────────────────────────────────────┘
```

### Success Message
```
┌──────────────────────────────────────────┐
│ ✅ Success                                │
├──────────────────────────────────────────┤
│ Successfully deployed 5 file(s)!          │
│                                           │
│ Applied 8 import replacement rule(s)      │
│                                           │
│ Backup location:                          │
│ DEVTOOLS/backups/20251209_143022         │
│                                           │
│                  [OK]                     │
└──────────────────────────────────────────┘
```

## 🎯 Step-by-Step Visual Workflow

### Step 1: Source Selection
```
┌──────────────────────────┐
│ Source: ● BASELINE       │ ← Click here
│         ○ BASELINE_DMR   │
│         ○ PPV            │
└──────────────────────────┘
```

### Step 2: Deployment Type
```
┌──────────────────────────┐
│ Deploy: ● DebugFramework │ ← Click here
│         ○ S2T            │
│         ○ PPV (disabled) │
└──────────────────────────┘
```

### Step 3: Target Selection
```
┌─────────────────────────────────────┐
│ Target: Not selected [Select...]    │ ← Click button
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 📁 Browse for Folder                │
│                                     │
│ Select target deployment directory:  │
│                                     │
│ ▼ C:\Git\Automation\Automation      │
│   ▼ S2T                             │
│     ▼ BASELINE_GNR                  │
│       ► DebugFramework ← Select     │
│                                     │
│        [OK]  [Cancel]               │
└─────────────────────────────────────┘
```

### Step 4: Load CSV
```
┌─────────────────────────────────────┐
│ Import CSV: None [Load CSV...]      │ ← Click button
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 📄 Open CSV File                    │
│                                     │
│ Files:                              │
│   import_replacement_gnr.csv        │ ← Select
│   import_replacement_cwf.csv        │
│   import_replacement_dmr.csv        │
│                                     │
│        [Open]  [Cancel]             │
└─────────────────────────────────────┘
```

### Step 5: Scan Files
```
┌──────────────────────────────────────┐
│ [Scan Files] ← Click                 │
└──────────────────────────────────────┘
         ↓
         Scanning...
         ↓
┌──────────────────────────────────────┐
│ ☑  File                  Status      │
│ ▼  DebugFramework/                   │
│    ☐  SystemDebug.py     Minor       │
│    ☐  FileHandler.py     New         │
└──────────────────────────────────────┘
```

### Step 6: Select Files
```
┌──────────────────────────────────────┐
│ ☑  File                  Status      │
│ ▼  DebugFramework/                   │
│    ☐  SystemDebug.py     Minor       │ ← Click checkbox
│    ☐  FileHandler.py     New         │ ← Click checkbox
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ ☑  File                  Status      │
│ ▼  DebugFramework/                   │
│    ☑  SystemDebug.py     Minor       │ ✓ Selected
│    ☑  FileHandler.py     New         │ ✓ Selected
└──────────────────────────────────────┘
```

### Step 7: Review Details
```
Click file → See details
         ↓
┌────────────────────────────────────────┐
│ File Details                            │
│ ───────────────────────────────────────│
│ File: DebugFramework/SystemDebug.py     │
│ Status: Minor changes                   │
│ Similarity: 85%                         │
│                                         │
│ Import Replacements:                    │
│   2 rules will be applied               │
│                                         │
│ Changes Preview:                        │
│   [Diff shown below]                    │
└────────────────────────────────────────┘
```

### Step 8: Deploy
```
┌──────────────────────────────────────┐
│ Selected 2 file(s)    [Deploy]       │ ← Click
└──────────────────────────────────────┘
         ↓
    Confirmation Dialog
         ↓
    Deployment in Progress
         ↓
    Success Message
```

## 🎨 Color Scheme

### Status Colors
```
New File:        RGB(0, 0, 255)      #0000FF  Blue
Identical:       RGB(128, 128, 128)  #808080  Gray
Minimal Changes: RGB(0, 128, 0)      #008000  Green
Minor Changes:   RGB(255, 165, 0)    #FFA500  Orange
Major Changes:   RGB(255, 0, 0)      #FF0000  Red
```

### Diff Colors
```
Header:      RGB(0, 0, 255)      #0000FF  Blue
Add Line:    RGB(0, 128, 0)      #008000  Green
Remove Line: RGB(255, 0, 0)      #FF0000  Red
Replacement: RGB(128, 0, 128)    #800080  Purple
Context:     RGB(0, 0, 0)        #000000  Black
```

## 📐 Layout Dimensions

```
Window:     1400 x 900 px (default)
Left Panel: ~50% width
Right Panel: ~50% width

Header:     Full width, ~200px height
File List:  ~60% height
Details:    ~20% height
Diff:       ~80% of right panel height
Status Bar: Full width, ~30px height
```

## 🔤 Font Specifications

```
Title:        Arial, 16pt, Bold
Headers:      Arial, 9pt, Bold
Labels:       Arial, 9pt, Regular
Tree Items:   Default system font
Diff Text:    Courier, 9pt, Regular
Status Bar:   Arial, 9pt, Regular
```

## 🎯 Hit Areas

### Interactive Zones
```
☑ Checkbox:     25x25 px clickable area
Directory △:    20x20 px clickable area
File Row:       Full row clickable
Column Header:  Full header clickable
Buttons:        Standard button size
```

---

**Note**: This is a text representation. The actual GUI uses native tkinter widgets with system-native appearance.
