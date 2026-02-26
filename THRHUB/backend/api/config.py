"""
Config API Blueprint
=====================
Serves per-product Control Panel configuration JSON files.
"""
import json
import os
import logging
from flask import Blueprint, jsonify

from config import CONFIGS_PATH, PRODUCTS

bp = Blueprint("config", __name__)
logger = logging.getLogger(__name__)


@bp.route("/<product>", methods=["GET"])
def get_config(product: str):
    """Return the Control Panel config for a product (GNR / CWF / DMR)."""
    product = product.upper()
    if product not in PRODUCTS:
        return jsonify({"error": f"Unknown product: {product}. Valid: {PRODUCTS}"}), 400

    config_file = os.path.join(CONFIGS_PATH, f"{product}ControlPanelConfig.json")
    if not os.path.exists(config_file):
        logger.warning(f"Config file not found: {config_file}")
        return jsonify({}), 200

    try:
        with open(config_file, encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        logger.error(f"Error reading config {config_file}: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/", methods=["GET"])
def list_products():
    """Return the list of supported products."""
    return jsonify({"products": PRODUCTS})
