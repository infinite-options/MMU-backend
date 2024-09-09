from flask import request, abort 
from flask_restful import Resource
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename


from data import connect, uploadImage, s3
import json
import os
import ast

# get new id (primary key)
def get_new_unique_id(table, col):
    print(' in get ne unique id')
    with connect() as db:
        query = f'''SELECT {col} FROM {table} ORDER BY user_uid DESC LIMIT 1;'''
        response = db.execute(query)

    last_unique_id = response['result'][0][col]

    if last_unique_id:
        last_id = last_unique_id
        id_list = last_id.split('-')
        last_int = int(id_list[1])
        new_int = last_int + 1
        new_unique_id = "{}-{:06d}".format(id_list[0], new_int)
    
    return new_unique_id

class UserInfo(Resource):
    
    def get(self, user_id):
        print("In UserInfo GET")

        with connect() as db:
            userQuery = db.select('users', {'user_uid': user_id})
            # userQuery = db.execute('''
            #                     SELECT * FROM mmu.users''')

        if userQuery['code'] == 200 and int(len(userQuery['result']) > 0):                
            return userQuery
        else:                
            abort(404, description="User not found")
    
    def post(self):
        print("In UserInfo POST")

        new_user_uid = get_new_unique_id('users', 'user_uid')
        with connect() as db:
            payload = request.form.to_dict()
            payload['user_uid'] = new_user_uid
            print(payload)

            userQuery = db.insert('users', payload)
        
        return userQuery

    def put(self, user_id):
        print("In UserInfo PUT")

        with connect() as db:
            payload = request.form.to_dict()

            userQuery = db.update('users', {'user_uid': user_id}, payload)
        
        return userQuery