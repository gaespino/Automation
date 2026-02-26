"""
THR Service — MCA Decoder, Loop Parser, Fuse Generator
========================================================
Pure Python logic, no tkinter, no xlwings.
Compatible with GNR, CWF, and DMR products.
"""
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── MCA Service ───────────────────────────────────────────────────────────────

class MCAService:
    """Decode MCA register values for CHA, LLC, CORE, MEMORY, IO, FIRST_ERROR."""

    # Bit-field definitions per register type (simplified, product-agnostic)
    _FIELDS: Dict[str, List[Dict]] = {
        "CORE": [
            {"name": "MCACOD",       "bits": [0, 15],  "desc": "MCA Error Code"},
            {"name": "MSCOD",        "bits": [16, 31], "desc": "Model-Specific Error Code"},
            {"name": "OTHER_INFO",   "bits": [32, 36], "desc": "Other Information"},
            {"name": "CORRECTED_ERR","bits": [37, 37], "desc": "Corrected Error Count"},
            {"name": "THRESHOLD",    "bits": [38, 52], "desc": "Error Threshold"},
            {"name": "PCC",          "bits": [57, 57], "desc": "Processor Context Corrupted"},
            {"name": "ADDRV",        "bits": [58, 58], "desc": "MCi_ADDR register valid"},
            {"name": "MISCV",        "bits": [59, 59], "desc": "MCi_MISC register valid"},
            {"name": "EN",           "bits": [60, 60], "desc": "Error Enabled"},
            {"name": "UC",           "bits": [61, 61], "desc": "Uncorrected Error"},
            {"name": "OVER",         "bits": [62, 62], "desc": "Error Overflow"},
            {"name": "VAL",          "bits": [63, 63], "desc": "MCi_STATUS register valid"},
        ],
        "CHA": [
            {"name": "MCACOD",  "bits": [0, 15],  "desc": "MCA Error Code"},
            {"name": "MSCOD",   "bits": [16, 31], "desc": "Model-Specific Error Code"},
            {"name": "CORRECTED","bits": [52, 56], "desc": "Corrected Error Count"},
            {"name": "UC",      "bits": [61, 61], "desc": "Uncorrected"},
            {"name": "VAL",     "bits": [63, 63], "desc": "Valid"},
        ],
        "LLC": [
            {"name": "MCACOD",  "bits": [0, 15],  "desc": "MCA Error Code"},
            {"name": "MSCOD",   "bits": [16, 31], "desc": "LLC MSCOD"},
            {"name": "UC",      "bits": [61, 61], "desc": "Uncorrected"},
            {"name": "VAL",     "bits": [63, 63], "desc": "Valid"},
        ],
        "MEMORY": [
            {"name": "MCACOD",  "bits": [0, 15],  "desc": "MCA Error Code"},
            {"name": "MSCOD",   "bits": [16, 31], "desc": "Memory MSCOD"},
            {"name": "RANKS",   "bits": [46, 47], "desc": "Failed Rank Indicator"},
            {"name": "UC",      "bits": [61, 61], "desc": "Uncorrected"},
            {"name": "VAL",     "bits": [63, 63], "desc": "Valid"},
        ],
        "IO": [
            {"name": "MCACOD",  "bits": [0, 15],  "desc": "MCA Error Code"},
            {"name": "MSCOD",   "bits": [16, 31], "desc": "IO MSCOD"},
            {"name": "UC",      "bits": [61, 61], "desc": "Uncorrected"},
            {"name": "VAL",     "bits": [63, 63], "desc": "Valid"},
        ],
        "FIRST_ERROR": [
            {"name": "MCACOD",  "bits": [0, 15],  "desc": "First Error Code"},
            {"name": "MSCOD",   "bits": [16, 31], "desc": "First Error MSCOD"},
            {"name": "VAL",     "bits": [63, 63], "desc": "Valid"},
        ],
    }

    @classmethod
    def decode(cls, register: str, reg_type: str, product: str = "GNR") -> Dict:
        """Decode an MCA register hex value into its bit fields."""
        reg_type = reg_type.upper()
        if reg_type not in cls._FIELDS:
            reg_type = "CORE"

        # Parse hex value
        try:
            val = int(register.strip(), 16) if register.strip().startswith("0x") else int(register.strip(), 16)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid register value: {register!r}")

        decoded = []
        for field in cls._FIELDS[reg_type]:
            lo, hi = field["bits"]
            mask = ((1 << (hi - lo + 1)) - 1) << lo
            field_val = (val & mask) >> lo
            decoded.append({
                "name": field["name"],
                "value": field_val,
                "hex": f"0x{field_val:X}",
                "bits": f"[{hi}:{lo}]",
                "desc": field["desc"],
            })

        return {
            "input": register,
            "type": reg_type,
            "product": product,
            "raw": f"0x{val:016X}",
            "fields": decoded,
            "valid": bool((val >> 63) & 1),
            "uncorrected": bool((val >> 61) & 1),
        }


# ── Loop Parser Service ───────────────────────────────────────────────────────

class LoopParserService:
    """Parse PTC loop log files and extract pass/fail data."""

    # Regex patterns
    _LOOP_START  = re.compile(r"Loop\s+(\d+)\s+Start", re.IGNORECASE)
    _LOOP_RESULT = re.compile(r"Loop\s+(\d+)\s+(PASS|FAIL)", re.IGNORECASE)
    _TEST_RESULT = re.compile(r"Test\s+(\S+)\s+(PASS|FAIL)", re.IGNORECASE)
    _MCA_ENTRY   = re.compile(r"MCA.*?Bank\s*(\d+).*?0x([0-9A-Fa-f]{16})", re.IGNORECASE)

    @classmethod
    def parse(cls, content: str, product: str = "GNR") -> Dict:
        """Parse loop log text content."""
        lines = content.splitlines()
        loops: List[Dict] = []
        mcas: List[Dict] = []
        total = 0
        passed = 0
        failed = 0

        for line in lines:
            m = cls._LOOP_RESULT.search(line)
            if m:
                total += 1
                num = int(m.group(1))
                result = m.group(2).upper()
                if result == "PASS":
                    passed += 1
                else:
                    failed += 1
                loops.append({"loop": num, "result": result})
                continue

            m = cls._MCA_ENTRY.search(line)
            if m:
                mcas.append({"bank": m.group(1), "value": f"0x{m.group(2)}"})

        return {
            "product": product,
            "total_loops": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed / total * 100):.1f}%" if total else "N/A",
            "loops": loops,
            "mcas": mcas,
        }


# ── Fuse Service ──────────────────────────────────────────────────────────────

class FuseService:
    """Parse fuse CSV data and generate fuse configuration files."""

    @classmethod
    def parse(cls, content: str, product: str = "GNR", ip_filter: str = "") -> Dict:
        """Parse CSV fuse content and return structured fuse data."""
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        if not lines:
            return {"product": product, "fuses": [], "count": 0}

        # Detect header
        header = []
        data_lines = lines
        if lines[0].lower().startswith("name") or "," in lines[0]:
            header = [h.strip() for h in lines[0].split(",")]
            data_lines = lines[1:]

        fuses = []
        for line in data_lines:
            parts = [p.strip() for p in line.split(",")]
            if header:
                entry = dict(zip(header, parts))
            else:
                entry = {"name": parts[0] if parts else "", "value": parts[1] if len(parts) > 1 else ""}

            # Apply IP filter
            if ip_filter and ip_filter.lower() not in entry.get("name", "").lower():
                continue
            fuses.append(entry)

        return {
            "product": product,
            "ip_filter": ip_filter,
            "fuses": fuses,
            "count": len(fuses),
        }
