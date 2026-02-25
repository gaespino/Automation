"""
plist_parser.py
---------------
Parse .plist files, extract GlobalPList names, compare folders, detect duplicates.
"""

import os
import re
from typing import Dict, List


def extract_plist_names(filepath: str) -> List[str]:
    """
    Return all GlobalPList names found in a .plist file.
    Each GlobalPList block starts with:
        GlobalPList <name> [...] {
    """
    names = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        # Match GlobalPList followed by the name (first token after it)
        for m in re.finditer(r'GlobalPList\s+(\S+)\s', content):
            names.append(m.group(1))
    except Exception:
        pass
    return names


def extract_plist_blocks(filepath: str) -> Dict[str, str]:
    """
    Return a dict of {plist_name: full_block_text} for a .plist file.
    Block ends at the matching closing brace.
    """
    blocks = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()

        # Find each GlobalPList header
        for m in re.finditer(r'(GlobalPList\s+(\S+)[\s\S]+?\}[^\n]*#end[^\n]*)', content):
            plist_name = m.group(2)
            blocks[plist_name] = m.group(1)
    except Exception:
        pass
    return blocks


def compare_plist_folders(ref_dir: str, new_dir: str) -> Dict:
    """
    Compare all .plist files between ref and new TP supersede directories.

    Returns:
      files_only_in_ref  - list of filenames only in ref
      files_only_in_new  - list of filenames only in new
      files_in_both      - list of per-file dicts with plist-level diff
    """
    result = {
        "ref_dir": ref_dir,
        "new_dir": new_dir,
        "ref_error": None,
        "new_error": None,
        "files_only_in_ref": [],
        "files_only_in_new": [],
        "files_in_both": [],
    }

    def list_plists(directory):
        try:
            return {
                f: os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.lower().endswith(".plist")
            }
        except Exception as e:
            return {"__error__": str(e)}

    ref_files = list_plists(ref_dir)
    new_files = list_plists(new_dir)

    if "__error__" in ref_files:
        result["ref_error"] = ref_files["__error__"]
        ref_files = {}
    if "__error__" in new_files:
        result["new_error"] = new_files["__error__"]
        new_files = {}

    ref_names = set(ref_files.keys())
    new_names = set(new_files.keys())

    result["files_only_in_ref"] = sorted(ref_names - new_names)
    result["files_only_in_new"] = sorted(new_names - ref_names)

    for fname in sorted(ref_names & new_names):
        ref_blocks = extract_plist_blocks(ref_files[fname])
        new_blocks = extract_plist_blocks(new_files[fname])

        ref_plist_names = set(ref_blocks.keys())
        new_plist_names = set(new_blocks.keys())

        file_diff = {
            "filename": fname,
            "ref_path": ref_files[fname],
            "new_path": new_files[fname],
            "only_in_ref": sorted(ref_plist_names - new_plist_names),
            "only_in_new": sorted(new_plist_names - ref_plist_names),
            "in_both_different": [],
            "in_both_identical": [],
        }

        for pname in sorted(ref_plist_names & new_plist_names):
            ref_block = ref_blocks[pname].strip()
            new_block = new_blocks[pname].strip()
            if ref_block != new_block:
                file_diff["in_both_different"].append({
                    "name": pname,
                    "ref_block": ref_block,
                    "new_block": new_block,
                })
            else:
                file_diff["in_both_identical"].append(pname)

        result["files_in_both"].append(file_diff)

    return result


def check_duplicates(new_dir: str) -> Dict:
    """
    Scan all .plist files in new_dir and report any GlobalPList names
    that appear more than once WITHIN THE SAME FILE.

    Returns:
      {filename: [list_of_duplicate_names]}
    Only files that actually contain duplicates are returned.
    """
    result: Dict[str, List[str]] = {}
    try:
        for fname in os.listdir(new_dir):
            if fname.lower().endswith(".plist"):
                fpath = os.path.join(new_dir, fname)
                names = extract_plist_names(fpath)
                seen: Dict[str, int] = {}
                for name in names:
                    seen[name] = seen.get(name, 0) + 1
                dups = [n for n, count in seen.items() if count > 1]
                if dups:
                    result[fname] = dups
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# XML Plist (UCCAP.all.plist.xml) comparison
# ---------------------------------------------------------------------------

def _extract_xml_plist_names(xml_filepath: str) -> List[str]:
    """
    Extract all plist/pattern names referenced in an UCCAP.all.plist.xml file.
    Handles both XML attributes and text content containing plist names.
    Returns a sorted list of unique names found.
    """
    names = set()
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_filepath)
        root = tree.getroot()

        # Collect all attribute values and text content that look like plist names
        # Plist names are typically identifiers with underscores and letters
        plist_name_re = re.compile(r'^[A-Za-z][A-Za-z0-9_]+$')

        def _walk(elem):
            for attr_val in elem.attrib.values():
                val = attr_val.strip()
                if val and plist_name_re.match(val):
                    names.add(val)
            if elem.text:
                for token in re.split(r'[\s,;]+', elem.text):
                    token = token.strip()
                    if token and plist_name_re.match(token):
                        names.add(token)
            for child in elem:
                _walk(child)

        _walk(root)

    except Exception:
        # Fallback: regex scan for plausible plist names in raw XML text
        try:
            with open(xml_filepath, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
            # Match names in attributes: name="..." or value="..."
            for m in re.finditer(r'(?:name|value|plist|id)\s*=\s*"([A-Za-z][A-Za-z0-9_]+)"',
                                 raw, re.IGNORECASE):
                names.add(m.group(1))
            # Also match bare identifiers that look like plist names (long, underscored)
            for m in re.finditer(r'\b([A-Za-z][A-Za-z0-9]+(?:_[A-Za-z0-9]+){3,})\b', raw):
                names.add(m.group(1))
        except Exception:
            pass

    return sorted(names)


def compare_xml_plist(ref_xml: str, new_xml: str,
                      ref_plist_dir: str, new_plist_dir: str) -> Dict:
    """
    Compare UCCAP.all.plist.xml files from ref and new.
    Also cross-references with the supersede/plist directory to show:
      - which plist names are referenced in the XML but have no .plist file (missing)
      - which .plist files exist in supersede but are NOT referenced in the XML

    Returns:
      ref_names:      all names in ref XML
      new_names:      all names in new XML
      only_in_ref:    names in ref XML but not new XML
      only_in_new:    names in new XML but not ref XML
      in_both:        names in both
      missing_from_new_dir:  names in new XML with no .plist file in new supersede dir
      unreferenced_in_new:   .plist files in new supersede dir not mentioned in new XML
      ref_error / new_error
    """
    result = {
        "ref_xml": ref_xml,
        "new_xml": new_xml,
        "ref_names": [],
        "new_names": [],
        "only_in_ref": [],
        "only_in_new": [],
        "in_both": [],
        "missing_from_new_dir": [],
        "unreferenced_in_new": [],
        "ref_error": None,
        "new_error": None,
    }

    try:
        ref_names = _extract_xml_plist_names(ref_xml)
        result["ref_names"] = ref_names
    except Exception as e:
        result["ref_error"] = str(e)
        ref_names = []

    try:
        new_names = _extract_xml_plist_names(new_xml)
        result["new_names"] = new_names
    except Exception as e:
        result["new_error"] = str(e)
        new_names = []

    ref_set = set(ref_names)
    new_set = set(new_names)

    result["only_in_ref"] = sorted(ref_set - new_set)
    result["only_in_new"] = sorted(new_set - ref_set)
    result["in_both"] = sorted(ref_set & new_set)

    # Cross-reference with new plist dir
    try:
        # All plist names available in new supersede dir
        new_dir_names: set = set()
        for fname in os.listdir(new_plist_dir):
            if fname.lower().endswith(".plist"):
                fpath = os.path.join(new_plist_dir, fname)
                for pname in extract_plist_names(fpath):
                    new_dir_names.add(pname)

        # Names referenced in new XML but not found in any plist file
        result["missing_from_new_dir"] = sorted(new_set - new_dir_names)

        # Plist files that exist but are not referenced in new XML
        result["unreferenced_in_new"] = sorted(new_dir_names - new_set)
    except Exception:
        pass

    return result
