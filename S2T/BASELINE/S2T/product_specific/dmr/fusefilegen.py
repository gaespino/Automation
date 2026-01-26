"""
Fuse File Generator for DMR Product

This tool parses user-created fuse configuration files in a simple INI-like format
and generates an array of fully-qualified register paths for use with CoreManipulation.

DMR Hierarchy:
- sv.socket<N>.cbb<N>.base.fuses
- sv.socket<N>.cbb<N>.compute<N>.fuses (compute = top)
- sv.socket<N>.imh<N>.fuses
- sv.sockets.cbbs.base.fuses (all sockets, all cbbs, base)
- sv.sockets.cbbs.computes.fuses (all sockets, all cbbs, all computes)
- sv.sockets.imhs.fuses (all sockets, all imhs)

Example input file:
    [sv.socket0.cbb0.base.fuses]
    register1 = 0x1
    register2 = 0x2
    sv.socket0.cbb0.base.fuses.register3 = 0xFF

    [sv.sockets.cbbs.base.fuses]
    register1 = 0x1
    sv.sockets.cbbs.base.fuses.register2 = 0xDEADBEEF

Usage:
    from S2T.product_specific.dmr.fusefilegen import process_fuse_file

    registers = process_fuse_file('path/to/fuses.fuse')
    # Returns: ['sv.socket0.cbb0.base.fuses.register1=0x1', ...]
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Union


class FuseFileParser:
    """Parser for DMR fuse configuration files"""

    # Valid section patterns for DMR
    # Accepts: socket/sockets/socket#, cbb/cbbs/cbb#, imh/imhs/imh#, compute/computes/compute#
    VALID_SECTION_PATTERNS = [
        r'^sv\.socket(s|\d+)\.cbb(s|\d+)\.base\.fuses$',
        r'^sv\.socket(s|\d+)\.cbb(s|\d+)\.compute(s|\d+)\.fuses$',
        r'^sv\.socket(s|\d+)\.imh(s|\d+)\.fuses$',
    ]

    def __init__(self):
        self.config: Dict[str, Dict[str, str]] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_section(self, section: str) -> bool:
        """Validate that a section matches DMR hierarchy patterns"""
        for pattern in self.VALID_SECTION_PATTERNS:
            if re.match(pattern, section):
                return True
        return False

    def parse_file(self, filepath: Path) -> bool:
        """Parse the configuration file and validate structure"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                current_section = None
                line_num = 0

                for line in f:
                    line_num += 1
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Section header
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1].strip()
                        if current_section not in self.config:
                            self.config[current_section] = {}
                        continue

                    # Key-value pair
                    if '=' in line:
                        if current_section is None:
                            self.errors.append(f"Line {line_num}: Key-value pair outside of section")
                            continue

                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        self.config[current_section][key] = value
                    else:
                        self.errors.append(f"Line {line_num}: Invalid syntax: {line}")

        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False

        # Validate sections
        for section in self.config.keys():
            if not self.validate_section(section):
                self.errors.append(
                    f"Invalid section '{section}'. Must match DMR hierarchy: "
                    f"sv.socket(s|#).cbb(s|#).base.fuses, "
                    f"sv.socket(s|#).cbb(s|#).compute(s|#).fuses, "
                    f"sv.socket(s|#).imh(s|#).fuses "
                    f"(where # is a number, 's' means plural for all units)"
                )

        return len(self.errors) == 0

    def generate_register_list(self) -> List[str]:
        """Generate the list of fully-qualified register assignments"""
        registers: List[str] = []
        seen: Set[str] = set()

        for section, values in self.config.items():
            for key, value in values.items():
                # Check if the key already contains the full path
                if key.startswith('sv.'):
                    # Already fully qualified
                    full_path = f"{key}={value}"
                else:
                    # Need to prepend the section
                    full_path = f"{section}.{key}={value}"

                # Avoid duplicates
                if full_path not in seen:
                    registers.append(full_path)
                    seen.add(full_path)

        return registers

    def get_report(self) -> Dict:
        """Get a report of the parsing results"""
        register_count = sum(len(v) for v in self.config.values())
        return {
            'sections': list(self.config.keys()),
            'register_count': register_count,
            'errors': self.errors,
            'warnings': self.warnings
        }


def process_fuse_file(filepath: Union[str, Path]) -> List[str]:
    """
    Process a fuse configuration file and return the list of register assignments.

    Args:
        filepath: Path to the fuse configuration file

    Returns:
        List of register assignments in format: ['sv.socket0.cbb0.base.fuses.register=0x1', ...]

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file has validation errors
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Fuse file not found: {filepath}")

    parser = FuseFileParser()

    if not parser.parse_file(filepath):
        error_msg = "\n".join(parser.errors)
        raise ValueError(f"Failed to parse fuse file:\n{error_msg}")

    return parser.generate_register_list()
