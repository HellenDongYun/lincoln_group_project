from flask import Blueprint, request, jsonify

from src.app.app_controller import town_service
api_blueprint = Blueprint('api', __name__)

@api_blueprint.route("new-zealand-town-names")
def get_new_zealand_town_names():

    query = request.args.get("q", "").strip().lower()
    if len(query) == 0:
        return jsonify([])

    return town_service.get_new_zealand_town_names(query)




