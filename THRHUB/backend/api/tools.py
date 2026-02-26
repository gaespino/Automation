"""
THR Tools API Blueprint
========================
Endpoints for all 9 THR tools.
"""
import logging
import json
import uuid
import os
from datetime import datetime
from flask import Blueprint, jsonify, request

from services.data_handler import DataHandler
from services.thr_service import MCAService, LoopParserService, FuseService

bp = Blueprint("tools", __name__)
logger = logging.getLogger(__name__)
_data = DataHandler()

# ── Experiment Builder ─────────────────────────────────────────────────────────

@bp.route("/experiments", methods=["GET"])
def list_experiments():
    """List all saved experiment sessions."""
    try:
        sessions = _data.list_sessions("experiments")
        return jsonify(sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/experiments", methods=["POST"])
def save_experiments():
    """Save an experiment batch (array of experiment objects)."""
    payload = request.get_json(force=True, silent=True) or {}
    experiments = payload.get("experiments", [])
    name = payload.get("name", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    try:
        session_id = _data.save_session("experiments", name, experiments)
        return jsonify({"id": session_id, "name": name, "count": len(experiments)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/experiments/<session_id>", methods=["GET"])
def get_experiment_session(session_id: str):
    """Load a saved experiment session."""
    try:
        session = _data.load_session("experiments", session_id)
        if session is None:
            return jsonify({"error": "Session not found"}), 404
        return jsonify(session)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Automation Designer ────────────────────────────────────────────────────────

@bp.route("/automation-flows", methods=["GET"])
def list_flows():
    """List all saved automation flows."""
    try:
        flows = _data.list_sessions("flows")
        return jsonify(flows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/automation-flows", methods=["POST"])
def save_flow():
    """Save an automation flow (nodes + edges from React Flow)."""
    payload = request.get_json(force=True, silent=True) or {}
    name = payload.get("name", f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    flow_data = {
        "nodes": payload.get("nodes", []),
        "edges": payload.get("edges", []),
        "metadata": payload.get("metadata", {}),
    }
    try:
        flow_id = _data.save_session("flows", name, flow_data)
        return jsonify({"id": flow_id, "name": name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/automation-flows/<flow_id>", methods=["GET"])
def get_flow(flow_id: str):
    """Load a saved automation flow."""
    try:
        flow = _data.load_session("flows", flow_id)
        if flow is None:
            return jsonify({"error": "Flow not found"}), 404
        return jsonify(flow)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── MCA Decoder ───────────────────────────────────────────────────────────────

@bp.route("/mca/decode", methods=["POST"])
def decode_mca():
    """
    Decode an MCA register value.
    Body: { "register": "0x...", "type": "CHA|LLC|CORE|MEMORY|IO", "product": "GNR|CWF|DMR" }
    """
    body = request.get_json(force=True, silent=True) or {}
    register = body.get("register", "")
    reg_type = body.get("type", "CORE")
    product = body.get("product", "GNR")
    try:
        result = MCAService.decode(register, reg_type, product)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Loop Parser ───────────────────────────────────────────────────────────────

@bp.route("/loop-parser/parse", methods=["POST"])
def parse_loops():
    """
    Parse loop log content.
    Body: { "content": "<log text>", "product": "GNR|CWF|DMR" }
    """
    body = request.get_json(force=True, silent=True) or {}
    content = body.get("content", "")
    product = body.get("product", "GNR")
    try:
        result = LoopParserService.parse(content, product)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Fuse Generator ────────────────────────────────────────────────────────────

@bp.route("/fuses/parse", methods=["POST"])
def parse_fuses():
    """
    Parse fuse CSV content.
    Body: { "content": "<csv text>", "product": "GNR|CWF|DMR", "ip_filter": "..." }
    """
    body = request.get_json(force=True, silent=True) or {}
    content = body.get("content", "")
    product = body.get("product", "GNR")
    ip_filter = body.get("ip_filter", "")
    try:
        result = FuseService.parse(content, product, ip_filter)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
