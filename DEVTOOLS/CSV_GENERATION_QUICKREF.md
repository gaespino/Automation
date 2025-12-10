# CSV Generation - Quick Visual Reference

## New UI Elements

### Import Replacement CSV Section
```
┌─────────────────────────────────────────────────────────────────┐
│ Import Replacement CSV: [None]                                  │
│  [Load CSV...] [Clear] [Generate...]  ← NEW BUTTON             │
└─────────────────────────────────────────────────────────────────┘
```

### File Rename CSV Section
```
┌─────────────────────────────────────────────────────────────────┐
│ File Rename CSV: [None]                                         │
│  [Load CSV...] [Clear] [Generate...]  ← NEW BUTTON             │
└─────────────────────────────────────────────────────────────────┘
```

## CSV Generator Dialog

Click any "Generate..." button to open:

```
┌──────────────────────────────────────────────────────────┐
│  Import Replacement CSV Generator                        │
│  Generate Import CSV for GNR                             │
│                                                           │
│  ┌─ Options ───────────────────────────────────────────┐ │
│  │                                                      │ │
│  │  Product Prefix:    [GNR________]                   │ │
│  │                                                      │ │
│  │  Output File:       [import_replacement_gnr.csv___] │ │
│  │                                                      │ │
│  │  Output Directory:  [C:\...\DEVTOOLS] [Browse...]   │ │
│  │                                                      │ │
│  │  ┌─ Template Contents ────────────────────────────┐ │ │
│  │  │ This will generate a template CSV with        │ │ │
│  │  │ common import replacement patterns for GNR:   │ │ │
│  │  │                                                │ │ │
│  │  │ • SystemDebug → GNRSystemDebug               │ │ │
│  │  │ • TestFramework → GNRTestFramework           │ │ │
│  │  │ • dpmChecks → GNRdpmChecks                   │ │ │
│  │  │ • CoreManipulation → GNRCoreManipulation     │ │ │
│  │  │                                                │ │ │
│  │  │ You can edit the generated CSV to add or      │ │ │
│  │  │ modify replacement rules.                      │ │ │
│  │  └────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│                              [Cancel] [Generate]          │
└──────────────────────────────────────────────────────────┘
```

## Quick Workflow

### 1️⃣ Select Your Product
```
Product: ⦿ GNR  ○ CWF  ○ DMR
```

### 2️⃣ Generate Import CSV
```
Click [Generate...] in Import Replacement CSV section
  → Dialog opens
  → Review/customize options
  → Click [Generate]
  → CSV created and loaded automatically
```

### 3️⃣ Generate Rename CSV
```
Click [Generate...] in File Rename CSV section
  → Dialog opens
  → Review/customize options
  → Click [Generate]
  → CSV created and loaded automatically
  → Files rescanned to show renames
```

### 4️⃣ Continue with Deployment
```
[Scan Files] → Review → [Deploy Selected] → View Report
```

## What Gets Generated

### Import Replacement CSV (9 rules)

| Old Import | New Import | Description |
|------------|-----------|-------------|
| `from DebugFramework.SystemDebug import` | `from DebugFramework.GNRSystemDebug import` | Product-specific SystemDebug |
| `from DebugFramework import SystemDebug` | `from DebugFramework import GNRSystemDebug as SystemDebug` | Product-specific SystemDebug alias |
| `import DebugFramework.SystemDebug` | `import DebugFramework.GNRSystemDebug as SystemDebug` | Product-specific SystemDebug module |
| `from S2T.dpmChecks import` | `from S2T.GNRdpmChecks import` | Product-specific dpmChecks |
| `from S2T import CoreManipulation` | `from S2T import GNRCoreManipulation as CoreManipulation` | Product-specific CoreManipulation |
| `from S2T.CoreManipulation import` | `from S2T.GNRCoreManipulation import` | Product-specific CoreManipulation imports |
| `users.gaespino.dev.DebugFramework.SystemDebug` | `users.gaespino.DebugFramework.GNRSystemDebug` | Path replacement |
| `from DebugFramework.TestFramework import` | `from DebugFramework.GNRTestFramework import` | Product-specific TestFramework |
| `from DebugFramework import TestFramework` | `from DebugFramework import GNRTestFramework as TestFramework` | Product-specific TestFramework alias |

### File Rename CSV (4 rules)

| Old File | New File | Update Imports |
|----------|----------|----------------|
| `DebugFramework/SystemDebug.py` | `DebugFramework/GNRSystemDebug.py` | ✓ Yes |
| `DebugFramework/TestFramework.py` | `DebugFramework/GNRTestFramework.py` | ✓ Yes |
| `S2T/dpmChecks.py` | `S2T/GNRdpmChecks.py` | ✓ Yes |
| `S2T/CoreManipulation.py` | `S2T/GNRCoreManipulation.py` | ✓ Yes |

## Key Benefits

✨ **No Command Line Needed** - Generate CSVs directly from the UI

🎯 **Product-Aware** - Templates match your selected product (GNR/CWF/DMR)

⚡ **Auto-Load** - Generated CSVs are immediately loaded into the tool

💾 **Auto-Save** - Configuration is saved for future sessions

🔄 **Instant Feedback** - See changes immediately after generation

📝 **Customizable** - Edit product prefix, filename, and location before generation

🎨 **Preview** - See what will be generated before creating the file

## File Locations

### Default Output Location
```
C:\Git\Automation\Automation\DEVTOOLS\
  ├── import_replacement_gnr.csv
  ├── import_replacement_cwf.csv
  ├── import_replacement_dmr.csv
  ├── file_rename_gnr.csv
  ├── file_rename_cwf.csv
  └── file_rename_dmr.csv
```

### Configuration Storage
```
C:\Git\Automation\Automation\DEVTOOLS\
  └── deploy_config.json
      └── Contains CSV paths per product
```

## Tips

💡 **First Time?** Generate both CSVs for your product to get started quickly

💡 **Need Changes?** Click Generate again to overwrite and reload

💡 **Different Products?** Each product maintains separate CSV configurations

💡 **Custom Rules?** Generate the template, then edit the CSV file to add your specific rules

💡 **Testing?** Generate → Scan → Review changes before deploying

## Comparison: Before vs After

### Before (Manual Process)
```
1. Open command prompt
2. cd C:\Git\Automation\Automation\DEVTOOLS
3. python generate_import_replacement_csv.py --mode product --product GNR
4. python generate_file_rename_csv.py --mode product --product GNR
5. Back to deployment tool
6. Click "Load CSV..." for imports
7. Browse and select import_replacement_gnr.csv
8. Click "Load CSV..." for renames
9. Browse and select file_rename_gnr.csv
```

### After (Integrated Process)
```
1. Click [Generate...] for imports → Click [Generate]
2. Click [Generate...] for renames → Click [Generate]
```

**Time Saved:** ~90 seconds per product setup! 🚀
