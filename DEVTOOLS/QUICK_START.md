# PPV Deployment Tool - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Launch the Tool
Double-click `launch_deploy.bat` or run:
```powershell
python deploy_ppv.py
```

### Step 2: Select Files
- Browse the file tree
- Click the checkbox (☐/☑) next to files to select them
- Click files to see detailed changes in the diff viewer
- Use filters to narrow down:
  - ✅ "Show only files with changes" - Hide identical files
  - ✅ "Show only selected" - Review your selection
- Use "Select All" or manually pick files
- Check the diff preview to understand changes

### Step 3: Deploy
- Click "Deploy Selected"
- Confirm the deployment
- Done! Files are copied with automatic backup

---

## 📋 Common Scenarios

### Scenario 1: Update a Single Module
**Goal**: Deploy changes to `MCAparser.py`

1. Launch the tool
2. Type "MCAparser" in the filter box
3. Click the file to see changes
4. If changes look good, click to select
5. Click "View Dependencies" to see what else might be needed
6. Deploy!

### Scenario 2: Deploy New Feature
**Goal**: Add a new GUI tool to DebugFramework

1. Launch the tool
2. Look for files marked "New File" (blue)
3. Select your new file
4. Click "View Dependencies" to find required modules
5. Select any missing dependencies
6. Deploy all together

### Scenario 3: Sync Multiple Files After Major Update
**Goal**: Update several parsers after refactoring

1. Launch the tool
2. Navigate to `parsers/` folder
3. Review each file's similarity score
4. Select files with changes
5. Watch for "Major Changes" warnings (red files)
6. Review major changes carefully in diff view
7. Deploy when ready

---

## 🎨 Understanding the Interface

### Selection Checkboxes
- ☐ = Not selected for deployment
- ☑ = Selected for deployment
- Click the checkbox or press spacebar to toggle
- Click column header (☑) to toggle all visible files

### File Tree Colors
- 🔵 **Blue** = New file (doesn't exist in target)
- 🟠 **Orange** = Minor changes (30-90% similar)
- 🔴 **Red** = Major changes (<30% similar - review carefully!)
- ⚪ **Gray** = Identical (no changes needed)

### Status Column
- **New File** → Will be created in target
- **Identical** → Already up to date (skip)
- **Minimal Changes** → Very small tweaks (90%+ similar)
- **Minor Changes** → Moderate updates (30-90% similar)
- **Major Changes** → Significant differences (<30% similar)

### Similarity Column
Shows percentage match between source and target:
- 100% = Exactly the same
- 90-99% = A few lines changed
- 50-89% = Moderate changes
- 0-49% = Substantial differences

---

## ⚠️ Safety Features

### Automatic Backups
Before ANY file is overwritten, the original is backed up to:
```
DEVTOOLS\backups\{timestamp}\
```
Example: `backups\20251209_143022\`

### Major Change Warnings
If files have <30% similarity, you'll get a warning dialog:
```
⚠️ WARNING: Major changes detected

The following files have major changes (< 30% similarity):
  • parsers/MCAparser.py
  • gui/PPVTools.py

Do you want to continue?
```

Review these carefully - the target might have custom modifications!

### Confirmation Dialogs
- Confirm before deployment
- Review major changes
- See backup location before proceeding

---

## 🔧 Configuration

Edit `deploy_config.json` to customize:

```json
{
  "paths": {
    "source_base": "c:\\Git\\Automation\\Automation\\PPV",
    "target_base": "c:\\Git\\Automation\\Automation\\S2T\\BASELINE\\DebugFramework\\PPV",
    "backup_base": "c:\\Git\\Automation\\Automation\\DEVTOOLS\\backups"
  },
  "settings": {
    "similarity_threshold": 0.3
  }
}
```

**Change target location?** Edit `target_base`  
**Deploy from different source?** Edit `source_base`  
**Adjust "major changes" sensitivity?** Edit `similarity_threshold`

---

## 💡 Pro Tips

### Tip 1: Use Dependencies Feature
Before deploying a file, click "View Dependencies" to see what modules it imports. Make sure to deploy dependencies too!

### Tip 2: Smart Filtering
Multiple ways to narrow down your view:
- **Text search**: Type "parser" to find parser files
- **Show only changes**: ✅ Check to hide identical files
- **Show only selected**: ✅ Review what you're deploying
- **Combine filters**: Search "gui" + "Show only changes" = changed GUI files only!

### Tip 3: Review Diffs Carefully
The diff preview shows exactly what will change:
- **Green lines** = Added
- **Red lines** = Removed
- Scroll through to understand the impact

### Tip 4: Don't Deploy Everything
DebugFramework doesn't need:
- ❌ `install_dependencies.py`
- ❌ `requirements.txt`
- ❌ `ExperimentBuilder.py` (standalone tool)
- ❌ `configs/` (handled separately)
- ❌ `.vscode/` (development only)

Only deploy what's actually used by DebugFramework!

### Tip 5: Test After Deployment
Always test after deploying:
```powershell
cd c:\Git\Automation\Automation\S2T\BASELINE\DebugFramework\PPV
python run.py
```

---

## 🐛 Troubleshooting

### Problem: Files not showing up
**Solution**: Click "Refresh" button

### Problem: Can't see differences
**Solution**: Click on the file name in the tree (single click)

### Problem: Deployment failed
**Solution**: 
1. Check the error message
2. Your files are safe in the backup folder
3. Close any programs using those files
4. Try again

### Problem: Wrong files deployed
**Solution**:
1. Go to backup folder
2. Find the timestamp folder
3. Copy files back manually
4. Or use the script to redeploy correct files

---

## 📞 Getting Help

1. **Read the README**: Check `README.md` for detailed documentation
2. **Check Config**: Review `deploy_config.json` settings
3. **Check Backups**: All backups are in `backups/` folder

---

## ✅ Deployment Checklist

Before deploying, verify:
- [ ] Selected the correct files
- [ ] Reviewed changes in diff preview
- [ ] Checked dependencies (if applicable)
- [ ] Understood what "major changes" mean
- [ ] Ready to test after deployment

After deploying:
- [ ] Check backup was created
- [ ] Test the DebugFramework
- [ ] Verify files work as expected

---

**Happy Deploying! 🚀**

Remember: When in doubt, check the diff preview. The tool shows you exactly what will change before you commit!
