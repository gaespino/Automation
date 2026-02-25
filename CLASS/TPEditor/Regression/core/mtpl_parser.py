"""
mtpl_parser.py
--------------
Parse Test / MultiTrialTest instances from .mtpl files and compare them.
"""

import re
import os
from typing import Dict, List, Optional, Tuple


def parse_all_instances(mtpl_filepath: str) -> Dict[str, dict]:
    """
    Parse every Test and MultiTrialTest block in an MTPL file.

    Returns:
        {
            instance_name: {
                "type":       "Test" | "MultiTrialTest",
                "raw_block":  str,          # full text of the block
                "key_values": {key: value}  # all key=value; pairs found
            }
        }
    """
    if not os.path.isfile(mtpl_filepath):
        return {}

    with open(mtpl_filepath, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    instances = {}
    in_block = False
    current_name = ""
    current_type = ""
    block_lines: List[str] = []
    brace_depth = 0

    for line in lines:
        stripped = line.strip()

        if not in_block:
            # "Test ClassName InstanceName { ..."
            m_test = re.match(r'^Test\s+\S+\s+(\S+)', stripped)
            # "MultiTrialTest InstanceName { ..."
            m_mtt = re.match(r'^MultiTrialTest\s+(\S+)', stripped)

            if m_test or m_mtt:
                if m_test:
                    current_type = "Test"
                    current_name = m_test.group(1)
                else:
                    current_type = "MultiTrialTest"
                    current_name = m_mtt.group(1)
                in_block = True
                block_lines = [line]
                brace_depth = stripped.count("{") - stripped.count("}")
                continue
        else:
            block_lines.append(line)
            brace_depth += stripped.count("{") - stripped.count("}")

            if brace_depth <= 0:
                # End of block
                raw = "".join(block_lines)
                instances[current_name] = {
                    "type": current_type,
                    "raw_block": raw,
                    "key_values": _extract_key_values(raw),
                }
                in_block = False
                block_lines = []
                brace_depth = 0

    return instances


def _extract_key_values(block_text: str) -> Dict[str, str]:
    """
    Extract all key = value; pairs from a block.
    Comment lines (starting with #) are skipped.
    """
    kv = {}
    for line in block_text.splitlines():
        stripped = line.strip()
        # Skip commented-out lines
        if stripped.startswith("#"):
            continue
        if "=" in stripped:
            left, _, right = stripped.partition("=")
            key = left.strip()
            # Remove trailing semicolon and surrounding whitespace/quotes
            value = right.strip().rstrip(";").strip()
            if key and " " not in key:  # simple key names only
                kv[key] = value
    return kv


def resolve_instances(cfg: dict, parsed: Dict[str, dict]) -> List[str]:
    """
    Build the final list of instance names to compare from config.

    Exact names come from cfg["mtpl_instances"].
    Pattern names (with {X}) are auto-expanded: for each pattern, find all
    names in `parsed` that match the pattern with {X} replaced by \\d* (0 or more digits).

    Returns a deduplicated ordered list.
    """
    result = list(cfg.get("mtpl_instances", []))
    seen = set(result)

    for pattern in cfg.get("mtpl_instance_patterns", []):
        # {X} → zero or more digits
        regex_str = re.escape(pattern).replace(r"\{X\}", r"\d*") + "$"
        regex = re.compile(regex_str, re.IGNORECASE)
        for name in sorted(parsed.keys()):
            if regex.match(name) and name not in seen:
                result.append(name)
                seen.add(name)

    return result


def compare_instances(
    ref_mtpl: str,
    new_mtpl: str,
    cfg: dict,
) -> Dict:
    """
    Parse both MTPL files, resolve instance names from config, and produce
    a per-instance comparison.

    Returns:
        {
            "resolved_names":   [str, ...]
            "only_in_ref":      [str, ...]
            "only_in_new":      [str, ...]
            "differences":      [{"name": str, "ref_kv": {}, "new_kv": {}, "diff_keys": [..]}]
            "identical":        [str, ...]
            "ref_error":        str | None
            "new_error":        str | None
        }
    """
    result = {
        "resolved_names": [],
        "only_in_ref": [],
        "only_in_new": [],
        "differences": [],
        "identical": [],
        "ref_error": None,
        "new_error": None,
    }

    try:
        ref_parsed = parse_all_instances(ref_mtpl)
    except Exception as e:
        result["ref_error"] = str(e)
        ref_parsed = {}

    try:
        new_parsed = parse_all_instances(new_mtpl)
    except Exception as e:
        result["new_error"] = str(e)
        new_parsed = {}

    # Resolve names against ref (primary) — auto-detect {X} against both dicts combined
    combined = {**ref_parsed, **new_parsed}
    names = resolve_instances(cfg, combined)
    result["resolved_names"] = names

    for name in names:
        in_ref = name in ref_parsed
        in_new = name in new_parsed

        if in_ref and not in_new:
            result["only_in_ref"].append(name)
        elif in_new and not in_ref:
            result["only_in_new"].append(name)
        else:
            ref_kv = ref_parsed[name]["key_values"]
            new_kv = new_parsed[name]["key_values"]

            all_keys = sorted(set(ref_kv.keys()) | set(new_kv.keys()))
            diff_keys = [k for k in all_keys if ref_kv.get(k) != new_kv.get(k)]

            if diff_keys:
                result["differences"].append({
                    "name": name,
                    "type": ref_parsed[name]["type"],
                    "ref_kv": ref_kv,
                    "new_kv": new_kv,
                    "all_keys": all_keys,
                    "diff_keys": diff_keys,
                })
            else:
                result["identical"].append(name)

    return result
