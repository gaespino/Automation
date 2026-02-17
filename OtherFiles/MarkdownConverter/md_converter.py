#!/usr/bin/env python3
"""
Markdown to HTML/PDF Converter
Converts markdown files to beautifully formatted HTML or PDF documents
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime

try:
    import markdown
    from markdown.extensions import tables, fenced_code, codehilite, toc
except ImportError:
    print("ERROR: 'markdown' package not installed.")
    print("Please run: pip install markdown")
    sys.exit(1)

# Optional PDF support
PDF_AVAILABLE = False
try:
    from weasyprint import HTML, CSS
    PDF_AVAILABLE = True
except ImportError:
    pass


class MarkdownConverter:
    """Convert markdown files to HTML or PDF with beautiful styling"""

    def __init__(self, css_file=None):
        self.css_file = css_file or self._get_default_css_path()
        self.md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'nl2br',
            'sane_lists'
        ])

    def _get_default_css_path(self):
        """Get path to default CSS file"""
        script_dir = Path(__file__).parent
        return script_dir / "md_converter_style.css"

    def _load_css(self):
        """Load CSS content"""
        if self.css_file and os.path.exists(self.css_file):
            with open(self.css_file, 'r', encoding='utf-8') as f:
                return f.read()
        return self._get_default_inline_css()

    def _get_default_inline_css(self):
        """Return default inline CSS if no file found"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        h1 { font-size: 2em; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { font-size: 1.5em; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; }
        h3 { font-size: 1.25em; }
        code {
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }
        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }
        pre code {
            background: transparent;
            color: #ecf0f1;
            padding: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }
        th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        tr:hover { background: #f8f9fa; }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background: #f8f9fa;
        }
        hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        li {
            margin: 8px 0;
        }
        @media print {
            @page { margin: 0.75in; }
            body { font-size: 10pt; background: white; }
            .container { box-shadow: none; }
            h1 { font-size: 18pt; page-break-after: avoid; }
            h2 { font-size: 14pt; page-break-after: avoid; }
            h3 { font-size: 12pt; page-break-after: avoid; }
            table, pre, code { page-break-inside: avoid; }
        }
        """

    def _create_html_template(self, title, content, css):
        """Create complete HTML document"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
{content}
        <hr>
        <div style="text-align: center; color: #7f8c8d; font-size: 0.9em; margin-top: 40px;">
            <p><strong>Generated:</strong> {timestamp} | <strong>Source:</strong> {title}</p>
        </div>
    </div>
</body>
</html>"""

    def convert_to_html(self, md_file, output_file=None):
        """Convert markdown file to HTML"""
        md_path = Path(md_file)

        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_file}")

        # Read markdown content
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert to HTML
        html_content = self.md.convert(md_content)
        self.md.reset()  # Reset for next conversion

        # Load CSS
        css = self._load_css()

        # Get title from first H1 or filename
        title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
        title = title_match.group(1) if title_match else md_path.stem

        # Create complete HTML
        full_html = self._create_html_template(title, html_content, css)

        # Determine output file
        if output_file is None:
            output_file = md_path.with_suffix('.html')

        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)

        return output_file

    def convert_to_pdf(self, md_file, output_file=None):
        """Convert markdown file to PDF via HTML"""
        if not PDF_AVAILABLE:
            raise ImportError(
                "PDF conversion requires 'weasyprint' package.\n"
                "Install with: pip install weasyprint\n"
                "Note: WeasyPrint requires additional system dependencies on some platforms."
            )

        # First convert to HTML
        md_path = Path(md_file)
        temp_html = md_path.with_suffix('.temp.html')

        try:
            self.convert_to_html(md_file, temp_html)

            # Determine output file
            if output_file is None:
                output_file = md_path.with_suffix('.pdf')

            # Convert HTML to PDF
            HTML(filename=str(temp_html)).write_pdf(output_file)

            return output_file

        finally:
            # Clean up temp HTML
            if temp_html.exists():
                temp_html.unlink()

    def convert_directory(self, directory, output_format='html', recursive=False):
        """Convert all markdown files in a directory"""
        dir_path = Path(directory)
        pattern = '**/*.md' if recursive else '*.md'

        converted_files = []
        errors = []

        for md_file in dir_path.glob(pattern):
            try:
                if output_format.lower() == 'pdf':
                    output = self.convert_to_pdf(md_file)
                else:
                    output = self.convert_to_html(md_file)

                converted_files.append(output)
                print(f"✓ Converted: {md_file.name} -> {output.name}")

            except Exception as e:
                errors.append((md_file, str(e)))
                print(f"✗ Error converting {md_file.name}: {e}")

        return converted_files, errors


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Convert Markdown files to HTML or PDF with beautiful styling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file to HTML
  python md_converter.py report.md

  # Convert to PDF
  python md_converter.py report.md -f pdf

  # Convert all markdown files in directory
  python md_converter.py -d ./reports/

  # Convert with custom CSS
  python md_converter.py report.md --css custom.css

  # Specify output file
  python md_converter.py report.md -o output.html
        """
    )

    parser.add_argument('input', nargs='?', help='Input markdown file or directory')
    parser.add_argument('-f', '--format', choices=['html', 'pdf'], default='html',
                        help='Output format (default: html)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-d', '--directory', help='Convert all .md files in directory')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Recursively process subdirectories')
    parser.add_argument('--css', help='Custom CSS file for styling')
    parser.add_argument('--generate-css', action='store_true',
                        help='Generate default CSS file and exit')

    args = parser.parse_args()

    # Generate CSS file if requested
    if args.generate_css:
        css_path = Path(__file__).parent / "md_converter_style.css"
        converter = MarkdownConverter()
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(converter._load_css())
        print(f"✓ Generated CSS file: {css_path}")
        return 0

    # Validate input
    if not args.input and not args.directory:
        parser.print_help()
        return 1

    # Check PDF dependencies
    if args.format == 'pdf' and not PDF_AVAILABLE:
        print("ERROR: PDF conversion requires 'weasyprint' package.")
        print("Install with: pip install weasyprint")
        print("\nNote: WeasyPrint requires additional system dependencies:")
        print("  Windows: No additional dependencies needed")
        print("  Linux: libpango, libcairo, libgdk-pixbuf")
        print("  macOS: brew install pango cairo")
        return 1

    # Create converter
    converter = MarkdownConverter(css_file=args.css)

    try:
        # Directory mode
        if args.directory:
            print(f"Converting {args.format.upper()} files in: {args.directory}")
            if args.recursive:
                print("(Recursive mode enabled)")

            converted, errors = converter.convert_directory(
                args.directory,
                output_format=args.format,
                recursive=args.recursive
            )

            print(f"\n{'='*60}")
            print(f"✓ Successfully converted: {len(converted)} file(s)")
            if errors:
                print(f"✗ Failed: {len(errors)} file(s)")

            return 0 if not errors else 1

        # Single file mode
        else:
            input_file = args.input
            output_file = args.output

            print(f"Converting: {input_file}")

            if args.format == 'pdf':
                result = converter.convert_to_pdf(input_file, output_file)
            else:
                result = converter.convert_to_html(input_file, output_file)

            print(f"✓ Successfully created: {result}")

            # Open in browser for HTML
            if args.format == 'html' and not args.output:
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(result)}')
                print("  (Opened in default browser)")

            return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
