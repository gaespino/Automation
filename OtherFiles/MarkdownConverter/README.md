# Markdown Converter Tool

Professional markdown to HTML/PDF conversion utility with beautiful styling.

## Quick Start

**🎨 GUI Application (Recommended):**
```cmd
launch_gui.bat
```
Or just double-click `launch_gui.bat`

**📝 Text Menu (Alternative):**
```cmd
convert_markdown.bat
```

**⌨️ Command Line:**
```bash
python md_converter.py your_file.md
```

## Documentation

See [README_md_converter.md](README_md_converter.md) for complete documentation, examples, and troubleshooting.

## Dark Mode

The converter automatically detects your system's dark mode preference and applies optimized colors for readability, including:
- High-contrast link colors (#64b5f6) for easy reading
- Adjusted callout boxes and code blocks
- Enhanced heading borders

## Quick Examples

```bash
# Convert to HTML
python md_converter.py report.md

# Convert to PDF
python md_converter.py report.md -f pdf

# Convert all .md files in a folder
python md_converter.py -d C:\path\to\folder

# Use custom CSS
python md_converter.py report.md --css custom.css
```

## Files

- **launch_gui.bat / launch_gui.ps1** - 🎨 GUI launcher (easiest!)
- **md_converter_gui.py** - Modern graphical interface
- **md_converter.py** - Main conversion script (CLI)
- **md_converter_style.css** - Professional stylesheet (light + dark mode)
- **convert_markdown.bat** - Text-based menu interface
- **requirements_md_converter.txt** - Python dependencies
- **README_md_converter.md** - Full documentation

## Features

✨ **GUI Features:**
- 📁 Drag-and-drop file selection
- 📂 Batch folder processing
- 🎨 Custom CSS support
- 📊 Real-time status logging
- ⚙️ Easy format selection (HTML/PDF)
- 🚀 One-click conversion

---

**Location:** `C:\Git\Automation\OtherFiles\MarkdownConverter\`
