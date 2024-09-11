from flask import request, abort, make_response, jsonify
from flask_restful import Resource
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename


from data import connect
from s3 import uploadImage, s3, processImage
import json
import os
import ast

class UserInfo(Resource):
    
    def get(self, user_id):
        print("In UserInfo GET")

        with connect() as db:
            userQuery = db.select('users', {'user_uid': user_id})

        if userQuery['code'] == 200 and int(len(userQuery['result']) > 0):                
            return userQuery
        else:                
            abort(404, description="User not found")
    
    def post(self):
        print("In UserInfo POST")
        
        try:
            with connect() as db:
                new_user_uid = db.call(procedure='new_user_uid')
                print(new_user_uid)
                payload = request.form.to_dict()
                payload['user_uid'] = new_user_uid['result'][0]['new_id']
                print(payload)
                parameter = {'user_email_id': payload['user_email_id']}
                email_exists = db.select('users', where=parameter)
                
                if email_exists['result']:
                    return make_response(jsonify({
                        'code': 409,
                        'name': 'Conflict',
                        'description': 'Email already exists'
                    }), 409)

                userQuery = db.insert('users', payload)
                userQuery['user_uid'] = new_user_uid['result'][0]['new_id']
            
            return userQuery
        
        except Exception as e:
            return {"error": e}

    def put(self):
        print("In UserInfo PUT")

        with connect() as db:
            payload = request.form.to_dict()
            user_uid = payload.pop('user_uid')
            key = {'user_uid': user_uid}

            email = db.select('users', key, cols='user_email_id')
            if email['result'][0]['user_email_id'] != payload['user_email_id']:
                return make_response(jsonify({
                        'code': 400,
                        'name': 'Bad Request',
                        'description': "Email-id doesn't match with the email-id linked with provided user_uid"
                    }), 400)


            # Process Images
            processImage(key, payload)
            userQuery = db.update('users', key, payload)
        
        # return userQuery
        return userQuery