# Visual Guide - New Features

## ✨ What's New in This Version

### 1. Visual Selection Checkboxes

Every file now has a checkbox showing its selection state:

```
☐ = Not selected (click to select)
☑ = Selected for deployment (click to deselect)
```

**How to use:**
- Click directly on the checkbox column
- Or press spacebar with file highlighted
- Or click the column header to toggle all visible files

---

### 2. Change Target Directory

New button: **"Change Target..."**

Located in the header next to the target path display.

```
Source: c:\Git\Automation\Automation\PPV
Target: c:\Git\Automation\Automation\S2T\BASELINE\DebugFramework\PPV  [Change Target...]
```

**Click it to:**
- Browse for a different deployment destination
- Deploy to multiple locations without restarting
- Automatically rescans files with the new target

**Use cases:**
- Deploy to different framework versions
- Test deployment to a staging location
- Support multiple project structures

---

### 3. Smart Filters

Two new filter checkboxes below the search box:

#### ✅ Show only files with changes
**What it does:**
- Hides all "Identical" files (gray files)
- Shows only: New files, Minor changes, Major changes
- Perfect for seeing what actually needs updating

**When to use:**
- You have 100+ files but only 10 changed
- Quick review of what's different
- Focus on files that matter

#### ✅ Show only selected  
**What it does:**
- Hides all unselected files
- Shows only files with checkboxes marked ☑
- Great for reviewing your deployment plan

**When to use:**
- Verify what you're about to deploy
- Double-check you didn't miss anything
- Final review before clicking "Deploy Selected"

---

## 🎯 Typical Workflow with New Features

### Scenario: Deploy only changed GUI files

1. **Launch the tool**
   ```
   python deploy_ppv.py
   ```

2. **Apply filters**
   - ✅ Check "Show only files with changes"
   - Type "gui" in the filter box
   - Result: Only changed GUI files visible

3. **Select files**
   - Click checkbox column header to select all visible
   - Or click individual checkboxes

4. **Review selection**
   - ✅ Check "Show only selected"
   - Verify the list looks correct

5. **Check dependencies**
   - Click "View Dependencies"
   - Add any missing dependencies

6. **Deploy**
   - Click "Deploy Selected"
   - Confirm and done!

---

## 📊 Filter Combinations

Here are powerful filter combinations:

### Find changed parsers only
```
Text Filter: "parser"
☑ Show only files with changes
☐ Show only selected
```

### Review what's about to deploy
```
Text Filter: (empty)
☐ Show only files with changes  
☑ Show only selected
```

### Find new API files
```
Text Filter: "api"
☑ Show only files with changes
☐ Show only selected
(Then look for blue-colored files in tree)
```

### Everything changed
```
Text Filter: (empty)
☑ Show only files with changes
☐ Show only selected
```

---

## 🖱️ Mouse & Keyboard Shortcuts

### Selection
- **Click** checkbox column → Toggle that file
- **Click** column header ☑ → Toggle all visible files
- **Spacebar** → Toggle highlighted file(s)
- **Ctrl+Click** → Multi-select files, then spacebar

### Navigation
- **Click** file name → Show diff and details
- **Arrow keys** → Navigate tree
- **Type** in filter box → Instant search

### Buttons
- **Select All** → Select ALL files (ignores filters)
- **Deselect All** → Clear all selections
- **Refresh** → Rescan files (keeps selections)

---

## 💡 Pro Tips

### Tip 1: Use "Show only changes" first
Start by checking "Show only files with changes" to hide all identical files. This dramatically reduces clutter and lets you focus on what matters.

### Tip 2: Column header is your friend
Click the ☑ in the column header to quickly select/deselect all visible files. Combined with filters, this is super powerful:
1. Filter to show only what you want
2. Click column header to select all visible
3. Done!

### Tip 3: Change target for testing
Before deploying to production:
1. Click "Change Target..."
2. Select a test directory
3. Deploy and test
4. Change target back to production
5. Deploy for real

### Tip 4: Combine filters creatively
Example: Find all changed Utils files that you haven't selected yet
```
Text: "utils"
☑ Show only files with changes
☐ Show only selected
```
Then scan for unchecked boxes!

### Tip 5: Review before deploy
Always enable "Show only selected" before clicking Deploy to do a final sanity check.

---

## 🔄 Before vs After

### Before (v0.9)
- No visual indication of selection
- Had to remember what you selected
- Couldn't see which files were selected
- Manual selection tracking
- Fixed target directory

### After (v1.0)
- ☑ Visual checkboxes for every file
- Click to select/deselect instantly
- See all selections at a glance
- "Show only selected" filter
- Change target directory anytime
- "Show only changes" filter
- Column header toggle all

---

## ❓ FAQ

**Q: What happens when I check "Show only selected" but nothing appears?**  
A: You haven't selected any files yet! Uncheck the filter, select some files with checkboxes, then check it again.

**Q: Does clicking the file name select it?**  
A: No, clicking the file name shows its diff. Click the checkbox to select it.

**Q: Can I use filters with Select All?**  
A: "Select All" button selects ALL files regardless of filters. Use the column header checkbox to select only visible files.

**Q: Will changing the target lose my selections?**  
A: Yes, changing target clears selections and rescans. This is intentional since file comparisons change with a new target.

**Q: Can I deploy to multiple targets?**  
A: Yes! Deploy to target #1, then click "Change Target", select target #2, reselect files, and deploy again.

---

**Enjoy the enhanced deployment experience! 🚀**
