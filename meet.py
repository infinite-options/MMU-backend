from flask import request, abort, make_response, jsonify
from flask_restful import Resource

from data import connect

class Meet(Resource):

    def get(self, user_id):
        print("In Meet GET")

        with connect() as db:
            meetQuery = db.select('meet', {'meet_user_id': user_id})

        if meetQuery['code'] == 200 and int(len(meetQuery['result']) > 0):                
            return meetQuery
        else:                
            abort(404, description="No data information availabe for the User")


    def post(self):
        print("In Meet POST")

        try:
            with connect() as db:
                new_user_uid = db.call(procedure='new_meet_uid')

                payload = request.form.to_dict()
                payload['meet_uid'] = new_user_uid['result'][0]['new_id']

                meetQuery = db.insert('meet', payload)
                meetQuery['meet_uid'] = new_user_uid['result'][0]['new_id']

            return meetQuery
        
        except Exception as e:
            return {"error": e}
    
    def put(self):
        print("In Meet PUT")

        with connect() as db:
            payload = request.form.to_dict()
            meet_uid = payload.pop('meet_uid')
            key = {'meet_uid': meet_uid}

            meetQuery = db.update('meet', key, payload)

        return meetQuery