"""
migration_applier.py
--------------------
Apply migration changes to new TP files, with automatic backup and change logging.
"""

import json
import os
import re
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKUP_ROOT = os.path.join(_BASE_DIR, "backups")
_LOG_FILE = os.path.join(_BASE_DIR, "output", "change_log.json")

# Session-level backup folder - same for all changes in one apply run
_session_id: Optional[str] = None


def _get_session_id() -> str:
    global _session_id
    if _session_id is None:
        _session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _session_id


def reset_session():
    """Call at the start of each apply batch to group backups together."""
    global _session_id
    _session_id = datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_file(filepath: str) -> str:
    """
    Copy filepath into backups/<session_id>/<original_filename>.
    Returns the backup destination path.
    """
    session = _get_session_id()
    backup_dir = os.path.join(_BACKUP_ROOT, session)
    os.makedirs(backup_dir, exist_ok=True)

    fname = os.path.basename(filepath)
    dest = os.path.join(backup_dir, fname)

    # If the same filename already exists (e.g., two files with same name),
    # append a counter to avoid overwriting a previous backup in this session.
    counter = 1
    while os.path.exists(dest):
        base, ext = os.path.splitext(fname)
        dest = os.path.join(backup_dir, f"{base}_{counter}{ext}")
        counter += 1

    shutil.copy2(filepath, dest)
    return dest


def log_change(action: str, description: str, affected_files: List[str],
               details: Optional[Dict] = None):
    """Append an entry to output/change_log.json."""
    os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)

    existing = []
    if os.path.isfile(_LOG_FILE):
        try:
            with open(_LOG_FILE, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
        except Exception:
            existing = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "session": _get_session_id(),
        "action": action,
        "description": description,
        "affected_files": affected_files,
    }
    if details:
        entry["details"] = details

    existing.append(entry)

    with open(_LOG_FILE, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, indent=2)


# ---------------------------------------------------------------------------
# Action: add_env_path
# Inserts a UNC path entry into HDST_PAT_PATH in the new .env file,
# just before the "$TORCH_AUTO_PAT_PATH" entry or at the end of the block.
# ---------------------------------------------------------------------------
def add_env_path(env_filepath: str, path_entry: str) -> Dict:
    """
    Insert `path_entry` into the HDST_PAT_PATH block in the .env file.
    The entry is placed before the $TORCH_AUTO_PAT_PATH line.
    Returns {"success": bool, "message": str, "backup": str}.
    """
    if not os.path.isfile(env_filepath):
        return {"success": False, "message": f"File not found: {env_filepath}"}

    backup_path = backup_file(env_filepath)

    with open(env_filepath, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    # Find insertion point: just before "$TORCH_AUTO_PAT_PATH"
    insert_line = f'\t\t\t\t"\\\\{path_entry.lstrip(chr(92))};" +\n'

    torch_pattern = re.compile(r'(\s*"\$TORCH_AUTO_PAT_PATH")', re.MULTILINE)
    m = torch_pattern.search(content)
    if m:
        insert_pos = m.start()
        new_content = content[:insert_pos] + insert_line + content[insert_pos:]
    else:
        # Fallback: append before closing semicolon of the block
        semi_match = re.search(r'(HDST_PAT_PATH\s*=[\s\S]+?)(;\s*\n)', content)
        if semi_match:
            insert_pos = semi_match.start(2)
            new_content = content[:insert_pos] + insert_line + content[insert_pos:]
        else:
            return {"success": False, "message": "Could not find insertion point in env file"}

    with open(env_filepath, "w", encoding="utf-8") as fh:
        fh.write(new_content)

    log_change("add_env_path", f"Added path: {path_entry}", [env_filepath],
               {"path_entry": path_entry})
    return {"success": True, "message": f"Added path entry", "backup": backup_path}


# ---------------------------------------------------------------------------
# Action: copy_plist_entry
# Appends a GlobalPList block from ref to new .plist file.
# ---------------------------------------------------------------------------
def copy_plist_entry(ref_plist_fp: str, new_plist_fp: str, plist_name: str) -> Dict:
    """
    Find the GlobalPList `plist_name` block in ref and append it to new_plist_fp.
    """
    if not os.path.isfile(ref_plist_fp):
        return {"success": False, "message": f"Ref plist not found: {ref_plist_fp}"}
    if not os.path.isfile(new_plist_fp):
        return {"success": False, "message": f"New plist not found: {new_plist_fp}"}

    with open(ref_plist_fp, "r", encoding="utf-8", errors="replace") as fh:
        ref_content = fh.read()

    # Extract the block for plist_name
    pattern = re.compile(
        rf'(GlobalPList\s+{re.escape(plist_name)}\b[\s\S]+?\}}[^\n]*#end[^\n]*)',
        re.MULTILINE
    )
    m = pattern.search(ref_content)
    if not m:
        return {"success": False, "message": f"GlobalPList '{plist_name}' not found in ref"}

    block = m.group(1)

    backup_path = backup_file(new_plist_fp)

    with open(new_plist_fp, "r", encoding="utf-8", errors="replace") as fh:
        new_content = fh.read()

    new_content = new_content.rstrip() + "\n\n" + block + "\n"

    with open(new_plist_fp, "w", encoding="utf-8") as fh:
        fh.write(new_content)

    log_change("copy_plist_entry", f"Copied GlobalPList: {plist_name}",
               [new_plist_fp], {"plist_name": plist_name, "source": ref_plist_fp})
    return {"success": True, "message": f"Copied GlobalPList '{plist_name}'",
            "backup": backup_path}


# ---------------------------------------------------------------------------
# Action: apply_shmoo_key
# Add or update a key in the new shmoo JSON file.
# ---------------------------------------------------------------------------
def apply_shmoo_key(new_fp: str, key: str, ref_value: Any) -> Dict:
    """Add or overwrite a key in the new shmoo config JSON."""
    if not os.path.isfile(new_fp):
        return {"success": False, "message": f"File not found: {new_fp}"}

    backup_path = backup_file(new_fp)

    with open(new_fp, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict):
        data[key] = ref_value
    elif isinstance(data, list):
        # keyed list — find and update or append
        found = False
        for item in data:
            if isinstance(item, dict) and item.get("Name") == key:
                item.update(ref_value if isinstance(ref_value, dict) else {"value": ref_value})
                found = True
                break
        if not found:
            if isinstance(ref_value, dict):
                data.append(ref_value)
            else:
                data.append({"Name": key, "value": ref_value})

    with open(new_fp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    log_change("apply_shmoo_key", f"Applied shmoo key: {key}", [new_fp],
               {"key": key})
    return {"success": True, "message": f"Applied key '{key}'", "backup": backup_path}


# ---------------------------------------------------------------------------
# Action: add_patmod_entry
# Copy a patmod entry (+ preceding comments) from ref to new .patmod.json
# ---------------------------------------------------------------------------
def add_patmod_entry(ref_fp: str, new_fp: str, entry_name: str) -> Dict:
    """
    Locate the patmod entry `entry_name` in ref (including preceding /* */ comments)
    and append it to the new patmod file.
    """
    if not os.path.isfile(ref_fp):
        return {"success": False, "message": f"Ref patmod not found: {ref_fp}"}
    if not os.path.isfile(new_fp):
        return {"success": False, "message": f"New patmod not found: {new_fp}"}

    with open(ref_fp, "r", encoding="utf-8", errors="replace") as fh:
        ref_raw = fh.read()

    # Find the block: look backwards from "Name": "entry_name" to grab comments
    # Capture up to 5 comment lines before the entry's opening {
    entry_pattern = re.compile(
        rf'((?:[ \t]*/\*[^*]*\*/[ \t]*\n)*\s*\{{[^{{}}]*?"Name"\s*:\s*"{re.escape(entry_name)}"[\s\S]*?\}})',
        re.MULTILINE
    )
    m = entry_pattern.search(ref_raw)
    if not m:
        # Fallback: find just the dict entry without comments
        simple = re.compile(
            rf'(\{{[^{{}}]*?"Name"\s*:\s*"{re.escape(entry_name)}"[\s\S]*?\}})',
            re.MULTILINE
        )
        m = simple.search(ref_raw)
        if not m:
            return {"success": False, "message": f"Entry '{entry_name}' not found in ref patmod"}

    block_text = m.group(1).strip()

    backup_path = backup_file(new_fp)

    with open(new_fp, "r", encoding="utf-8", errors="replace") as fh:
        new_raw = fh.read()

    # Try to insert before the closing ] of the JSON array
    closing_bracket = new_raw.rfind("]")
    if closing_bracket != -1:
        # Find last entry's closing brace to place a comma
        last_entry_end = new_raw.rfind("}", 0, closing_bracket)
        if last_entry_end != -1:
            new_raw = (
                new_raw[:last_entry_end + 1]
                + ",\n    " + block_text
                + new_raw[last_entry_end + 1:]
            )
        else:
            new_raw = new_raw[:closing_bracket] + "    " + block_text + "\n" + new_raw[closing_bracket:]
    else:
        new_raw = new_raw.rstrip() + ",\n" + block_text + "\n"

    with open(new_fp, "w", encoding="utf-8") as fh:
        fh.write(new_raw)

    log_change("add_patmod_entry", f"Added patmod entry: {entry_name}", [new_fp],
               {"entry_name": entry_name, "source": ref_fp})
    return {"success": True, "message": f"Added patmod entry '{entry_name}'",
            "backup": backup_path}


# ---------------------------------------------------------------------------
# Action: add_utp_entry
# Copy a UTP setpoints entry from ref to new
# ---------------------------------------------------------------------------
def add_utp_entry(ref_fp: str, new_fp: str, entry_name: str) -> Dict:
    """Copy a Name block from ref UTP setpoints to new."""
    if not os.path.isfile(ref_fp):
        return {"success": False, "message": f"Ref UTP not found: {ref_fp}"}
    if not os.path.isfile(new_fp):
        return {"success": False, "message": f"New UTP not found: {new_fp}"}

    try:
        with open(ref_fp, "r", encoding="utf-8") as fh:
            ref_data = json.load(fh)
    except Exception as e:
        return {"success": False, "message": f"Could not parse ref UTP: {e}"}

    # Find the entry
    entry = None
    for item in (ref_data if isinstance(ref_data, list) else [ref_data]):
        if isinstance(item, dict) and item.get("Name") == entry_name:
            entry = item
            break

    if entry is None:
        return {"success": False, "message": f"Entry '{entry_name}' not found in ref UTP"}

    backup_path = backup_file(new_fp)

    try:
        with open(new_fp, "r", encoding="utf-8") as fh:
            new_data = json.load(fh)
    except Exception as e:
        return {"success": False, "message": f"Could not parse new UTP: {e}"}

    if not isinstance(new_data, list):
        new_data = [new_data]

    # Remove existing entry with same name (if any) then append
    new_data = [i for i in new_data if not (isinstance(i, dict) and i.get("Name") == entry_name)]
    new_data.append(entry)

    with open(new_fp, "w", encoding="utf-8") as fh:
        json.dump(new_data, fh, indent=2)

    log_change("add_utp_entry", f"Added UTP entry: {entry_name}", [new_fp],
               {"entry_name": entry_name, "source": ref_fp})
    return {"success": True, "message": f"Added UTP entry '{entry_name}'",
            "backup": backup_path}


# ---------------------------------------------------------------------------
# Action: copy_defeature_file
# Copy a whole defeature tracking JSON from ref InputFiles to new InputFiles
# ---------------------------------------------------------------------------
def copy_defeature_file(ref_fp: str, new_dir: str) -> Dict:
    """Copy a defeature tracking file from ref into the new InputFiles directory."""
    if not os.path.isfile(ref_fp):
        return {"success": False, "message": f"Ref file not found: {ref_fp}"}
    if not os.path.isdir(new_dir):
        return {"success": False, "message": f"New directory not found: {new_dir}"}

    fname = os.path.basename(ref_fp)
    dest = os.path.join(new_dir, fname)

    # Backup destination if it exists
    if os.path.isfile(dest):
        backup_file(dest)

    shutil.copy2(ref_fp, dest)

    log_change("copy_defeature_file", f"Copied defeature file: {fname}", [dest],
               {"source": ref_fp})
    return {"success": True, "message": f"Copied '{fname}' to new InputFiles",
            "backup": dest}


# ---------------------------------------------------------------------------
# Action: update_mtpl_key
# Update a single key in a Test/MultiTrialTest block in the new MTPL
# ---------------------------------------------------------------------------
def update_mtpl_key(new_mtpl_fp: str, instance_name: str, key: str, ref_value: str) -> Dict:
    """
    In the new MTPL file, find instance_name's block and update `key = value;`
    with ref_value.
    """
    if not os.path.isfile(new_mtpl_fp):
        return {"success": False, "message": f"New MTPL not found: {new_mtpl_fp}"}

    backup_path = backup_file(new_mtpl_fp)

    with open(new_mtpl_fp, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    # Find the block for instance_name
    # Pattern: (Test|MultiTrialTest) <type> instance_name { ... }
    block_pattern = re.compile(
        rf'((Test|MultiTrialTest)\s+\S+\s+{re.escape(instance_name)}\s*\{{[\s\S]+?\n\}})',
        re.MULTILINE
    )
    m = block_pattern.search(content)
    if not m:
        return {"success": False, "message": f"Instance '{instance_name}' not found in new MTPL"}

    block_start = m.start()
    block_end = m.end()
    block = m.group(1)

    # Replace the key line in the block
    key_pattern = re.compile(rf'^([ \t]*{re.escape(key)}\s*=\s*)[^;\n]+;', re.MULTILINE)
    new_block, n = key_pattern.subn(lambda mo: mo.group(1) + ref_value + ";", block)

    if n == 0:
        return {"success": False, "message": f"Key '{key}' not found in instance '{instance_name}'"}

    new_content = content[:block_start] + new_block + content[block_end:]

    with open(new_mtpl_fp, "w", encoding="utf-8") as fh:
        fh.write(new_content)

    log_change("update_mtpl_key", f"Updated {instance_name}.{key} = {ref_value}",
               [new_mtpl_fp], {"instance": instance_name, "key": key, "value": ref_value})
    return {"success": True, "message": f"Updated '{key}' in '{instance_name}'",
            "backup": backup_path}


# ---------------------------------------------------------------------------
# Dispatcher: apply a list of actions sent from the UI
# ---------------------------------------------------------------------------
def apply_actions(actions: List[Dict], resolved: Dict) -> List[Dict]:
    """
    Dispatch a list of action dicts from the frontend.

    Each action has:
      {"type": str, ...params}

    Returns a list of result dicts.
    """
    reset_session()
    results = []

    for action in actions:
        action_type = action.get("type", "")
        try:
            if action_type == "add_env_path":
                r = add_env_path(
                    resolved["new_env_file"],
                    action["path_entry"]
                )

            elif action_type == "copy_plist_entry":
                r = copy_plist_entry(
                    action["ref_plist_fp"],
                    action["new_plist_fp"],
                    action["plist_name"]
                )

            elif action_type == "apply_shmoo_key":
                r = apply_shmoo_key(
                    resolved["new_shmoo_config"],
                    action["key"],
                    action["ref_value"]
                )

            elif action_type == "add_patmod_entry":
                r = add_patmod_entry(
                    resolved["ref_patmod_file"],
                    resolved["new_patmod_file"],
                    action["entry_name"]
                )

            elif action_type == "add_utp_entry":
                r = add_utp_entry(
                    resolved["ref_utp_setpoints"],
                    resolved["new_utp_setpoints"],
                    action["entry_name"]
                )

            elif action_type == "copy_defeature_file":
                r = copy_defeature_file(
                    action["ref_fp"],
                    resolved["new_input_files"]
                )

            elif action_type == "update_mtpl_key":
                r = update_mtpl_key(
                    resolved["new_mtpl_file"],
                    action["instance_name"],
                    action["key"],
                    action["ref_value"]
                )

            else:
                r = {"success": False, "message": f"Unknown action type: {action_type}"}

        except Exception as e:
            r = {"success": False, "message": f"Exception: {e}"}

        r["action"] = action
        results.append(r)

    backup_folder = os.path.join(_BACKUP_ROOT, _get_session_id()) if any(r.get("success") for r in results) else None
    return results, backup_folder
