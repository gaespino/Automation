"""
Dashboard API Blueprint
========================
Provides unit and experiment tracking data for the THRHUB Dashboard.
"""
import logging
from flask import Blueprint, jsonify, request

from services.unit_service import UnitService
from services.data_handler import DataHandler

bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)

_unit_svc = UnitService()
_data = DataHandler()


@bp.route("/stats", methods=["GET"])
def get_stats():
    """Return summary statistics for the dashboard."""
    try:
        stats = _unit_svc.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"stats error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/units", methods=["GET"])
def get_units():
    """Return all units. Optional ?product= and ?status= filters."""
    product = request.args.get("product")
    status = request.args.get("status")
    try:
        units = _unit_svc.list_units(product=product, status=status)
        return jsonify(units)
    except Exception as e:
        logger.error(f"list_units error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/units/<unit_id>", methods=["GET"])
def get_unit(unit_id: str):
    """Return detail for a single unit."""
    try:
        unit = _unit_svc.get_unit(unit_id)
        if unit is None:
            return jsonify({"error": "Unit not found"}), 404
        return jsonify(unit)
    except Exception as e:
        logger.error(f"get_unit error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/units", methods=["POST"])
def create_unit():
    """Create a new unit entry."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        unit = _unit_svc.create_unit(data)
        return jsonify(unit), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"create_unit error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/units/<unit_id>", methods=["PUT"])
def update_unit(unit_id: str):
    """Update an existing unit."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        unit = _unit_svc.update_unit(unit_id, data)
        if unit is None:
            return jsonify({"error": "Unit not found"}), 404
        return jsonify(unit)
    except Exception as e:
        logger.error(f"update_unit error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/units/<unit_id>/experiments", methods=["GET"])
def get_unit_experiments(unit_id: str):
    """Return experiments for a unit."""
    try:
        exps = _unit_svc.get_experiments(unit_id)
        return jsonify(exps)
    except Exception as e:
        logger.error(f"get_experiments error: {e}")
        return jsonify({"error": str(e)}), 500
