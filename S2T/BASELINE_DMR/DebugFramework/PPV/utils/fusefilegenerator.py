"""
Fuse File Generator for PPV Engineering Tools

This module processes raw CSV fuse files from product-specific folders and provides
functionality to parse, filter, search, and generate .fuse files compatible with
the fusefilegen.py tool.

Features:
- Parse CSV files from configs/fuses/<product>/ folder
- Combine multiple CSV files (compute.csv, io.csv, cbb.csv, imh.csv, etc.)
- Add IP origin tracking (IO, Compute, CBB, IMH) based on filename
- Provide searchable/filterable data interface
- Generate .fuse files with product-specific hierarchy patterns
- Support for GNR, CWF, and DMR products

Author: Engineering Tools Team
Date: February 2026
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import re
import sys

# Increase CSV field size limit to handle large fields in DMR fuses
csv.field_size_limit(sys.maxsize)


class FuseFileGenerator:
    """
    Main class for processing and generating fuse files from CSV data.

    Supports multiple products (GNR, CWF, DMR) with product-specific hierarchy patterns.
    """

    # Product-specific hierarchy patterns
    PRODUCT_HIERARCHIES = {
        'GNR': {
            'compute': 'sv.socket{socket}.compute{compute}.fuses',
            'io': 'sv.socket{socket}.io{io}.fuses',
            'computes': 'sv.sockets.computes.fuses',  # Plural for all
            'ios': 'sv.sockets.ios.fuses'  # Plural for all
        },
        'CWF': {
            'compute': 'sv.socket{socket}.compute{compute}.fuses',
            'io': 'sv.socket{socket}.io{io}.fuses',
            'computes': 'sv.sockets.computes.fuses',
            'ios': 'sv.sockets.ios.fuses'
        },
        'DMR': {
            'cbb_base': 'sv.socket{socket}.cbb{cbb}.base.fuses',
            'cbb_top': 'sv.socket{socket}.cbb{cbb}.compute{compute}.fuses',
            'imh': 'sv.socket{socket}.imh{imh}.fuses',
            'cbbs_base': 'sv.sockets.cbbs.base.fuses',  # Plural for all
            'cbbs_top': 'sv.sockets.cbbs.computes.fuses',  # Plural for all
            'imhs': 'sv.sockets.imhs.fuses'  # Plural for all
        }
    }

    def __init__(self, product: str = 'GNR'):
        """
        Initialize the FuseFileGenerator.

        Args:
            product: Product name (GNR, CWF, or DMR)
        """
        self.product = product.upper()
        self.fuse_data: List[Dict] = []
        self.csv_files_loaded: List[str] = []
        self.available_columns: Set[str] = set()

        if self.product not in self.PRODUCT_HIERARCHIES:
            raise ValueError(f"Unsupported product: {self.product}. Supported: GNR, CWF, DMR")

    def load_csv_files(self, folder_path: str) -> bool:
        """
        Load all CSV files from the specified product folder.
        Each CSV file represents an IP (compute, io, cbb, imh, etc.)

        Args:
            folder_path: Path to the fuses folder (e.g., configs/fuses/gnr/)

        Returns:
            True if successful, False otherwise
        """
        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            print(f"Error: Folder not found: {folder_path}")
            return False

        csv_files = list(folder.glob('*.csv'))

        if not csv_files:
            print(f"Error: No CSV files found in {folder_path}")
            return False

        self.fuse_data = []
        self.csv_files_loaded = []
        self.available_columns = set()

        for csv_file in csv_files:
            ip_name = csv_file.stem  # Get filename without extension (e.g., 'compute', 'io')

            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)

                    # Store column names
                    if reader.fieldnames:
                        self.available_columns.update(reader.fieldnames)

                    # Read all rows and add IP origin
                    for row in reader:
                        row['IP_Origin'] = ip_name.upper()  # Add IP origin column
                        self.fuse_data.append(row)

                self.csv_files_loaded.append(csv_file.name)
                print(f"Loaded: {csv_file.name} ({len(list(csv_file.open()))-1} fuses)")

            except Exception as e:
                print(f"Error loading {csv_file.name}: {e}")
                return False

        # Add IP_Origin to available columns
        self.available_columns.add('IP_Origin')

        print(f"\nTotal fuses loaded: {len(self.fuse_data)}")
        print(f"Files loaded: {', '.join(self.csv_files_loaded)}")
        print(f"Available columns: {len(self.available_columns)}")

        return True

    def get_available_columns(self) -> List[str]:
        """Get list of available columns from loaded data."""
        return sorted(list(self.available_columns))

    def search_fuses(self, search_term: str, search_columns: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for fuses matching the search term in specified columns.

        Args:
            search_term: Term to search for (case-insensitive)
            search_columns: List of column names to search in. If None, searches in key columns.

        Returns:
            List of matching fuse records
        """
        if not self.fuse_data:
            return []

        # Default search columns if not specified
        if search_columns is None:
            search_columns = ['original_name', 'Instance', 'description', 'VF_Name']

        search_term_lower = search_term.lower()
        results = []

        for fuse in self.fuse_data:
            for col in search_columns:
                if col in fuse and fuse[col]:
                    if search_term_lower in str(fuse[col]).lower():
                        results.append(fuse)
                        break  # Found match, move to next fuse

        return results

    def filter_fuses(self, filters: Dict[str, str]) -> List[Dict]:
        """
        Filter fuses based on column values.

        Args:
            filters: Dictionary of {column_name: filter_value}
                    Filter value supports:
                    - Exact match: "value"
                    - Contains: "*value*"
                    - Starts with: "value*"
                    - Ends with: "*value"

        Returns:
            List of filtered fuse records
        """
        if not self.fuse_data:
            return []

        results = self.fuse_data.copy()

        for col, filter_val in filters.items():
            if not filter_val or filter_val == '*':  # Skip empty or wildcard-only filters
                continue

            filter_val_lower = filter_val.lower()
            filtered = []

            for fuse in results:
                if col not in fuse:
                    continue

                cell_value = str(fuse[col]).lower()

                # Handle wildcard matching
                if filter_val.startswith('*') and filter_val.endswith('*'):
                    # Contains
                    match_term = filter_val_lower[1:-1]
                    if match_term in cell_value:
                        filtered.append(fuse)
                elif filter_val.startswith('*'):
                    # Ends with
                    match_term = filter_val_lower[1:]
                    if cell_value.endswith(match_term):
                        filtered.append(fuse)
                elif filter_val.endswith('*'):
                    # Starts with
                    match_term = filter_val_lower[:-1]
                    if cell_value.startswith(match_term):
                        filtered.append(fuse)
                else:
                    # Exact match
                    if cell_value == filter_val_lower:
                        filtered.append(fuse)

            results = filtered

        return results

    def get_column_unique_values(self, column_name: str, max_values: int = 100) -> List[str]:
        """
        Get unique values for a column (useful for filter dropdowns).

        Args:
            column_name: Column to get values from
            max_values: Maximum number of unique values to return

        Returns:
            List of unique values (sorted)
        """
        if not self.fuse_data or column_name not in self.available_columns:
            return []

        unique_values = set()
        for fuse in self.fuse_data:
            if column_name in fuse and fuse[column_name]:
                unique_values.add(str(fuse[column_name]))

        values = sorted(list(unique_values))
        return values[:max_values]

    def generate_fuse_file(self,
                          selected_fuses: List[Dict],
                          ip_assignments: Dict[str, Dict[str, str]],
                          output_file: str) -> bool:
        """
        Generate a .fuse file from selected fuses with IP assignments.

        Args:
            selected_fuses: List of fuse records to include
            ip_assignments: Dictionary mapping IP instances to fuse values
                           Format: {
                               'compute0': {'fuse_name': '0x1', ...},
                               'io0': {'fuse_name': '0x2', ...}
                           }
            output_file: Path to output .fuse file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write(f"# Fuse configuration file for {self.product}\n")
                f.write(f"# Generated by PPV Engineering Tools - Fuse File Generator\n")
                f.write(f"# Total fuses: {len(selected_fuses)}\n")
                f.write(f"#\n")
                f.write(f"# This file is compatible with fusefilegen.py\n\n")

                # Group by IP assignments
                for ip_instance, fuse_values in ip_assignments.items():
                    if not fuse_values:
                        continue

                    # Determine the section header based on product and IP
                    # Convert instance to lowercase for consistency
                    section_header = self._get_section_header(ip_instance.lower())

                    if section_header:
                        f.write(f"[{section_header}]\n")

                        # Write fuse assignments
                        for fuse_name, value in fuse_values.items():
                            f.write(f"{fuse_name} = {value}\n")

                        f.write("\n")  # Blank line between sections

            print(f"Successfully generated fuse file: {output_file}")
            return True

        except Exception as e:
            print(f"Error generating fuse file: {e}")
            return False

    def _get_section_header(self, ip_instance: str) -> Optional[str]:
        """
        Get the proper section header for a given IP instance.

        Args:
            ip_instance: IP instance identifier (e.g., 'compute0', 'io1', 'all_computes')

        Returns:
            Section header string or None if invalid
        """
        hierarchies = self.PRODUCT_HIERARCHIES[self.product]

        # Handle plural/all instances
        if ip_instance in ['all_computes', 'computes']:
            return hierarchies.get('computes')
        elif ip_instance in ['all_ios', 'ios']:
            return hierarchies.get('ios')
        elif ip_instance in ['all_cbbs_base', 'cbbs_base']:
            return hierarchies.get('cbbs_base')
        elif ip_instance in ['all_cbbs_top', 'cbbs_top']:
            return hierarchies.get('cbbs_top')
        elif ip_instance in ['all_imhs', 'imhs']:
            return hierarchies.get('imhs')

        # Parse individual instances (e.g., compute0, io1, cbb2, etc.)
        # Format: <ip_type><number> or <ip_type><number>_<subtype><number>

        # For DMR CBB with compute (e.g., cbb0_compute1)
        cbb_compute_match = re.match(r'cbb(\d+)_compute(\d+)', ip_instance)
        if cbb_compute_match and self.product == 'DMR':
            cbb_num = cbb_compute_match.group(1)
            compute_num = cbb_compute_match.group(2)
            return hierarchies['cbb_top'].format(socket=0, cbb=cbb_num, compute=compute_num)

        # Standard single IP instance
        compute_match = re.match(r'compute(\d+)', ip_instance)
        if compute_match:
            num = compute_match.group(1)
            return hierarchies.get('compute', '').format(socket=0, compute=num)

        io_match = re.match(r'io(\d+)', ip_instance)
        if io_match:
            num = io_match.group(1)
            return hierarchies.get('io', '').format(socket=0, io=num)

        cbb_match = re.match(r'cbb(\d+)', ip_instance)
        if cbb_match and self.product == 'DMR':
            num = cbb_match.group(1)
            return hierarchies.get('cbb_base', '').format(socket=0, cbb=num)

        imh_match = re.match(r'imh(\d+)', ip_instance)
        if imh_match and self.product == 'DMR':
            num = imh_match.group(1)
            return hierarchies.get('imh', '').format(socket=0, imh=num)

        return None

    def export_to_csv(self, fuses: List[Dict], output_file: str, columns: Optional[List[str]] = None) -> bool:
        """
        Export selected fuses to a CSV file.

        Args:
            fuses: List of fuse records to export
            output_file: Path to output CSV file
            columns: List of columns to include (None = all columns)

        Returns:
            True if successful, False otherwise
        """
        if not fuses:
            print("No fuses to export")
            return False

        try:
            # Determine columns to export
            if columns is None:
                columns = sorted(list(fuses[0].keys()))

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(fuses)

            print(f"Successfully exported {len(fuses)} fuses to: {output_file}")
            return True

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False

    def get_statistics(self) -> Dict:
        """
        Get statistics about loaded fuse data.

        Returns:
            Dictionary containing various statistics
        """
        if not self.fuse_data:
            return {}

        stats = {
            'total_fuses': len(self.fuse_data),
            'files_loaded': len(self.csv_files_loaded),
            'columns_available': len(self.available_columns),
            'ip_origins': {},
            'product': self.product
        }

        # Count fuses by IP origin
        for fuse in self.fuse_data:
            ip = fuse.get('IP_Origin', 'Unknown')
            stats['ip_origins'][ip] = stats['ip_origins'].get(ip, 0) + 1

        return stats


# Utility functions for external use

def load_product_fuses(product: str, base_path: Optional[str] = None) -> Optional[FuseFileGenerator]:
    """
    Convenience function to load fuses for a product.

    Args:
        product: Product name (GNR, CWF, DMR)
        base_path: Base path to configs folder (auto-detected if None)

    Returns:
        FuseFileGenerator instance or None if failed
    """
    try:
        generator = FuseFileGenerator(product)

        # Auto-detect base path if not provided
        if base_path is None:
            # Assume we're in PPV/utils or similar
            current_dir = Path(__file__).parent
            base_path = current_dir.parent / 'configs' / 'fuses' / product.lower()
        else:
            base_path = Path(base_path) / product.lower()

        if generator.load_csv_files(str(base_path)):
            return generator

    except Exception as e:
        print(f"Error loading fuses for {product}: {e}")

    return None


def validate_fuse_value(value: str, fuse_width: Optional[int] = None, numbits: Optional[int] = None) -> bool:
    """
    Validate that a fuse value is in proper format and fits within the specified bit width.

    Args:
        value: Fuse value string (e.g., '0x1', '0xFF', '255', '0b1111')
        fuse_width: Expected bit width of the fuse (optional)
        numbits: Number of bits for the fuse (optional, same as fuse_width typically)

    Returns:
        True if valid value and fits within bit width, False otherwise
    """
    if not value:
        return False

    value = value.strip()
    
    try:
        # Parse the value based on format
        if value.startswith('0x') or value.startswith('0X'):
            # Hexadecimal format
            hex_part = value[2:]
            if not hex_part:
                return False
            int_value = int(hex_part, 16)
        elif value.startswith('0b') or value.startswith('0B'):
            # Binary format
            bin_part = value[2:]
            if not bin_part:
                return False
            int_value = int(bin_part, 2)
        else:
            # Decimal format
            int_value = int(value, 10)
        
        # Check if value is non-negative
        if int_value < 0:
            return False
        
        # Check against bit width if provided
        bit_width = fuse_width or numbits
        if bit_width is not None:
            try:
                max_value = (2 ** int(bit_width)) - 1
                if int_value > max_value:
                    return False
            except (ValueError, TypeError):
                # If bit_width can't be converted to int, skip width check
                pass
        
        return True
    except (ValueError, TypeError):
        return False


if __name__ == "__main__":
    # Example usage
    print("=== PPV Fuse File Generator - Test ===\n")

    # Test with GNR product
    generator = load_product_fuses('GNR')

    if generator:
        print("\n=== Statistics ===")
        stats = generator.get_statistics()
        print(f"Product: {stats['product']}")
        print(f"Total fuses: {stats['total_fuses']}")
        print(f"Files loaded: {stats['files_loaded']}")
        print(f"IP Origins:")
        for ip, count in stats['ip_origins'].items():
            print(f"  {ip}: {count} fuses")

        print("\n=== Available Columns ===")
        columns = generator.get_available_columns()
        print(f"Total columns: {len(columns)}")
        print(f"Sample columns: {columns[:10]}")

        print("\n=== Search Test ===")
        results = generator.search_fuses('bgr', ['description', 'original_name'])
        print(f"Found {len(results)} fuses matching 'bgr'")
        if results:
            print(f"First result: {results[0].get('original_name', 'N/A')}")

        print("\nTest completed successfully!")
    else:
        print("Failed to load fuses")
