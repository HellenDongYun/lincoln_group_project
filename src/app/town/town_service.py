import requests
from flask import jsonify

OPEN_DATA_SOFT_API_URL = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/geonames-all-cities-with-a-population-1000/records"


class TownService:

    def get_new_zealand_town_names(self, query: str):

        if len(query) == 0:
            return jsonify([])

        try:
            params = {
                "select": "name",
                "refine": "cou_name_en:'New Zealand'",
                "where": f"search(name, '{query}')",
                "order_by": "name ASC",
                "limit": 20,
            }

            response = requests.get(OPEN_DATA_SOFT_API_URL, params=params, timeout=8.0)
            response.raise_for_status()
            results = response.json().get("results", [])

            print(results)

            names = sorted(
                {town.get("name", "").strip() for town in results if isinstance(town.get("name"), str)},
                key=str.lower
            )

            return jsonify(names)

        except Exception as e:
            print(e)
            return jsonify([])
