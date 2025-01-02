from flask import request
from flask_restful import Resource

from data import connect


class List(Resource):
    def get(self):
        response = {}
        where = request.args.to_dict()
        with connect() as db:
            response = db.select('lists', where)
        
        # Filter the `result` list to exclude entries with `list_item` as None
        if "result" in response and isinstance(response["result"], list):
            response["result"] = [
                item for item in response["result"] if item.get("list_item") is not None
            ]

        return response
