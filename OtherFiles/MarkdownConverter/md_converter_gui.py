#!/usr/bin/env python3
"""
Markdown Converter GUI
Modern graphical interface for converting markdown files to HTML/PDF
"""

import os
import sys
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# Import the converter
try:
    from md_converter import MarkdownConverter
except ImportError:
    print("ERROR: Could not import md_converter module")
    print("Make sure md_converter.py is in the same directory")
    sys.exit(1)


class MarkdownConverterGUI:
    """Modern GUI for Markdown Converter"""

    def __init__(self, root):
        self.root = root
        self.root.title("Markdown Converter")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Set minimum size
        self.root.minsize(700, 600)

        # Variables
        self.input_files = []
        self.output_format = StringVar(value="html")
        self.output_dir = StringVar(value="")
        self.custom_css = StringVar(value="")
        self.recursive = BooleanVar(value=False)
        self.open_after = BooleanVar(value=True)

        # Configure style
        self.setup_styles()

        # Create UI
        self.create_widgets()

        # Configure grid weights for resizing
        self.root.grid_rowconfigure(5, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Set icon (optional, will fail gracefully if not found)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass

    def setup_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        bg_color = '#f5f5f5'
        fg_color = '#2c3e50'
        accent_color = '#3498db'
        button_color = '#3498db'
        button_hover = '#2980b9'

        # Frame style
        style.configure('TFrame', background=bg_color)
        style.configure('Title.TLabel',
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 16, 'bold'))
        style.configure('TLabel',
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 10))
        style.configure('TButton',
                       background=button_color,
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10))
        style.map('TButton',
                 background=[('active', button_hover)])

        # Radiobutton style
        style.configure('TRadiobutton',
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 10))

        # Checkbutton style
        style.configure('TCheckbutton',
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 10))

        # Configure root background
        self.root.configure(bg=bg_color)

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        main_frame.columnconfigure(1, weight=1)

        # Title
        title = ttk.Label(main_frame, text="📄 Markdown to HTML/PDF Converter", style='Title.TLabel')
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="File(s):").grid(row=0, column=0, sticky=W, pady=5)
        self.input_display = Text(input_frame, height=3, width=50, wrap='word',
                                  font=('Segoe UI', 9))
        self.input_display.grid(row=0, column=1, sticky=(W, E), padx=(10, 5), pady=5)
        self.input_display.insert('1.0', 'No files selected')
        self.input_display.config(state='disabled')

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=2, sticky=(N, S))

        ttk.Button(btn_frame, text="Browse File",
                  command=self.browse_file, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="Browse Folder",
                  command=self.browse_folder, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="Clear",
                  command=self.clear_input, width=12).pack(pady=2)

        # Recursive option (for folders)
        ttk.Checkbutton(input_frame, text="Include subdirectories (for folders)",
                       variable=self.recursive).grid(row=1, column=1, sticky=W, pady=5)

        # Output format section
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="10")
        format_frame.grid(row=2, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))

        ttk.Radiobutton(format_frame, text="HTML",
                       variable=self.output_format,
                       value="html").grid(row=0, column=0, padx=10, pady=5)
        ttk.Radiobutton(format_frame, text="PDF (requires weasyprint)",
                       variable=self.output_format,
                       value="pdf").grid(row=0, column=1, padx=10, pady=5)

        # Output directory section
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Directory:").grid(row=0, column=0, sticky=W, pady=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir)
        output_entry.grid(row=0, column=1, sticky=(W, E), padx=(10, 5), pady=5)
        ttk.Button(output_frame, text="Browse",
                  command=self.browse_output_dir, width=10).grid(row=0, column=2, pady=5)

        ttk.Label(output_frame, text="(Leave empty to save in source location)",
                 font=('Segoe UI', 8, 'italic')).grid(row=1, column=1, sticky=W, pady=(0, 5))

        # CSS customization section
        css_frame = ttk.LabelFrame(main_frame, text="Styling (Optional)", padding="10")
        css_frame.grid(row=4, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))
        css_frame.columnconfigure(1, weight=1)

        ttk.Label(css_frame, text="Custom CSS:").grid(row=0, column=0, sticky=W, pady=5)
        css_entry = ttk.Entry(css_frame, textvariable=self.custom_css)
        css_entry.grid(row=0, column=1, sticky=(W, E), padx=(10, 5), pady=5)
        ttk.Button(css_frame, text="Browse",
                  command=self.browse_css, width=10).grid(row=0, column=2, pady=5)

        ttk.Checkbutton(css_frame, text="Open file(s) after conversion",
                       variable=self.open_after).grid(row=1, column=1, sticky=W, pady=5)

        # Log/Output section
        log_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(W, E, N, S), pady=(0, 10))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = ScrolledText(log_frame, height=12, width=70,
                                     font=('Consolas', 9), wrap='word')
        self.log_text.grid(row=0, column=0, sticky=(W, E, N, S))
        self.log_text.insert('1.0', 'Ready. Select files to convert.\n')
        self.log_text.config(state='disabled')

        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))

        self.convert_btn = ttk.Button(button_frame, text="🚀 Convert",
                                      command=self.convert, width=15)
        self.convert_btn.pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="Clear Log",
                  command=self.clear_log, width=15).pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="About",
                  command=self.show_about, width=15).pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="Exit",
                  command=self.root.quit, width=15).pack(side=LEFT, padx=5)

    def log(self, message, level='info'):
        """Add message to log"""
        self.log_text.config(state='normal')

        # Color coding
        if level == 'error':
            prefix = '❌ ERROR: '
        elif level == 'success':
            prefix = '✓ '
        elif level == 'warning':
            prefix = '⚠️ WARNING: '
        else:
            prefix = ''

        self.log_text.insert('end', f"{prefix}{message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def clear_log(self):
        """Clear the log"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

    def browse_file(self):
        """Browse for markdown file(s)"""
        files = filedialog.askopenfilenames(
            title="Select Markdown File(s)",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if files:
            self.input_files = list(files)
            self.update_input_display()

    def browse_folder(self):
        """Browse for folder containing markdown files"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.input_files = [folder]
            self.update_input_display()

    def browse_output_dir(self):
        """Browse for output directory"""
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_dir.set(folder)

    def browse_css(self):
        """Browse for custom CSS file"""
        file = filedialog.askopenfilename(
            title="Select CSS File",
            filetypes=[("CSS files", "*.css"), ("All files", "*.*")]
        )
        if file:
            self.custom_css.set(file)

    def clear_input(self):
        """Clear input selection"""
        self.input_files = []
        self.update_input_display()

    def update_input_display(self):
        """Update the input display text"""
        self.input_display.config(state='normal')
        self.input_display.delete('1.0', 'end')

        if not self.input_files:
            self.input_display.insert('1.0', 'No files selected')
        else:
            text = '\n'.join([Path(f).name if os.path.isfile(f) else f"📁 {Path(f).name}"
                            for f in self.input_files])
            self.input_display.insert('1.0', text)

        self.input_display.config(state='disabled')

    def convert(self):
        """Perform conversion"""
        if not self.input_files:
            messagebox.showwarning("No Input", "Please select file(s) or folder to convert.")
            return

        # Disable convert button during conversion
        self.convert_btn.config(state='disabled')
        self.clear_log()

        # Run conversion in separate thread to keep GUI responsive
        thread = threading.Thread(target=self._do_conversion, daemon=True)
        thread.start()

    def _do_conversion(self):
        """Actual conversion logic (runs in thread)"""
        try:
            # Get parameters
            output_format = self.output_format.get()
            output_dir = self.output_dir.get() or None
            custom_css = self.custom_css.get() or None
            recursive = self.recursive.get()

            # Create converter
            converter = MarkdownConverter(css_file=custom_css)

            self.log(f"Starting conversion to {output_format.upper()}...")
            self.log("=" * 60)

            converted_files = []
            total_files = 0
            errors = 0

            for input_path in self.input_files:
                path = Path(input_path)

                # Check if it's a directory
                if path.is_dir():
                    self.log(f"Processing directory: {path.name}")
                    pattern = '**/*.md' if recursive else '*.md'
                    md_files = list(path.glob(pattern))

                    if not md_files:
                        self.log(f"No markdown files found in {path.name}", 'warning')
                        continue

                    self.log(f"Found {len(md_files)} markdown file(s)")

                    for md_file in md_files:
                        total_files += 1
                        try:
                            output_file = self._get_output_path(md_file, output_format, output_dir)

                            if output_format == 'pdf':
                                result = converter.convert_to_pdf(md_file, output_file)
                            else:
                                result = converter.convert_to_html(md_file, output_file)

                            converted_files.append(result)
                            self.log(f"Converted: {md_file.name} → {Path(result).name}", 'success')

                        except Exception as e:
                            errors += 1
                            self.log(f"Failed to convert {md_file.name}: {e}", 'error')

                # Single file
                elif path.is_file():
                    total_files += 1
                    try:
                        output_file = self._get_output_path(path, output_format, output_dir)

                        if output_format == 'pdf':
                            result = converter.convert_to_pdf(path, output_file)
                        else:
                            result = converter.convert_to_html(path, output_file)

                        converted_files.append(result)
                        self.log(f"Converted: {path.name} → {Path(result).name}", 'success')

                    except Exception as e:
                        errors += 1
                        self.log(f"Failed to convert {path.name}: {e}", 'error')

                else:
                    self.log(f"Path not found: {input_path}", 'error')
                    errors += 1

            # Summary
            self.log("=" * 60)
            self.log(f"Conversion complete!")
            self.log(f"✓ Successfully converted: {total_files - errors}/{total_files} file(s)")
            if errors > 0:
                self.log(f"✗ Failed: {errors} file(s)", 'warning')

            # Open files if requested
            if self.open_after.get() and converted_files:
                self.log(f"Opening {len(converted_files)} file(s)...")
                for file in converted_files[:3]:  # Limit to first 3 to avoid overwhelming
                    try:
                        os.startfile(file)
                    except Exception as e:
                        self.log(f"Could not open {Path(file).name}: {e}", 'warning')

                if len(converted_files) > 3:
                    self.log(f"(Only opened first 3 files to avoid overwhelming your system)")

            # Show success message
            if errors == 0 and total_files > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Successfully converted {total_files} file(s) to {output_format.upper()}!"
                ))

        except Exception as e:
            self.log(f"Unexpected error: {e}", 'error')
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred during conversion:\n\n{str(e)}"
            ))

        finally:
            # Re-enable convert button
            self.root.after(0, lambda: self.convert_btn.config(state='normal'))

    def _get_output_path(self, input_path, format, output_dir):
        """Determine output file path"""
        input_path = Path(input_path)

        if output_dir:
            # Use specified output directory
            output_path = Path(output_dir) / input_path.with_suffix(f'.{format}').name
        else:
            # Save in same location as input
            output_path = input_path.with_suffix(f'.{format}')

        return output_path

    def show_about(self):
        """Show about dialog"""
        about_text = """Markdown to HTML/PDF Converter
Version 1.0

A professional tool for converting markdown
documents to beautifully styled HTML or PDF files.

Features:
• Single file or batch conversion
• Custom CSS styling support
• Dark mode optimized output
• Print-friendly PDF generation

Created: 2026"""

        messagebox.showinfo("About", about_text)


def main():
    """Main entry point"""
    root = Tk()
    app = MarkdownConverterGUI(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == '__main__':
    main()
