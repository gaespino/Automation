"""
json_comparator.py
------------------
Diff shmoo configs, patmod files, UTP setpoints, and defeature tracking files.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(filepath: str, lenient: bool = False) -> Any:
    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if lenient:
            # Strip trailing commas before ] or } (common TP file issue)
            clean = re.sub(r',\s*(?=[}\]])', '', raw)
            return json.loads(clean)
        raise


def _deep_equal(a: Any, b: Any) -> bool:
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---------------------------------------------------------------------------
# Shmoo config comparison
# ---------------------------------------------------------------------------

def compare_shmoo(ref_fp: str, new_fp: str) -> Dict:
    """Flat key-value diff of two JSON shmoo config files."""
    result = {
        "ref_path": ref_fp,
        "new_path": new_fp,
        "ref_error": None,
        "new_error": None,
        "only_in_ref": [],
        "only_in_new": [],
        "different": [],
        "identical": [],
    }

    try:
        ref_data = _load_json(ref_fp, lenient=True)
    except Exception as e:
        result["ref_error"] = str(e)
        return result

    try:
        new_data = _load_json(new_fp, lenient=True)
    except Exception as e:
        result["new_error"] = str(e)
        return result

    # Flatten to key→value dicts (handle both object and array-of-dicts)
    def flatten(data):
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            # Assume list of dicts with "Name" key
            return {item.get("Name", str(i)): item for i, item in enumerate(data)}
        return {"__root__": data}

    ref_flat = flatten(ref_data)
    new_flat = flatten(new_data)

    all_keys = sorted(set(ref_flat.keys()) | set(new_flat.keys()))
    for k in all_keys:
        if k in ref_flat and k not in new_flat:
            result["only_in_ref"].append({"key": k, "ref_value": ref_flat[k]})
        elif k in new_flat and k not in ref_flat:
            result["only_in_new"].append({"key": k, "new_value": new_flat[k]})
        elif not _deep_equal(ref_flat[k], new_flat[k]):
            result["different"].append({
                "key": k,
                "ref_value": ref_flat[k],
                "new_value": new_flat[k],
            })
        else:
            result["identical"].append(k)

    return result


# ---------------------------------------------------------------------------
# Patmod comparison
# ---------------------------------------------------------------------------

def _match_any_pattern(name: str, patterns: List[str]) -> bool:
    if not patterns:
        return True  # no filter configured → show everything
    for p in patterns:
        # Support glob-style wildcards (*pattern* or *pattern)
        if '*' in p or '?' in p:
            # Convert glob to regex: * -> .*, ? -> .
            glob_rx = re.escape(p).replace(r'\*', '.*').replace(r'\?', '.')
            if re.search(glob_rx, name, re.IGNORECASE):
                return True
        elif p.startswith("^"):
            # Anchored regex
            if re.match(p, name, re.IGNORECASE):
                return True
        else:
            # Plain substring / regex search
            if re.search(p, name, re.IGNORECASE):
                return True
    return False


def _parse_patmod_with_labels(filepath: str) -> List[Dict]:
    """
    Parse a .patmod.json file that is JSON with embedded /* */ and // comments.
    Returns a list of {"name": str, "entry": dict, "preceding_comments": [str]}.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()

    # --- Step 1: clean comments -----------------------------------------------
    # Strip multi-line /* ... */ block comments (DOTALL)
    clean = re.sub(r'/\*.*?\*/', ' ', raw, flags=re.DOTALL)
    # Strip // line comments (but NOT http:// — don't touch : followed by //)
    clean = re.sub(r'(?m)(?<!:)//[^\n]*', ' ', clean)
    # Strip trailing commas (common in TP files)
    clean = re.sub(r',\s*(?=[}\]])', '', clean)

    # --- Step 2: parse JSON ---------------------------------------------------
    data = None
    for attempt in (clean, "[" + clean.strip().rstrip(",") + "]"):
        try:
            data = json.loads(attempt)
            break
        except json.JSONDecodeError:
            continue

    if data is None:
        return []

    # --- Step 3: unwrap wrapper objects  {"Configurations":[...]} etc ----------
    if isinstance(data, dict):
        for wrapper_key in ("Configurations", "configurations", "entries", "Entries", "items"):
            if wrapper_key in data and isinstance(data[wrapper_key], list):
                data = data[wrapper_key]
                break
        else:
            data = [data]

    if not isinstance(data, list):
        return []

    # --- Step 4: build entry list with names ----------------------------------
    entries = []
    for item in data:
        if isinstance(item, dict) and "Name" in item:
            entries.append({
                "name": item["Name"],
                "entry": item,
                "preceding_comments": [],
            })

    # --- Step 5: correlate preceding /* */ comments (positional, no backtracking) --
    # Pre-find all block comment positions in raw
    block_comments = [(m.start(), m.end(), m.group(1).strip())
                      for m in re.finditer(r'/\*(.*?)\*/', raw, re.DOTALL)
                      if m.group(1).strip()]

    for entry in entries:
        target_name = entry["name"]
        # Find first occurrence of this Name value in raw
        marker = f'"Name": "{target_name}"'
        pos = raw.find(marker)
        if pos == -1:
            continue
        # Find the closest block comment that ends before this position
        preceding = [c for (s, e, c) in block_comments if e <= pos]
        if preceding:
            # Take the last one (closest before the Name)
            entry["preceding_comments"] = [preceding[-1]]

    return entries


def compare_patmod(ref_fp: str, new_fp: str, patterns: List[str]) -> Dict:
    """
    Compare .patmod.json files, filtered to entries matching `patterns`.
    Returns per-entry diff with preceding comment labels.
    """
    result = {
        "ref_path": ref_fp,
        "new_path": new_fp,
        "ref_error": None,
        "new_error": None,
        "only_in_ref": [],
        "only_in_new": [],
        "different": [],
        "identical": [],
        # debug
        "_debug": {},
    }

    try:
        ref_entries = _parse_patmod_with_labels(ref_fp)
    except Exception as e:
        result["ref_error"] = str(e)
        return result

    try:
        new_entries = _parse_patmod_with_labels(new_fp)
    except Exception as e:
        result["new_error"] = str(e)
        return result

    # Filter by patterns
    ref_filtered = {
        e["name"]: e for e in ref_entries if _match_any_pattern(e["name"], patterns)
    }
    new_filtered = {
        e["name"]: e for e in new_entries if _match_any_pattern(e["name"], patterns)
    }

    result["_debug"] = {
        "ref_total": len(ref_entries),
        "new_total": len(new_entries),
        "ref_filtered": len(ref_filtered),
        "new_filtered": len(new_filtered),
        "patterns": patterns,
        "ref_path": ref_fp,
        "new_path": new_fp,
    }

    all_names = sorted(set(ref_filtered.keys()) | set(new_filtered.keys()))
    for name in all_names:
        in_ref = name in ref_filtered
        in_new = name in new_filtered
        if in_ref and not in_new:
            result["only_in_ref"].append(ref_filtered[name])
        elif in_new and not in_ref:
            result["only_in_new"].append(new_filtered[name])
        elif not _deep_equal(ref_filtered[name]["entry"], new_filtered[name]["entry"]):
            result["different"].append({
                "name": name,
                "ref_entry": ref_filtered[name],
                "new_entry": new_filtered[name],
            })
        else:
            result["identical"].append(name)

    return result


# ---------------------------------------------------------------------------
# UTP setpoints comparison + consistency check
# ---------------------------------------------------------------------------

def compare_utp(ref_fp: str, new_fp: str, patmod_names: Optional[set] = None) -> Dict:
    """
    Compare FUN_UTP_setpoints.json files by Name key.
    Also performs a consistency check: each Configuration value should exist
    in patmod_names (if provided).
    """
    result = {
        "ref_path": ref_fp,
        "new_path": new_fp,
        "ref_error": None,
        "new_error": None,
        "only_in_ref": [],
        "only_in_new": [],
        "different": [],
        "identical": [],
        "consistency_issues": [],
    }

    try:
        ref_data = _load_json(ref_fp, lenient=True)
    except Exception as e:
        result["ref_error"] = str(e)
        return result

    try:
        new_data = _load_json(new_fp, lenient=True)
    except Exception as e:
        result["new_error"] = str(e)
        return result

    def to_dict(data):
        if isinstance(data, list):
            return {item["Name"]: item for item in data if isinstance(item, dict) and "Name" in item}
        if isinstance(data, dict):
            return data
        return {}

    ref_dict = to_dict(ref_data)
    new_dict = to_dict(new_data)

    result["_debug"] = {
        "ref_total": len(ref_dict),
        "new_total": len(new_dict),
        "ref_path": ref_fp,
        "new_path": new_fp,
    }

    all_names = sorted(set(ref_dict.keys()) | set(new_dict.keys()))
    for name in all_names:
        in_ref = name in ref_dict
        in_new = name in new_dict
        if in_ref and not in_new:
            result["only_in_ref"].append({"name": name, "entry": ref_dict[name]})
        elif in_new and not in_ref:
            result["only_in_new"].append({"name": name, "entry": new_dict[name]})
        elif not _deep_equal(ref_dict[name], new_dict[name]):
            result["different"].append({
                "name": name,
                "ref_entry": ref_dict[name],
                "new_entry": new_dict[name],
            })
        else:
            result["identical"].append(name)

    # Consistency check against patmod
    if patmod_names:
        for name, entry in new_dict.items():
            for cfg_item in entry.get("Configurations", []):
                cfg_name = cfg_item.get("Configuration", "")
                elem_name = cfg_item.get("ElementName", "")
                if cfg_name and cfg_name not in patmod_names:
                    result["consistency_issues"].append({
                        "utp_name": name,
                        "configuration": cfg_name,
                        "element_name": elem_name,
                        "issue": "Configuration not found in patmod",
                    })
                if elem_name and elem_name not in patmod_names:
                    result["consistency_issues"].append({
                        "utp_name": name,
                        "configuration": cfg_name,
                        "element_name": elem_name,
                        "issue": "ElementName not found in patmod",
                    })

    return result


# ---------------------------------------------------------------------------
# DefeatureTracking file comparison
# ---------------------------------------------------------------------------

def compare_defeature(ref_dir: str, new_dir: str) -> Dict:
    """
    Find all *DefeatureTracking*.json files in ref InputFiles dir,
    compare each with its counterpart in new.
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

    def find_defeature_files(directory: str) -> Dict[str, str]:
        found = {}
        try:
            for f in os.listdir(directory):
                if "defeaturetracking" in f.lower() and f.lower().endswith(".json"):
                    found[f] = os.path.join(directory, f)
        except Exception as e:
            found["__error__"] = str(e)
        return found

    ref_files = find_defeature_files(ref_dir)
    new_files = find_defeature_files(new_dir)

    if "__error__" in ref_files:
        result["ref_error"] = ref_files.pop("__error__")
    if "__error__" in new_files:
        result["new_error"] = new_files.pop("__error__")

    ref_names = set(ref_files.keys())
    new_names = set(new_files.keys())

    result["files_only_in_ref"] = sorted(ref_names - new_names)
    result["files_only_in_new"] = sorted(new_names - ref_names)

    for fname in sorted(ref_names & new_names):
        try:
            ref_data = _load_json(ref_files[fname], lenient=True)
        except Exception as e:
            result["files_in_both"].append({
                "filename": fname,
                "ref_path": ref_files[fname],
                "new_path": new_files[fname],
                "error": f"ref load error: {e}",
            })
            continue
        try:
            new_data = _load_json(new_files[fname], lenient=True)
        except Exception as e:
            result["files_in_both"].append({
                "filename": fname,
                "ref_path": ref_files[fname],
                "new_path": new_files[fname],
                "error": f"new load error: {e}",
            })
            continue

        # Deep diff using flattened representation
        shmoo_like = compare_shmoo.__wrapped__ if hasattr(compare_shmoo, "__wrapped__") else None
        identical = _deep_equal(ref_data, new_data)
        diff_summary = _diff_json_trees(ref_data, new_data)

        result["files_in_both"].append({
            "filename": fname,
            "ref_path": ref_files[fname],
            "new_path": new_files[fname],
            "identical": identical,
            "diff": diff_summary if not identical else [],
        })

    return result


def _diff_json_trees(ref: Any, new: Any, path: str = "") -> List[Dict]:
    """Recursively diff two JSON structures, returning a list of change records."""
    diffs = []

    if isinstance(ref, dict) and isinstance(new, dict):
        all_keys = sorted(set(ref.keys()) | set(new.keys()))
        for k in all_keys:
            child_path = f"{path}.{k}" if path else k
            if k not in ref:
                diffs.append({"path": child_path, "status": "added", "new_value": new[k]})
            elif k not in new:
                diffs.append({"path": child_path, "status": "removed", "ref_value": ref[k]})
            else:
                diffs.extend(_diff_json_trees(ref[k], new[k], child_path))
    elif isinstance(ref, list) and isinstance(new, list):
        if not _deep_equal(ref, new):
            # Try name-keyed matching for lists of dicts
            if all(isinstance(i, dict) and "Name" in i for i in ref + new):
                ref_m = {i["Name"]: i for i in ref}
                new_m = {i["Name"]: i for i in new}
                for name in sorted(set(ref_m.keys()) | set(new_m.keys())):
                    child_path = f"{path}[Name={name}]"
                    if name not in ref_m:
                        diffs.append({"path": child_path, "status": "added", "new_value": new_m[name]})
                    elif name not in new_m:
                        diffs.append({"path": child_path, "status": "removed", "ref_value": ref_m[name]})
                    else:
                        diffs.extend(_diff_json_trees(ref_m[name], new_m[name], child_path))
            else:
                diffs.append({"path": path, "status": "changed",
                              "ref_value": ref, "new_value": new})
    else:
        if ref != new:
            diffs.append({"path": path, "status": "changed",
                          "ref_value": ref, "new_value": new})

    return diffs


def get_patmod_names(filepath: str) -> set:
    """
    Extract all Name values and ConfigurationElement Name values from a patmod file.
    Used for UTP consistency checks.
    """
    names = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        # Strip block comments
        clean = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)
        data = json.loads(clean)
        if not isinstance(data, list):
            data = [data]
        for item in data:
            if isinstance(item, dict):
                n = item.get("Name", "")
                if n:
                    names.add(n)
                for elem in item.get("ConfigurationElement", []):
                    en = elem.get("Name", "")
                    if en:
                        names.add(en)
    except Exception:
        pass
    return names
