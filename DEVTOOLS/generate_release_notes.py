#!/usr/bin/env python3
"""
Debug Framework Release Notes Generator

This script automates the collection of changes from deployment reports and source code
to jumpstart the release notes generation process.

Usage:
    python generate_release_notes.py --start-date 2026-01-22 --end-date 2026-02-18
    python generate_release_notes.py --start-date 2026-01-22 --end-date 2026-02-18 --output DRAFT_RELEASE.md
    python generate_release_notes.py --version 1.7.1 --start-date 2026-01-22

Author: THR Debug Framework Team
Version: 1.0
Last Updated: February 18, 2026
"""

import argparse
import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class ReleaseNotesGenerator:
    """Generate release notes from deployment reports and source code markers."""

    def __init__(self, start_date: str, end_date: str = None, version: str = None):
        """
        Initialize the generator.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)
            version: Release version (e.g., "1.7.1")
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        self.version = version or "X.X.X"

        # Base paths
        self.devtools_path = Path(__file__).parent
        self.workspace_path = self.devtools_path.parent
        self.baseline_path = self.workspace_path / "S2T" / "BASELINE"
        self.baseline_dmr_path = self.workspace_path / "S2T" / "BASELINE_DMR"

        # Data storage
        self.deployment_reports: List[Dict] = []
        self.code_changes: Dict[str, List[Tuple[str, int, str]]] = {
            "NEW": [],
            "FIXED": [],
            "ADDED": [],
            "UPDATED": [],
        }
        self.new_files: List[str] = []
        self.modified_files: List[Tuple[str, str, float]] = []  # (file, product, similarity)

    def parse_deployment_reports(self):
        """Parse all deployment reports in the date range."""
        print(f"📊 Parsing deployment reports from {self.start_date.date()} to {self.end_date.date()}...")

        # Find all CSV reports
        report_files = list(self.devtools_path.glob("deployment_report_*.csv"))

        for report_file in report_files:
            # Extract date from filename: deployment_report_YYYYMMDD_HHMMSS.csv
            match = re.search(r'deployment_report_(\d{8})_(\d{6})\.csv', report_file.name)
            if not match:
                continue

            date_str = match.group(1)
            report_date = datetime.strptime(date_str, "%Y%m%d")

            # Check if within date range
            if self.start_date <= report_date <= self.end_date:
                self._parse_single_report(report_file, report_date)

        print(f"   Found {len(self.deployment_reports)} deployment reports")
        print(f"   New files: {len(self.new_files)}")
        print(f"   Modified files: {len(self.modified_files)}")

    def _parse_single_report(self, report_file: Path, report_date: datetime):
        """Parse a single deployment report CSV."""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Store report data
                    entry = {
                        'date': report_date,
                        'file': row.get('Source File', ''),
                        'target': row.get('Target File', ''),
                        'product': row.get('Product', 'Unknown'),
                        'similarity': float(row.get('Similarity (%)', 0)),
                        'status': row.get('Status', ''),
                    }
                    self.deployment_reports.append(entry)

                    # Classify as new or modified
                    if entry['similarity'] == 0 or 'NEW' in entry['status'].upper():
                        self.new_files.append(entry['target'])
                    else:
                        self.modified_files.append((entry['target'], entry['product'], entry['similarity']))

        except Exception as e:
            print(f"   ⚠️  Error parsing {report_file.name}: {e}")

    def search_code_markers(self):
        """Search for code change markers in Python files."""
        print(f"\n🔍 Searching for code change markers...")

        # Search both BASELINE and BASELINE_DMR
        paths_to_search = [
            (self.baseline_path, "BASELINE"),
            (self.baseline_dmr_path, "BASELINE_DMR"),
        ]

        marker_pattern = re.compile(r'#\s*(NEW|FIXED|ADDED|UPDATED)[:\-\s]*(.+)', re.IGNORECASE)

        for base_path, repo_name in paths_to_search:
            if not base_path.exists():
                print(f"   ⚠️  {repo_name} not found at {base_path}")
                continue

            # Search all .py files
            python_files = list(base_path.rglob("*.py"))
            print(f"   Searching {len(python_files)} Python files in {repo_name}...")

            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            match = marker_pattern.search(line)
                            if match:
                                marker_type = match.group(1).upper()
                                description = match.group(2).strip()
                                relative_path = py_file.relative_to(self.workspace_path)

                                self.code_changes[marker_type].append(
                                    (str(relative_path), line_num, description)
                                )
                except Exception as e:
                    # Skip files that can't be read
                    pass

        # Print summary
        for marker_type, changes in self.code_changes.items():
            if changes:
                print(f"   {marker_type}: {len(changes)} instances")

    def find_new_markdown_docs(self) -> List[Tuple[str, datetime]]:
        """Find new or recently updated markdown documentation files."""
        print(f"\n📚 Searching for new/updated documentation...")

        new_docs = []
        paths_to_search = [
            self.baseline_path,
            self.baseline_dmr_path,
            self.devtools_path,
        ]

        for base_path in paths_to_search:
            if not base_path.exists():
                continue

            for md_file in base_path.rglob("*.md"):
                # Get file modification time
                mod_time = datetime.fromtimestamp(md_file.stat().st_mtime)

                # Check if modified in date range
                if self.start_date <= mod_time <= self.end_date:
                    relative_path = md_file.relative_to(self.workspace_path)
                    new_docs.append((str(relative_path), mod_time))

        new_docs.sort(key=lambda x: x[1], reverse=True)
        print(f"   Found {len(new_docs)} documentation files")

        return new_docs

    def generate_markdown_output(self, output_file: str = None):
        """Generate markdown output with collected data."""
        print(f"\n📝 Generating release notes markdown...")

        if not output_file:
            output_file = f"DRAFT_RELEASE_v{self.version}_{datetime.now().strftime('%b%Y')}.md"

        output_path = self.devtools_path / "deploys" / output_file

        # Ensure deploys directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Debug Framework Release v{self.version} - DRAFT\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y %H:%M')}\n")
            f.write(f"**Date Range:** {self.start_date.date()} to {self.end_date.date()}\n\n")
            f.write("---\n\n")
            f.write("> ⚠️ **DRAFT DOCUMENT** - Review and fill in details before finalizing\n\n")
            f.write("---\n\n")

            # Release Information
            f.write("## Release Information\n\n")
            f.write(f"- **Version:** {self.version}\n")
            f.write(f"- **Release Date:** [TO BE DETERMINED]\n")
            f.write(f"- **Previous Version:** [FILL IN]\n")
            f.write("- **Products:** GNR (Granite Rapids), CWF (Clearwater Forest), DMR (Diamond Rapids)\n")
            f.write("- **Repositories:** BASELINE (GNR/CWF), BASELINE_DMR (DMR)\n\n")
            f.write("---\n\n")

            # Overview
            f.write("## Overview\n\n")
            f.write("[TODO: Write 2-3 sentence summary of release highlights]\n\n")
            f.write("---\n\n")

            # New Files
            if self.new_files:
                f.write("## 🆕 NEW FILES DETECTED\n\n")
                f.write(f"Found {len(self.new_files)} new files:\n\n")

                # Group by directory
                files_by_dir = {}
                for file in self.new_files[:50]:  # Limit to 50 for readability
                    dir_name = str(Path(file).parent)
                    files_by_dir.setdefault(dir_name, []).append(Path(file).name)

                for directory, files in sorted(files_by_dir.items()):
                    f.write(f"### `{directory}/`\n")
                    for file in sorted(files):
                        f.write(f"- `{file}`\n")
                    f.write("\n")

                f.write("**Action Required:** Review these files and categorize into features.\n\n")
                f.write("---\n\n")

            # Code Changes by Marker
            f.write("## 🔍 CODE CHANGE MARKERS\n\n")

            for marker_type in ["NEW", "ADDED", "FIXED", "UPDATED"]:
                changes = self.code_changes.get(marker_type, [])
                if changes:
                    icon = {"NEW": "🆕", "ADDED": "➕", "FIXED": "🐛", "UPDATED": "📈"}.get(marker_type, "•")
                    f.write(f"### {icon} {marker_type} ({len(changes)} instances)\n\n")

                    # Group by file
                    changes_by_file = {}
                    for file_path, line_num, description in changes[:30]:  # Limit to 30
                        changes_by_file.setdefault(file_path, []).append((line_num, description))

                    for file_path, file_changes in sorted(changes_by_file.items()):
                        f.write(f"**{file_path}:**\n")
                        for line_num, description in file_changes[:5]:  # Limit to 5 per file
                            f.write(f"- Line {line_num}: {description}\n")
                        if len(file_changes) > 5:
                            f.write(f"- ... and {len(file_changes) - 5} more\n")
                        f.write("\n")

                    if len(changes) > 30:
                        f.write(f"*... and {len(changes) - 30} more instances*\n\n")

            f.write("**Action Required:** Review these markers and expand into feature descriptions.\n\n")
            f.write("---\n\n")

            # Modified Files
            if self.modified_files:
                f.write("## 📝 MODIFIED FILES\n\n")
                f.write(f"Found {len(self.modified_files)} modified files:\n\n")

                # Sort by similarity (lowest first = most changed)
                sorted_files = sorted(self.modified_files, key=lambda x: x[2])

                f.write("| File | Product | Similarity | Change Magnitude |\n")
                f.write("|------|---------|------------|------------------|\n")

                for file, product, similarity in sorted_files[:50]:
                    if similarity < 50:
                        magnitude = "🔴 Major"
                    elif similarity < 80:
                        magnitude = "🟡 Moderate"
                    else:
                        magnitude = "🟢 Minor"

                    f.write(f"| `{Path(file).name}` | {product} | {similarity:.1f}% | {magnitude} |\n")

                if len(self.modified_files) > 50:
                    f.write(f"\n*... and {len(self.modified_files) - 50} more files*\n")

                f.write("\n**Action Required:** Review major changes and document.\n\n")
                f.write("---\n\n")

            # Documentation Updates
            new_docs = self.find_new_markdown_docs()
            if new_docs:
                f.write("## 📚 DOCUMENTATION UPDATES\n\n")
                f.write(f"Found {len(new_docs)} new or updated documentation files:\n\n")

                for doc_path, mod_time in new_docs[:20]:
                    f.write(f"- `{doc_path}` (Modified: {mod_time.strftime('%b %d, %Y')})\n")

                if len(new_docs) > 20:
                    f.write(f"\n*... and {len(new_docs) - 20} more files*\n")

                f.write("\n**Action Required:** Review and list in documentation section.\n\n")
                f.write("---\n\n")

            # Deployment Reports Summary
            if self.deployment_reports:
                f.write("## 📦 DEPLOYMENT REPORTS SUMMARY\n\n")

                # Group by date
                reports_by_date = {}
                for report in self.deployment_reports:
                    date_key = report['date'].strftime('%Y-%m-%d')
                    reports_by_date.setdefault(date_key, []).append(report)

                for date_key in sorted(reports_by_date.keys(), reverse=True):
                    reports = reports_by_date[date_key]
                    f.write(f"### {date_key}\n\n")

                    # Group by product
                    by_product = {}
                    for report in reports:
                        product = report['product']
                        by_product.setdefault(product, []).append(report)

                    for product, prod_reports in by_product.items():
                        f.write(f"**{product}:** {len(prod_reports)} files deployed\n")

                    f.write("\n")

                f.write("**Action Required:** Review deployment reports for context.\n\n")
                f.write("---\n\n")

            # Template Sections
            f.write("## 🆕 NEW FEATURES (TODO)\n\n")
            f.write("[Fill in based on analysis above]\n\n")
            f.write("---\n\n")

            f.write("## 🐛 BUG FIXES (TODO)\n\n")
            f.write("[Fill in based on FIXED markers above]\n\n")
            f.write("---\n\n")

            f.write("## 📈 IMPROVEMENTS (TODO)\n\n")
            f.write("[Fill in based on analysis]\n\n")
            f.write("---\n\n")

            f.write("## 🚀 UPGRADE INSTRUCTIONS (TODO)\n\n")
            f.write("[Standard upgrade instructions]\n\n")
            f.write("---\n\n")

            # Footer
            f.write("## 📝 NEXT STEPS\n\n")
            f.write("1. Review all TODO sections\n")
            f.write("2. Categorize new files into features\n")
            f.write("3. Expand code markers into descriptions\n")
            f.write("4. Verify all file paths and references\n")
            f.write("5. Write feature descriptions with user benefits\n")
            f.write("6. Create email draft from this document\n")
            f.write("7. Review with team before release\n\n")

            f.write("---\n\n")
            f.write(f"**Generated by:** `generate_release_notes.py`\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%B %d, %Y %H:%M:%S')}\n")

        print(f"✅ Release notes draft saved to: {output_path}")
        print(f"\n📋 Summary:")
        print(f"   - New files: {len(self.new_files)}")
        print(f"   - Modified files: {len(self.modified_files)}")
        print(f"   - Code markers: {sum(len(v) for v in self.code_changes.values())}")
        print(f"   - Documentation updates: {len(new_docs)}")
        print(f"   - Deployment reports: {len(self.deployment_reports)}")

        return output_path

    def generate_html_from_markdown(self, md_file: Path) -> Path:
        """Generate HTML from markdown using the markdown converter."""
        print(f"\n🌐 Generating HTML version...")

        # Path to markdown converter
        converter_path = self.workspace_path / "OtherFiles" / "MarkdownConverter" / "md_converter.py"

        if not converter_path.exists():
            print(f"   ⚠️  Markdown converter not found at {converter_path}")
            print("   Skipping HTML generation")
            return None

        # Output HTML path
        html_file = md_file.with_suffix('.html')

        # Run converter
        import subprocess
        try:
            result = subprocess.run(
                ['python', str(converter_path), str(md_file), '-f', 'html', '-o', str(html_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✅ HTML version saved to: {html_file}")
                return html_file
            else:
                print(f"   ⚠️  HTML generation failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  HTML generation timed out")
            return None
        except Exception as e:
            print(f"   ⚠️  HTML generation error: {e}")
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Debug Framework release notes from deployment data and code markers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate notes for changes since Jan 22
  python generate_release_notes.py --start-date 2026-01-22

  # Specify version and date range
  python generate_release_notes.py --version 1.7.1 --start-date 2026-01-22 --end-date 2026-02-18

  # Custom output file
  python generate_release_notes.py --start-date 2026-01-22 --output my_draft.md

  # Generate with HTML version
  python generate_release_notes.py --start-date 2026-01-22 --html
        """
    )

    parser.add_argument(
        '--start-date',
        required=True,
        help='Start date in YYYY-MM-DD format (e.g., 2026-01-22)'
    )

    parser.add_argument(
        '--end-date',
        help='End date in YYYY-MM-DD format (default: today)'
    )

    parser.add_argument(
        '--version',
        default='X.X.X',
        help='Release version number (e.g., 1.7.1)'
    )

    parser.add_argument(
        '--output',
        help='Output filename (default: DRAFT_RELEASE_v{VERSION}_{MONTH}{YEAR}.md)'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Also generate HTML version using markdown converter'
    )

    args = parser.parse_args()

    # Create generator
    print("=" * 80)
    print("Debug Framework Release Notes Generator")
    print("=" * 80)
    print()

    try:
        generator = ReleaseNotesGenerator(
            start_date=args.start_date,
            end_date=args.end_date,
            version=args.version
        )

        # Collect data
        generator.parse_deployment_reports()
        generator.search_code_markers()

        # Generate output
        output_path = generator.generate_markdown_output(args.output)

        # Generate HTML if requested
        if args.html:
            html_path = generator.generate_html_from_markdown(output_path)

        print()
        print("=" * 80)
        print("✨ Generation complete!")
        print("=" * 80)
        print()
        print(f"Next: Review and edit {output_path}")
        if args.html and html_path:
            print(f"HTML: {html_path}")
        print("Then: Use RELEASE_TEMPLATE.md to create final release notes")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
