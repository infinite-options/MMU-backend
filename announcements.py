from flask import request, jsonify, make_response
from flask_restful import Resource
from datetime import datetime, date, timedelta, timezone
from data import connect

class Announcements(Resource):

    def get(self, user_id):
        
        with connect() as db:
            response = db.select('announcements', where={"announcement_receiver": user_id})

        return response

    def post(self, payload):
        print("In Announcements POST")
        response = {}
        # payload = request.get_json()

        if isinstance(payload["announcement_receiver"], list):
            receivers = payload["announcement_receiver"]
        else:
            receivers = [payload["announcement_receiver"]]

        with connect() as db:

            for i in range(len(receivers)):
                new_announcement_uid = db.call(procedure='new_announcement_uid')

                newRequest = {}
                newRequest['announcement_uid'] = new_announcement_uid['result'][0]['new_id']
                newRequest['announcement_title'] = payload['announcement_title']
                newRequest['announcement_message'] = payload['announcement_message']
                newRequest['announcement_mode'] = payload['announcement_mode']
                newRequest['announcement_receiver'] = receivers[i]

                current_datetime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S") #datetime.now().strftime("%m-%d-%Y %H:%M:%S")

                newRequest['announcement_date'] = current_datetime
                newRequest['announcement_app'] = "1"

                response['App'] = db.insert('announcements', newRequest)
        
        return response

    def put(self):
        print("In Announcements PUT")

        response = {}
        payload = request.get_json()

        if 'announcement_uid' in payload and payload['announcement_uid']:

            current_datetime = current_datetime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

            payload['announcement_read'] = current_datetime

            i = 0

            for each in payload['announcement_uid']:

                if each in {None, '', 'null'}:
                    response["Bad Data"] = "TRUE"
            
                else:
                    key = {'announcement_uid': each}

                    with connect() as db:
                        response = db.update('announcements', key, payload)
                        i = i + 1
                    
                    response["rows affected"] = i

        else:
            response['message'] = 'No UID in payload'
        
        return response