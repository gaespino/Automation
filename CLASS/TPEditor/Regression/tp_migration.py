"""
tp_migration.py
---------------
Flask web application for TP Migration Comparison Tool.
Run: python tp_migration.py  → opens at http://localhost:5050
"""

import os
import sys
import json
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Add project dir to path for core imports
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE_DIR)

from core.config_manager import load_config, save_config, resolve_paths, validate_paths
from core.env_parser import compare_env
from core.plist_parser import compare_plist_folders, check_duplicates, compare_xml_plist
from core.mtpl_parser import compare_instances
from core.json_comparator import (
    compare_shmoo, compare_patmod, compare_utp, compare_defeature, get_patmod_names
)
from core.migration_applier import apply_actions

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "tp_migration_tool_2026"

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _get_cfg_and_resolved():
    cfg = load_config()
    resolved = resolve_paths(cfg)
    return cfg, resolved


def _open_file_dialog(dialog_type="folder"):
    """Open a native Windows file/folder dialog and return the selected path."""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    if dialog_type == "folder":
        path = filedialog.askdirectory(title="Select folder")
    else:
        path = filedialog.askopenfilename(title="Select file")
    root.destroy()
    return path or ""


# -----------------------------------------------------------------------
# Routes: Config
# -----------------------------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("config_page"))


@app.route("/config")
def config_page():
    cfg = load_config()
    cfg_json = json.dumps(cfg, indent=2)
    return render_template("config.html", cfg=cfg, cfg_json=cfg_json)


@app.route("/save_config", methods=["POST"])
def save_config_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400
    try:
        save_config(data)
        cfg, resolved = _get_cfg_and_resolved()
        path_status = validate_paths(resolved)
        return jsonify({
            "success": True,
            "message": "Configuration saved.",
            "path_status": path_status,
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/validate_paths")
def validate_paths_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        path_status = validate_paths(resolved)
        return jsonify({"success": True, "path_status": path_status})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/browse")
def browse():
    dialog_type = request.args.get("type", "folder")
    path = _open_file_dialog(dialog_type)
    return jsonify({"path": path})


# -----------------------------------------------------------------------
# Routes: Compare sections
# -----------------------------------------------------------------------

@app.route("/compare/env")
def compare_env_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_env(resolved["ref_env_file"], resolved["new_env_file"])
        return render_template("compare_env.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="Environment File",
                               error=str(e), cfg=load_config())


@app.route("/compare/plists")
def compare_plists_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_plist_folders(
            resolved["ref_supersede_plist"],
            resolved["new_supersede_plist"]
        )
        duplicates = check_duplicates(resolved["new_supersede_plist"])
        return render_template("compare_plists.html", result=result,
                               duplicates=duplicates, cfg=cfg, resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="Supersede PList",
                               error=str(e), cfg=load_config())


@app.route("/compare/mtpl")
def compare_mtpl_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_instances(
            resolved["ref_mtpl_file"],
            resolved["new_mtpl_file"],
            cfg
        )
        return render_template("compare_mtpl.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="MTPL Instances",
                               error=str(e), cfg=load_config())


@app.route("/compare/shmoo")
def compare_shmoo_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_shmoo(
            resolved["ref_shmoo_config"],
            resolved["new_shmoo_config"]
        )
        return render_template("compare_shmoo.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="Shmoo Config",
                               error=str(e), cfg=load_config())


@app.route("/compare/patmod")
def compare_patmod_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_patmod(
            resolved["ref_patmod_file"],
            resolved["new_patmod_file"],
            cfg.get("patmod_patterns", [])
        )
        return render_template("compare_patmod.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="Patmod",
                               error=str(e), cfg=load_config())


@app.route("/compare/utp")
def compare_utp_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        patmod_names = get_patmod_names(resolved["new_patmod_file"])
        result = compare_utp(
            resolved["ref_utp_setpoints"],
            resolved["new_utp_setpoints"],
            patmod_names
        )
        return render_template("compare_utp.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="UTP Setpoints",
                               error=str(e), cfg=load_config())


@app.route("/compare/xmlplist")
def compare_xmlplist_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_xml_plist(
            resolved["ref_plist_xml"],
            resolved["new_plist_xml"],
            resolved["ref_supersede_plist"],
            resolved["new_supersede_plist"],
        )
        return render_template("compare_xmlplist.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="XML PList",
                               error=str(e), cfg=load_config())


@app.route("/compare/defeature")
def compare_defeature_route():
    try:
        cfg, resolved = _get_cfg_and_resolved()
        result = compare_defeature(
            resolved["ref_input_files"],
            resolved["new_input_files"]
        )
        return render_template("compare_defeature.html", result=result, cfg=cfg,
                               resolved=resolved)
    except Exception as e:
        return render_template("error.html", section="Defeature Tracking",
                               error=str(e), cfg=load_config())


# -----------------------------------------------------------------------
# Routes: Apply changes
# -----------------------------------------------------------------------

@app.route("/apply", methods=["POST"])
def apply_route():
    data = request.get_json()
    if not data or "actions" not in data:
        return jsonify({"success": False, "message": "No actions provided"}), 400
    try:
        cfg, resolved = _get_cfg_and_resolved()
        results, backup_folder = apply_actions(data["actions"], resolved)
        success_count = sum(1 for r in results if r.get("success"))
        return jsonify({
            "success": True,
            "results": results,
            "summary": f"{success_count}/{len(results)} actions applied successfully.",
            "backup_folder": backup_folder or "",
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# -----------------------------------------------------------------------
# Routes: Changelog
# -----------------------------------------------------------------------

@app.route("/changelog")
def changelog_route():
    log_file = os.path.join(_BASE_DIR, "output", "change_log.json")
    entries = []
    if os.path.isfile(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as fh:
                entries = json.load(fh)
        except Exception:
            entries = []
    entries = list(reversed(entries))  # most recent first
    return render_template("changelog.html", entries=entries, cfg=load_config())


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

if __name__ == "__main__":
    port = 5050
    url = f"http://localhost:{port}"

    # Open browser after a brief delay to let Flask start
    def open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    print(f"\n  TP Migration Tool running at {url}\n  Press Ctrl+C to stop.\n")
    app.run(debug=False, port=port, use_reloader=False)
