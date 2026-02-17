# Markdown to HTML/PDF Converter

A professional markdown conversion tool with beautiful styling and easy-to-use interface. Convert your markdown documentation to polished HTML or PDF documents.

## Features

✨ **Key Features:**
- 🎨 Beautiful, professional styling with responsive design
- 📄 Convert to HTML or PDF format
- 🎯 Single file or batch directory conversion
- 🖼️ Syntax highlighting for code blocks
- 📊 Styled tables, blockquotes, and lists
- 🖨️ Print-optimized CSS for clean PDF output
- 🎨 Customizable CSS styling
- 🌓 Dark mode support
- 📱 Mobile-responsive output

## Installation

### Prerequisites

```bash
# Install Python 3.6 or higher (if not already installed)
# Then install required packages:

pip install markdown
```

### Optional: PDF Support

```bash
# For PDF conversion capability:
pip install weasyprint

# Note: WeasyPrint may require additional system dependencies:
# - Windows: No additional dependencies needed
# - Linux: sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
# - macOS: brew install pango cairo
```

## Quick Start

### Option 1: GUI Application (Recommended - Easiest!)

**Windows:**
```cmd
launch_gui.bat
```
Just double-click `launch_gui.bat` or `launch_gui.ps1`

**All Platforms:**
```bash
python md_converter_gui.py
```

The GUI provides:
- 📁 Easy file/folder selection with browse buttons
- 🎨 Visual format selection (HTML/PDF)
- 📂 Batch processing with progress tracking
- ⚙️ Custom CSS support with file picker
- 📊 Real-time status log
- 🚀 One-click conversion

### Option 2: Text Menu (Windows)

Double-click `convert_markdown.bat` and follow the menu prompts.

### Option 3: Command Line

```bash
# Convert single file to HTML
python md_converter.py report.md

# Convert to PDF
python md_converter.py report.md -f pdf

# Convert all markdown files in a directory
python md_converter.py -d ./reports/

# Convert recursively (include subdirectories)
python md_converter.py -d ./reports/ -r
```

## Usage Examples

### Basic Conversions

```bash
# Convert to HTML (opens in browser automatically)
python md_converter.py my_document.md

# Convert to PDF
python md_converter.py my_document.md -f pdf

# Specify custom output file
python md_converter.py input.md -o custom_name.html
```

### Batch Operations

```bash
# Convert all .md files in current directory to HTML
python md_converter.py -d .

# Convert all .md files to PDF recursively
python md_converter.py -d ./docs/ -f pdf -r

# Convert with custom CSS
python md_converter.py -d ./docs/ --css my_style.css
```

### Custom Styling

```bash
# Generate default CSS file for customization
python md_converter.py --generate-css

# Edit md_converter_style.css to customize appearance

# Use your custom CSS
python md_converter.py report.md --css custom_style.css
```

## File Structure

```
OtherFiles/
└── MarkdownConverter/
    ├── launch_gui.bat             # 🎨 GUI launcher for Windows
    ├── launch_gui.ps1             # 🎨 GUI launcher for PowerShell
    ├── md_converter_gui.py        # Modern GUI application
    ├── md_converter.py            # Main conversion script (CLI)
    ├── md_converter_style.css     # Default stylesheet (light + dark mode)
    ├── convert_markdown.bat       # Text menu launcher
    ├── requirements_md_converter.txt  # Python dependencies
    ├── README.md                  # Quick start guide
    └── README_md_converter.md     # This file (full documentation)
```

## Command Line Options

```
usage: md_converter.py [-h] [-f {html,pdf}] [-o OUTPUT] [-d DIRECTORY]
                       [-r] [--css CSS] [--generate-css]
                       [input]

positional arguments:
  input                 Input markdown file or directory

optional arguments:
  -h, --help           Show help message and exit
  -f, --format         Output format: html or pdf (default: html)
  -o, --output         Custom output file path
  -d, --directory      Convert all .md files in directory
  -r, --recursive      Recursively process subdirectories
  --css CSS            Custom CSS file for styling
  --generate-css       Generate default CSS file and exit
```

## Styling Features

The default stylesheet includes:

- **Professional Typography**: Clean, readable fonts optimized for both screen and print
- **Color-Coded Elements**:
  - Headers with underlines
  - Code blocks with syntax highlighting
  - Styled tables with hover effects
  - Callout boxes for warnings/info
- **Print Optimization**: Clean PDF output with proper page breaks
- **Responsive Design**: Mobile-friendly layouts
- **Enhanced Dark Mode**: Automatic dark mode detection with optimized colors
  - High-contrast link colors (#64b5f6) for excellent readability
  - Adjusted background colors for callout boxes
  - Bright heading borders and text
  - Comfortable reading experience in low-light environments
The converter automatically adds these classes:
- `.container` - Main content wrapper
- `.status-badge` - For status indicators
- `.status-failed`, `.status-success`, `.status-warning` - Status colors
- `.callout`, `.callout-warning`, `.callout-danger`, `.callout-success` - Info boxes
- `.metadata` - Metadata display boxes

### Example Custom CSS

```css
/* Your custom additions to md_converter_style.css */

/* Custom heading colors */
h1 { color: #1a237e; border-bottom-color: #1a237e; }

/* Custom code block theme */
pre {
    background: #263238;
    border-left-color: #00acc1;
}

/* Custom table styling */
th {
    background: #1a237e;
}
```

## Using the GUI Application

The GUI application (`md_converter_gui.py`) provides the easiest way to convert markdown files.

### Launch the GUI

**Windows:**
- Double-click `launch_gui.bat` in the MarkdownConverter folder
- Or run: `python md_converter_gui.py`

**Features:**

1. **Input Selection**
   - Click "Browse File" to select single or multiple markdown files
   - Click "Browse Folder" to process all .md files in a directory
   - Check "Include subdirectories" for recursive folder processing
   - Click "Clear" to reset selection

2. **Output Format**
   - Select "HTML" for web-ready documents (default)
   - Select "PDF" for print-ready documents (requires weasyprint)

3. **Output Settings**
   - Leave "Output Directory" empty to save next to source files
   - Or browse to specify a different output location
   - Check "Open file(s) after conversion" to auto-open results

4. **Custom Styling**
   - Leave "Custom CSS" empty to use default beautiful styling
   - Or browse to a custom .css file for personalized appearance

5. **Status Log**
   - Watch real-time progress in the status log
   - See which files converted successfully
   - View any errors or warnings

6. **Convert**
   - Click "🚀 Convert" to start the conversion
   - GUI remains responsive during conversion
   - Multiple files are processed automatically

### GUI Tips

- **Drag & Drop**: Select files easily with the file browser
- **Batch Processing**: Convert entire folders of markdown files at once
- **Progress Tracking**: Watch the status log for real-time feedback
- **Error Handling**: Any errors are clearly displayed in the log
- **Auto-Open**: Enable to automatically view converted files

## Tips & Best Practices

### For Best HTML Output

1. Use proper markdown headers (`#`, `##`, `###`)
2. Use fenced code blocks with language specifiers:
   ````markdown
   ```python
   def hello():
       print("Hello!")
   ```
   ````
3. Use tables for structured data
4. Add horizontal rules (`---`) for section breaks

### For Best PDF Output

1. Use the generated HTML first and preview in browser
2. Use `Ctrl+P` → "Save as PDF" for more control
3. The CSS includes print-optimized styles automatically
4. Keep images to reasonable sizes (they'll auto-scale)

### For Large Documents

1. Use `-r` flag to recursively process subdirectories
2. Convert to HTML first for quick preview
3. Generate PDFs only for final versions
4. Consider splitting very large docs into chapters

## Troubleshooting

### "markdown module not found"
```bash
pip install markdown
```

### "weasyprint module not found" (PDF conversion)
```bash
pip install weasyprint
```

### WeasyPrint Installation Issues

**Windows**: Usually works out of the box

**Linux**:
```bash
sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
pip install weasyprint
```

**macOS**:
```bash
brew install pango cairo
pip install weasyprint
```

### HTML Opens But Styling Looks Wrong

This shouldn't happen as CSS is embedded. If it does:
1. Check if CSS file exists: `md_converter_style.css`
2. Regenerate: `python md_converter.py --generate-css`
3. Try with explicit CSS: `python md_converter.py file.md --css md_converter_style.css`

### PDF Generation Fails

1. Verify weasyprint is installed: `pip list | grep weasyprint`
2. Try HTML conversion first to verify markdown is valid
3. Check for very large images (resize before conversion)
4. For Windows: Ensure no antivirus blocking PDF creation

## Examples

### Convert Technical Report
```bash
python md_converter.py BIOS_Analysis_Report.md -f pdf
```

### Convert All Documentation
```bash
python md_converter.py -d ./documentation/ -r
```

### Custom Styled Output
```bash
# Generate and customize CSS
python md_converter.py --generate-css
# Edit md_converter_style.css
python md_converter.py report.md --css md_converter_style.css
```

## License

Free to use and modify for your projects.

## Support

For issues or questions:
1. Check this README
2. Run with `-h` flag for command help
3. Check Python and package versions

## Version History

- **v1.0** - Initial release
  - HTML and PDF conversion
  - Custom CSS support
  - Batch processing
  - Interactive launcher
  - Professional styling

---

**Created by:** Automation Team
**Last Updated:** 2026-02-16
