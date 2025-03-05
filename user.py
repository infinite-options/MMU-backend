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
    
    # def get(self, user_id):
    #     print("In UserInfo GET")

    #     with connect() as db:
    #         userQuery = db.select('users', {'user_uid': user_id})

    #     if userQuery['code'] == 200 and int(len(userQuery['result']) > 0):                
    #         return userQuery
    #     else:                
    #         abort(404, description="User not found")

    # def get(self, user_id):
    #     print("In UserInfo GET")

    #     # Reverse mapping for openTo
    #     reverse_openTo_mapping = {'Men (TG)': 'Men (transgender)', 'Women (TG)': 'Women (transgender)'}

    #     with connect() as db:
    #         userQuery = db.select('users', {'user_uid': user_id})

    #     if userQuery['code'] == 200 and int(len(userQuery['result']) > 0):
    #         # Perform reverse mapping on 'openTo' if present in the result
    #         for user in userQuery['result']:
    #             # Reverse mapping for 'openTo'
    #             if 'openTo' in user:
    #                 user['openTo'] = [reverse_openTo_mapping.get(item, item) for item in user['openTo']]

    #         return userQuery
    #     else:
    #         abort(404, description="User not found")

    def get(self, user_id):
        print("In UserInfo GET")

        # Reverse mapping for openTo
        reverse_openTo_mapping = {'Men (TG)': 'Men (transgender)', 'Women (TG)': 'Women (transgender)'}

        with connect() as db:
            # print(user_id)
            userQuery = db.select('users', {'user_uid': user_id})
            # print("Query Result: ", userQuery)

        if userQuery['code'] == 200 and int(len(userQuery['result']) > 0):
            # Perform reverse mapping on 'openTo' if present in the result
            for user in userQuery['result']:
                # Parse 'user_open_to' if it's stored as a string and reverse map values
                # if 'user_open_to' in user:
                if 'user_open_to' in user and user['user_open_to']:
                    # Parse the JSON string back into a list
                    open_to_list = json.loads(user['user_open_to'])
                    
                    # Reverse mapping for 'openTo'
                    user['user_open_to'] = [reverse_openTo_mapping.get(item, item) for item in open_to_list]
                    
                    # Convert the list back into a JSON string before sending to frontend
                    user['user_open_to'] = json.dumps(user['user_open_to'])
                else:
                    user['user_open_to'] = '[]'

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

                # Map singular to plural for a new column
                identity_mapping = {'Man': 'Men', 'Woman': 'Women', 'Man (transgender)': 'Men (TG)', 'Woman (transgender)': 'Women (TG)'}
                payload['user_identity_plural'] = identity_mapping.get(payload.get('user_identity'), payload.get('user_identity'))


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
        response = {}

        payload = request.form.to_dict()
        print("Payload: ", payload)

        # Verify uid has been included in the data
        if payload.get('user_uid') in {None, '', 'null'}:
            print("No user_uid")
            raise BadRequest("Request failed, no UID in payload.")
        
        # Verify email included in the data matches email in database - not sure I need this
        # email = db.select('users', key, cols='user_email_id')
        # if email['result'][0]['user_email_id'] != payload['user_email_id']:
        #     return make_response(jsonify({
        #             'code': 400,
        #             'name': 'Bad Request',
        #             'description': "Email-id doesn't match with the email-id linked with provided user_uid"
        #         }), 400)
        
         # property_uid = payload.get('property_uid')
        key = {'user_uid': payload.pop('user_uid')}
        print("User Key: ", key)

         # --------------- PROCESS IMAGES ------------------

        processImage(key, payload)
        # print("Payload after processImage function: ", payload, type(payload))
        
        # --------------- PROCESS IMAGES ------------------


        with connect() as db:
            
           

            # Map singular to plural for a new column
            identity_mapping = {'Man': 'Men', 'Woman': 'Women', 'Man (transgender)': 'Men (TG)', 'Woman (transgender)': 'Women (TG)'}

            # Map 'user_identity' if it's present in the payload
            if payload.get('user_identity'):
                payload['user_identity_plural'] = identity_mapping.get(payload.get('user_identity'), payload.get('user_identity'))

            
            # # Map transgender to TG
            # openTo_mapping = {'Men (transgender)': 'Men (TG)', 'Women (transgender)': 'Women (TG)'}

            # # Check if 'openTo' is present in the payload and map values accordingly
            # if payload.get('openTo'):
            #     payload['openTo'] = [openTo_mapping.get(item, item) for item in payload['openTo']]

            # print(payload)



            # Map transgender to TG
            openTo_mapping = {'Men (transgender)': 'Men (TG)', 'Women (transgender)': 'Women (TG)'}

            # Check if 'user_open_to' is present in the payload and map values accordingly
            if payload.get('user_open_to'):
                # Convert the string to a list
                open_to_list = json.loads(payload['user_open_to'])
                
                # Map values in the list
                payload['user_open_to'] = [openTo_mapping.get(item, item) for item in open_to_list]

                # Convert the list back into a JSON string
                payload['user_open_to'] = json.dumps(payload['user_open_to'])

            print("Checking Inputs: ", key, payload)
            userQuery = db.update('users', key, payload)
        
        return userQuery