from flask import Blueprint, jsonify

routes = Blueprint("routes", __name__)


@routes.route("/alive", methods=["GET"])
def alive():
    return jsonify(success=True)
