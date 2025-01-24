from flask import request, abort, make_response, jsonify
from flask_restful import Resource
import requests

from data import connect

from announcements import Announcements

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
                print(new_user_uid)

                payload = request.form.to_dict()
                payload['meet_uid'] = new_user_uid['result'][0]['new_id']
                print(payload)

                meetQuery = db.insert('meet', payload)
                print(meetQuery)
                meetQuery['meet_uid'] = new_user_uid['result'][0]['new_id']
                print(meetQuery['meet_uid'])

                userQuery = db.execute(f'''SELECT user_first_name FROM mmu.users WHERE user_uid = "{payload['meet_user_id']}"''', cmd='get')
                print(userQuery)
                userName = userQuery['result'][0]['user_first_name']

                data = {
                    "announcement_title": "New Meet",
                    "announcement_message": f"You are invited to meet {userName}",
                    "announcement_mode": "Meet",
                    "announcement_receiver": [f"{payload['meet_date_user_id']}"]
                }

                try:
                    # response = requests.post("http://127.0.0.1:4000/announcements", json=data)
                    response = Announcements().post(data)
                    print(response)
                    meetQuery['announcements added'] = "TRUE"
                except:
                    return jsonify({
                        "message": "Error in anouncement API (from Meet)",
                        "code": 400
                    })

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