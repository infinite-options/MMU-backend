import requests
import pytest
import json
import pymysql
import os
import datetime
from decimal import Decimal
from hashlib import sha256, sha512
from flask import jsonify, make_response

from dotenv import load_dotenv
load_dotenv()

# endpointTest_CRON

BASE_URL = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"
LOGIN_URL = "https://mrle52rri4.execute-api.us-west-1.amazonaws.com/dev/api/v2"

# Connect to MySQL database (API v2)
def connect():

    print("Trying to connect to RDS (API v2)...")

    try:
        conn = pymysql.connect(
            host=os.getenv('RDS_HOST'),
            user=os.getenv('RDS_USER'),
            port=int(os.getenv('RDS_PORT')),
            passwd=os.getenv('RDS_PW'),
            db=os.getenv('RDS_DB'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        print("Successfully connected to RDS. (API v2)")
        return DatabaseConnection(conn)
    except:
        print("Could not connect to RDS. (API v2)")
        raise Exception("RDS Connection failed. (API v2)")


# Disconnect from MySQL database (API v2)
def disconnect(conn):
    try:
        conn.close()
        print("Successfully disconnected from MySQL database. (API v2)")
    except:
        print("Could not properly disconnect from MySQL database. (API v2)")
        raise Exception("Failure disconnecting from MySQL database. (API v2)")


# Serialize JSON
def serializeJSON(unserialized):
    # print("In serialized JSON: ", unserialized, type(unserialized))
    if type(unserialized) == list:
        # print("in list")
        serialized = []
        for entry in unserialized:
            # print("entry: ", entry)
            serializedEntry = serializeJSON(entry)
            serialized.append(serializedEntry)
        # print("Serialized: ", serialized)
        return serialized
    elif type(unserialized) == dict:
        # print("in dict")
        serialized = {}
        for entry in unserialized:
            serializedEntry = serializeJSON(unserialized[entry])
            serialized[entry] = serializedEntry
        return serialized
    elif type(unserialized) == datetime.datetime:
        # print("in date")
        return str(unserialized)
    elif type(unserialized) == bytes:
        # print("in bytes")
        return str(unserialized)
    elif type(unserialized) == Decimal:
        # print("in Decimal")
        return str(unserialized)
    else:
        # print("in else")
        return unserialized

class DatabaseConnection:
    def __init__(self, conn):
        self.conn = conn

    def disconnect(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def execute(self, sql, args=[], cmd='get'):
        print("In execute.  SQL: ", sql)
        print("In execute.  args: ",args)
        print("In execute.  cmd: ",cmd)
        response = {}
        try:
            with self.conn.cursor() as cur:
                # print('IN EXECUTE')
                if len(args) == 0:
                    cur.execute(sql)
                else:
                    cur.execute(sql, args)
                formatted_sql = f"{sql} (args: {args})"                    

                if 'get' in cmd:
                    print('IN GET')
                    result = cur.fetchall()
                    # print("After result: ", result, type(result))
                    result = serializeJSON(result)
                    # print("After serialization: ", result)
                    # print('RESULT GET')
                    response['message'] = 'Successfully executed SQL query'
                    response['code'] = 200
                    response['result'] = result
                    # print('RESPONSE GET')

                elif 'post' in cmd:
                    # print('IN POST')
                    self.conn.commit()
                    response['message'] = 'Successfully committed SQL query'
                    response['code'] = 200
                    response['change'] = str(cur.rowcount) + " rows affected"
                    # print('RESPONSE POST')

        except pymysql.MySQLError as e:
            message = str(e)
            
            if 'Unknown column' in message:
                column_name = message.split("'")[1]
                error_message = f"Error: The column '{column_name}' does not exist"
            else:
                error_message = "An error occured in database: " + message
            
            return make_response(jsonify({
                'code': 400,
                'message': error_message
            }), 400)
        
        except Exception as e:
            print('ERROR', e)
            response['message'] = 'Error occurred while executing SQL query'
            response['code'] = 500
            response['error'] = e
            print('RESPONSE ERROR', response)
        return response

    def select(self, tables, where={}, cols='*', exact_match = True, limit = None):
        response = {}
        try:
            # print("In Select")
            sql = f'SELECT {cols} FROM {tables}'
            # print(sql)
            for i, key in enumerate(where.keys()):
                # print(i, key)
                if i == 0:
                    sql += ' WHERE '
                if exact_match:
                    sql += f'{key} = %({key})s'
                else:
                    sql += f"{key} LIKE CONCAT('%%', %({key})s ,'%%')"
                if i != len(where.keys()) - 1:
                    sql += ' AND '
            if limit:
                sql += f' LIMIT {limit}'
            response = self.execute(sql, where, 'get')
        except Exception as e:
            print(e)
        return response

    def insert(self, table, object):
        response = {}
        try:
            sql = f'INSERT INTO {table} SET '
            for i, key in enumerate(object.keys()):
                sql += f'{key} = %({key})s'
                if i != len(object.keys()) - 1:
                    sql += ', '
            # print(sql)
            # print(object)
            response = self.execute(sql, object, 'post')
        except Exception as e:
            print(e)
        return response

    def update(self, table, primaryKey, object):
        # print("\nIn Update: ", table, primaryKey, object)
        response = {}
        try:
            sql = f'UPDATE {table} SET '
            # print("SQL :", sql)
            # print(object.keys())
            for i, key in enumerate(object.keys()):
                # print("update here 0 ", key)
                sql += f'{key} = %({key})s'
                # print("sql: ", sql)
                if i != len(object.keys()) - 1:
                    sql += ', '
            sql += f' WHERE '
            # print("Updated SQL: ", sql)
            # print("Primary Key: ", primaryKey, type(primaryKey))
            for i, key in enumerate(primaryKey.keys()):
                # print("update here 1")
                sql += f'{key} = %({key})s'
                object[key] = primaryKey[key]
                # print("update here 2", key, primaryKey[key])
                if i != len(primaryKey.keys()) - 1:
                    # print("update here 3")
                    sql += ' AND '
            print("SQL Query: ", sql, object)
            response = self.execute(sql, object, 'post')
            # print("Response: ", response)
        except Exception as e:
            print(e)
        return response

    def delete(self, sql):
        response = {}
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)

                self.conn.commit()
                response['message'] = 'Successfully committed SQL query'
                response['code'] = 200
                # response = self.execute(sql, 'post')
        except Exception as e:
            print(e)
        return response

    def call(self, procedure, cmd='get'):
        response = {}
        try:
            sql = f'CALL {procedure}()'
            response = self.execute(sql, cmd=cmd)
        except Exception as e:
            print(e)
        return response


# ---------------- Testing Starts from here --------------------

# ******** Userinfo ******** Completed
def test_get_userinfo():

    response = requests.get(BASE_URL + "/userinfo/100-000001")

    assert response.status_code == 200

def test_put_userinfo():

    payload = {
            "user_uid": "100-000006",
            "user_email_id": "mollysymonds@gmail.com",
            "user_first_name": "Molly",
            "user_last_name": "Symonds",
            "user_notification_preference": "True",
            "user_location_service": "True",
            "user_date_interests": "Coffee,Lunch,Dinner",
            "user_available_time": '[{"day": "Wednesday", "end_time": "06:00 PM", "start_time": "02:00 PM"}, {"day": "Sunday", "end_time": "04:00 PM", "start_time": "01:00 PM"}, {"day": "Saturday", "end_time": "10:00 PM", "start_time": "11:00 AM"}]'
            }

    response = requests.put(BASE_URL + "/userinfo", data=payload)

    assert response.status_code == 200

# def test_post_userinfo():
#     payload = {
#             "user_email_id": "qwerty@gmail.com"
#             }
#     response = requests.post(BASE_URL + "/userinfo", data=payload)

#     delete = response.json()
#     print(delete)
#     with connect() as db:
#         query = f'''DELETE FROM mmu.users
#                 WHERE user_uid="{delete['user_uid']}"'''

#         result = db.delete(query)

#         print(result)
    
#     assert response.status_code == 200

# ******** Likes ******** Completed
def test_get_likes():

    response = requests.get(BASE_URL + "/likes/100-000001")

    assert response.status_code == 200

def test_post_likes():

    payload = {
        "liker_user_id": "100-000001",
        "liked_user_id": "100-000004"
    }

    response = requests.post(BASE_URL + "/likes", data=payload)

    assert response.status_code == 200

def test_delete_likes():

    payload = {
        "liker_user_id": "100-000001",
        "liked_user_id": "100-000004"
    }

    response = requests.delete(BASE_URL + "/likes", data=payload)

    assert response.status_code == 200

# ******** Meet ******** Completed
def test_get_meet():

    response = requests.get(BASE_URL + "/meet/100-000001")

    assert response.status_code == 200

def test_post_meet():

    payload = {
        "meet_user_id": "100-000001",
        "meet_date_user_id": "100-000004",
        "meet_day": "Saturday",
        "meet_time": "7:00 AM"
    }
    
    response = requests.post(BASE_URL + "/meet", data=payload)

    delete = response.json()

    with connect() as db:
        query = f'''DELETE FROM mmu.meet
                WHERE meet_uid="{delete['meet_uid']}"'''

        result = db.delete(query)

    assert response.status_code == 200

# ******** Lists ******** Completed
def test_get_lists():

    response = requests.get(BASE_URL + "/lists?list_category=activities")

    assert response.status_code == 200

# ******** Messages ******** Completed
def test_get_messages():

    response = requests.get(BASE_URL + "/messages?sender_id=100-000001&receiver_id=100-000007")

    assert response.status_code == 200

def test_post_message():

    payload = {
        "sender_id": "100-000001",
        "receiver_id": "100-000002",
        "message_content": "Hi, There"
    }

    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(BASE_URL + "/messages", data=json.dumps(payload), headers=headers)
    
    delete = response.json()

    with connect() as db:
        query = f'''DELETE FROM mmu.messages
                WHERE message_uid="{delete['message_uid']}"'''

        result = db.delete(query)

    assert response.status_code == 200

# ******** Matches ******** Completed
def test_get_matches():
    
    response = requests.get(BASE_URL + "/matches/100-000001")

    assert response.status_code == 200

# ******** Login ******** Completed
user_uid = ""

def test_create_account():
    payload = {
            "email": "testapi@gmail.com",
            "password": "123",
            "phone_number": "(408) 679-4332"
        }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(LOGIN_URL + "/CreateAccount/MMU", data=json.dumps(payload), headers=headers)
    delete = response.json()

    global user_uid
    user_uid = delete['result'][0]['user_uid']

    assert response.status_code == 200

def test_email_login():
    payload = {
        "email": "testapi@gmail.com",
        "password": "123"
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(LOGIN_URL + "/AccountSalt/MMU", data=json.dumps(payload), headers=headers)

    method = response.json()

    assert response.status_code == 200

    print(' Now In Login Part')

    def getHash(value):
        base = str(value).encode()
        return sha256(base).hexdigest()
    
    def createHash(password, salt):
        return getHash(password+salt)
    
    password = createHash(payload["password"], method["result"][0]["password_salt"])

    payload = {
        "email": "testapi@gmail.com",
        "password": password
    }
    response = requests.post(LOGIN_URL + "/Login/MMU", data=json.dumps(payload), headers=headers)

    global user_uid
    with connect() as db:
        query = f'''DELETE FROM mmu.users
                WHERE user_uid="{user_uid}"'''

        result = db.delete(query)
    
    assert response.status_code == 200

# ******** Announcements ******** Completed
def test_get_announcements():
    response = requests.get(BASE_URL + "/announcements/100-000002")

    assert response.status_code == 200