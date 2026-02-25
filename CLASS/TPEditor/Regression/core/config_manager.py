"""
config_manager.py
-----------------
Load, save, and resolve the project configuration (config.json).
"""

import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_FILE = os.path.join(_BASE_DIR, "config.json")


def load_config() -> dict:
    """Return raw config dict from config.json."""
    with open(_CONFIG_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_config(data: dict) -> None:
    """Persist config dict to config.json."""
    with open(_CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def resolve_paths(cfg: dict) -> dict:
    """
    Build fully-qualified paths for every content area in the config.
    Returns a dict with keys: ref_<name>, new_<name> for each sub_path entry,
    plus ref_tp_path and new_tp_path themselves.
    """
    ref = cfg["ref_tp_path"]
    new = cfg["new_tp_path"]
    sub = cfg.get("sub_paths", {})
    resolved = {
        "ref_tp_path": ref,
        "new_tp_path": new,
    }

    def join(base, rel):
        return os.path.normpath(os.path.join(base, rel)) if rel else ""

    # env file — ref and new have different sub-paths
    env = sub.get("env_file", {})
    resolved["ref_env_file"] = join(ref, env.get("ref", ""))
    resolved["new_env_file"] = join(new, env.get("new", ""))

    # plist XML — ref and new have different sub-paths
    pxml = sub.get("plist_xml", {})
    resolved["ref_plist_xml"] = join(ref, pxml.get("ref", ""))
    resolved["new_plist_xml"] = join(new, pxml.get("new", ""))

    # single sub-path keys (same relative path for ref and new)
    for key in ["supersede_plist", "mtpl_file", "input_files",
                "shmoo_config", "patmod_file", "utp_setpoints"]:
        rel = sub.get(key, "")
        resolved[f"ref_{key}"] = join(ref, rel)
        resolved[f"new_{key}"] = join(new, rel)

    return resolved


def validate_paths(resolved: dict) -> dict:
    """
    Check which resolved paths actually exist on disk.
    Returns {path_key: {"path": str, "exists": bool}}.
    """
    results = {}
    for key, path in resolved.items():
        results[key] = {"path": path, "exists": os.path.exists(path) if path else False}
    return results


def get_resolved() -> tuple:
    """Convenience: return (cfg, resolved_paths)."""
    cfg = load_config()
    resolved = resolve_paths(cfg)
    return cfg, resolved
