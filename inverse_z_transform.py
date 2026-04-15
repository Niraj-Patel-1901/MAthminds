from flask import Blueprint, request, jsonify
from inverse_z_transform_solver import solve_inverse_z_transform

bp = Blueprint("inverse_z_transform", __name__)

@bp.route("/api/inverse-z-transform", methods=["POST"])
def inverse_z_transform_api():
    data = request.get_json(force=True)
    expression = data.get("expression", "")
    method = data.get("method", "partial")

    result = solve_inverse_z_transform(expression, method)

    if not result.get("success"):
        return jsonify({"success": False, "error": result["error"]}), 400

    return jsonify({"success": True, "payload": result})
