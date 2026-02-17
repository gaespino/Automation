# Markdown Converter - GUI Quick Guide

## 🚀 Getting Started with the GUI

### Launch Methods

1. **Easiest:** Double-click `launch_gui.bat`
2. **PowerShell:** Double-click `launch_gui.ps1`
3. **Command:** `python md_converter_gui.py`

---

## 🖥️ GUI Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  📄 Markdown to HTML/PDF Converter                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ Input ─────────────────────────────────────────────────┐  │
│  │ File(s): [Selected files display here]                   │  │
│  │                                                           │  │
│  │  [ Browse File ]  [ Browse Folder ]  [ Clear ]          │  │
│  │  ☐ Include subdirectories (for folders)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Output Format ──────────────────────────────────────────┐  │
│  │  ○ HTML      ○ PDF (requires weasyprint)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Output Settings ────────────────────────────────────────┐  │
│  │ Output Directory: [path]              [ Browse ]         │  │
│  │ (Leave empty to save in source location)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Styling (Optional) ─────────────────────────────────────┐  │
│  │ Custom CSS: [path]                    [ Browse ]         │  │
│  │ ☑ Open file(s) after conversion                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Status Log ─────────────────────────────────────────────┐  │
│  │ Ready. Select files to convert.                          │  │
│  │                                                           │  │
│  │ (Real-time conversion progress shown here)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [🚀 Convert] [Clear Log] [About] [Exit]                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 Step-by-Step Usage

### Single File Conversion

1. **Select File**
   - Click `Browse File`
   - Select one or more .md files
   - Files appear in the input display

2. **Choose Format**
   - Select `HTML` (recommended) or `PDF`

3. **Convert**
   - Click `🚀 Convert`
   - Watch progress in status log
   - File opens automatically (if enabled)

### Batch Folder Conversion

1. **Select Folder**
   - Click `Browse Folder`
   - Choose folder containing .md files
   - Check `Include subdirectories` if needed

2. **Set Output** (Optional)
   - Leave empty to save with source files
   - Or click `Browse` to specify output folder

3. **Convert**
   - Click `🚀 Convert`
   - All markdown files process automatically
   - Progress shown in status log

### Custom Styling

1. **Prepare CSS**
   - Create or edit .css file
   - Or use generated default: `md_converter_style.css`

2. **Apply CSS**
   - Click `Browse` next to Custom CSS
   - Select your .css file

3. **Convert**
   - Your custom styles apply to all converted files

---

## 💡 Tips & Tricks

### File Selection
- **Multiple Files:** Ctrl+Click or Shift+Click in file browser
- **Quick Clear:** Use Clear button to reset selection
- **Folder vs Files:** Browse File for specific files, Browse Folder for all .md files

### Output Options
- **Same Location:** Leave Output Directory empty
- **Organized Output:** Set output directory to collect all results
- **Auto-Open:** Keep checked to review results immediately

### Performance
- **Large Batches:** Process 50+ files easily with status tracking
- **PDF Note:** PDF conversion is slower than HTML
- **Responsive:** GUI stays usable during conversion

### Status Log
- ✓ Green checkmarks = Success
- ❌ Red X = Errors
- ⚠️ Yellow warning = Non-critical issues
- Clear Log button resets for next batch

---

## 🐛 Troubleshooting

### "No files selected" error
- **Solution:** Click Browse File or Browse Folder first

### PDF conversion fails
- **Issue:** weasyprint not installed
- **Solution:** Run `pip install weasyprint`

### GUI won't launch
- **Issue:** Python not in PATH
- **Solution:** Reinstall Python with "Add to PATH" checked

### Files not opening automatically
- **Issue:** Security settings or no default app
- **Solution:** Uncheck "Open after" and open manually

---

## ⌨️ Keyboard Shortcuts

- **Tab/Shift+Tab:** Navigate between fields
- **Space:** Toggle checkboxes
- **Enter:** Activate buttons (when focused)
- **Alt+F4:** Close window

---

## 🎨 Interface Features

### Color Coding
- **Blue accents:** Interactive buttons and links
- **Green (✓):** Successful operations
- **Red (❌):** Errors
- **Yellow (⚠️):** Warnings

### Real-time Feedback
- Immediate file count after selection
- Progress updates during conversion
- Completion summary with statistics

### User-Friendly
- No command-line knowledge needed
- Clear labeling and instructions
- Tooltips and help text
- Responsive design

---

## 📊 Example Workflow

### Converting a Report

1. Launch GUI: Double-click `launch_gui.bat`
2. Click `Browse File`
3. Select `BIOS_Report.md`
4. Format: Select `HTML`
5. Click `🚀 Convert`
6. Report opens in browser
7. Done! ✨

### Batch Converting Documentation

1. Launch GUI
2. Click `Browse Folder`
3. Select `C:\Docs\` folder
4. Check `Include subdirectories`
5. Output Directory: `C:\Docs\HTML_Output\`
6. Click `🚀 Convert`
7. Watch status log for progress
8. All files converted! 🎉

---

## 🔄 Version Info

**Current Version:** 1.0
**Last Updated:** 2026-02-16

**Features:**
- Modern tkinter-based GUI
- Multi-threaded conversion (non-blocking)
- Batch processing support
- Real-time status logging
- Custom CSS support
- Auto-open results

---

For command-line usage and advanced features, see [README_md_converter.md](README_md_converter.md)
