"""
env_parser.py
-------------
Parse .env files and compare HDST_PAT_PATH entries between ref and new TP.
"""

import re
import os
from typing import List, Dict


def _extract_hdst_pat_path(env_filepath: str) -> List[str]:
    """
    Read an .env file and extract all path entries from the HDST_PAT_PATH variable.
    Returns a list of stripped path strings (empty strings filtered out).
    """
    if not os.path.isfile(env_filepath):
        raise FileNotFoundError(f"Env file not found: {env_filepath}")

    with open(env_filepath, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    # Match the HDST_PAT_PATH block: everything between first " after = and the final ;
    # The block spans multiple lines and uses "..." + "..." continuation
    match = re.search(
        r'HDST_PAT_PATH\s*=\s*([\s\S]+?);(?:\s*\n|\s*$)',
        content
    )
    if not match:
        return []

    block = match.group(1)

    # Remove C-style line comments
    block = re.sub(r'//[^\n]*', '', block)

    # Split on semicolons preceded by string segments - extract quoted strings first
    # Each path is inside double-quotes, separated by + operators and semicolons
    # Pattern: extract everything inside quotes
    raw_paths = re.findall(r'"([^"]*)"', block)

    # Each raw_paths entry may contain multiple ;-separated paths
    paths = []
    for entry in raw_paths:
        for part in entry.split(";"):
            part = part.strip()
            if part:
                paths.append(part)

    return paths


def classify_path(path: str) -> str:
    """Classify a path entry by type."""
    if path.startswith("~"):
        return "INTERNAL"
    if path.startswith("\\\\"):
        return "EXTERNAL_UNC"
    if re.match(r'^[A-Za-z]:\\', path):
        return "LOCAL"
    if path.startswith("$"):
        return "VAR"
    return "OTHER"


def compare_env(ref_filepath: str, new_filepath: str) -> Dict:
    """
    Compare HDST_PAT_PATH entries between reference and new .env files.
    Returns a dict with:
      - ref_paths: ordered list from ref
      - new_paths: ordered list from new
      - only_in_ref: paths present in ref but not new
      - only_in_new: paths present in new but not ref
      - in_both: paths present in both
      - ref_error / new_error: error strings if files couldn't be parsed
    """
    result = {
        "ref_paths": [],
        "new_paths": [],
        "only_in_ref": [],
        "only_in_new": [],
        "in_both": [],
        "ref_error": None,
        "new_error": None,
    }

    try:
        ref_paths = _extract_hdst_pat_path(ref_filepath)
        result["ref_paths"] = [{"path": p, "type": classify_path(p)} for p in ref_paths]
    except Exception as e:
        result["ref_error"] = str(e)
        ref_paths = []

    try:
        new_paths = _extract_hdst_pat_path(new_filepath)
        result["new_paths"] = [{"path": p, "type": classify_path(p)} for p in new_paths]
    except Exception as e:
        result["new_error"] = str(e)
        new_paths = []

    ref_set = set(ref_paths)
    new_set = set(new_paths)

    result["only_in_ref"] = [
        {"path": p, "type": classify_path(p)} for p in ref_paths if p not in new_set
    ]
    result["only_in_new"] = [
        {"path": p, "type": classify_path(p)} for p in new_paths if p not in ref_set
    ]
    result["in_both"] = [
        {"path": p, "type": classify_path(p)} for p in ref_paths if p in new_set
    ]

    return result
