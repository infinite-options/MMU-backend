import requests
# import pytest
import json
import pymysql
import os
# import datetime
from datetime import datetime
from decimal import Decimal
from hashlib import sha256, sha512
from flask import jsonify, make_response
from flask_restful import Resource

from dotenv import load_dotenv
load_dotenv()

# endpointTest_CRON



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

ENDPOINT = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"
BASE_URL = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"
LOGIN_URL = "https://mrle52rri4.execute-api.us-west-1.amazonaws.com/dev/api/v2"

class test_endpoint_CLASS(Resource):
    def get(self):
        print("In GET of test_endpoint_CLASS")
        dt = datetime.today()
        response = {}

        # Insert temporary data into the database
        try:
            print("\n-------- Inserting temporary data into the MMU database --------")
            insert_user_query = """
                                        INSERT INTO `mmu`.`users` (`user_uid`, `user_first_name`, `user_last_name`, `user_email_id`, `user_phone_number`, `user_country`, `user_age`, `user_gender`, `user_height`, `user_sexuality`, `user_open_to`, `user_latitude`, `user_longitude`, `user_profile_bio`, `user_prefer_age_min`, `user_prefer_age_max`, `user_prefer_height_min`, `user_prefer_distance`, `user_prefer_gender`) VALUES ('100-000000', 'Test 0', 'Account', 'test0account@gmail.com', '0000000000', 'USA', '27', 'Male', '180', 'Straight', '[\"Straight\"]', '82.8628', '135.0000', 'Hi, Test 0 Account here!', '20', '30', '150', '100', 'Female');
                                    """
            
            with connect() as db:
                insert_user_query_response = db.execute(insert_user_query, cmd='post')

            print("\n------- Completed inserting temporary data into the MMU database --------")
            response['insert_temporary_data'] = 'Passed: Inserted into MMU database'

        except:
            response['insert_temporary_data'] = 'Failed: Insert data into MMU database'

        if response['insert_temporary_data'] != 'Passed: Inserted into MMU database':
            return response['insert_temporary_data']
        
        response['No of APIs tested'] = 0
        response['APIs running successfully'] = []
        response['APIs failing'] = []
        response['Error in running APIs'] = []

        json_headers = {
                    'Content-Type': 'application/json',
                } 

        try:
            user_uid = ""
            # -------- test all login APIs --------
            try:
                print("\nIn test all Login APIs")

                # -------- test Create Account API--------
                print("\n\tIn test Create Account API")
                create_account_payload = {
                        "email": "testapi@gmail.com",
                        "password": "123",
                        "phone_number": "(408) 679-4332"
                    }
                create_account_response = requests.post(LOGIN_URL + "/CreateAccount/MMU", data=json.dumps(create_account_payload), headers=json_headers)
                user_uid = create_account_response.json()['result'][0]['user_uid']
                # print("User UID: ", user_uid)
                if create_account_response.status_code == 200:
                    response['APIs running successfully'].append('Create Account API')
                else:
                    response['APIs failing'].append('Create Account API')
                response['No of APIs tested'] += 1

                # -------- test Account Salt API--------
                print("\n\tIn test Account Salt API")
                account_salt_payload = {
                    "email": "testapi@gmail.com",
                    "password": "123"
                }
                account_salt_response = requests.post(LOGIN_URL + "/AccountSalt/MMU", data=json.dumps(account_salt_payload), headers=json_headers)
                if account_salt_response.status_code == 200:
                    response['APIs running successfully'].append('Account Salt API')
                    account_salt_data = account_salt_response.json()
                    
                    # -------- test Login API--------
                    print("\n\tIn test Login API")
                    def getHash(value):
                        base = str(value).encode()
                        return sha256(base).hexdigest()
                    def createHash(password, salt):
                        return getHash(password+salt)
                    password = createHash(account_salt_payload["password"], account_salt_data["result"][0]["password_salt"])
                    login_payload = {
                        "email": "testapi@gmail.com",
                        "password": password
                    }
                    login_response = requests.post(LOGIN_URL + "/Login/MMU", data=json.dumps(login_payload), headers=json_headers)
                    if login_response.status_code == 200:
                        response['APIs running successfully'].append('Login API')
                    else:
                        response['APIs failing'].append('Login API')
                    
                else:
                    response['APIs failing'].append("Account Salt API")

                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Login APIs')
            
            finally:
                # -------- delete user data --------
                print("\n\tIn delete data from the Users table")
                print(f"\tDeleting {user_uid} from Users table\n")
                # with connect() as db:
                #     if user_uid != "":
                #         delete_user_uid_query = f'''DELETE FROM mmu.users
                #                 WHERE user_uid="{user_uid}"'''
                #         delete_user_uid_query_response = db.delete(delete_user_uid_query) 

            # -------- test all Userinfo APIs --------
            try:
                print('\nIn test all Userinfo APIs')

                # -------- test PUT Userinfo API --------
                print('\n\tIn test PUT Userinfo API')
                put_userinfo_payload = {
                    "user_uid": user_uid,
                    "user_email_id": "testapi@gmail.com",
                    "user_first_name": "Test 1",
                    "user_last_name": "Account",
                    "user_age": "26",
                    "user_gender": "Female",
                    "user_height": "160",
                    "user_sexuality": "Straight",
                    "user_open_to": '["Straight"]',
                    "user_latitude": "82.8628",
                    "user_longitude": "135.0000",
                    "user_prefer_age_min": "25",
                    "user_prefer_age_max": "30",
                    "user_prefer_height_min": "150",
                    "user_prefer_distance": "100",
                    "user_prefer_gender": "Male",
                    "user_date_interests": "Coffee,Lunch,Dinner",
                    "user_available_time": '[{"day": "Wednesday", "end_time": "06:00 PM", "start_time": "02:00 PM"}, {"day": "Sunday", "end_time": "04:00 PM", "start_time": "01:00 PM"}, {"day": "Saturday", "end_time": "10:00 PM", "start_time": "11:00 AM"}]'
                }
                put_userinfo_response = requests.put(ENDPOINT + "/userinfo", data=put_userinfo_payload)
                if put_userinfo_response.status_code == 200:
                    response['APIs running successfully'].append('Put UserInfo API')
                else:
                    response['APIs failing'].append('Put UserInfo API')
                response['No of APIs tested'] += 1

                # -------- test GET Userinfo API --------
                print("\n\tIn test GET UserInfo API")
                get_userinfo_response = requests.get(ENDPOINT + f"/userinfo/{user_uid}")
                get_userinfo_data = get_userinfo_response.json()['result'][0]
                if get_userinfo_data['user_first_name'] != "Test 1" and get_userinfo_data['user_last_name'] != "Account":
                    print("\n\t\tNot a match")
                if get_userinfo_response.status_code == 200:
                    response['APIs running successfully'].append('Get UserInfo API')
                else:
                    response['APIs failing'].append('Get UserInfo API')
                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Userinfo APIs')

            finally:
                pass           
            
            # -------- test all Matches APIs --------
            try:
                print("\nIn test GET Matches API")
                get_matches_response = requests.get(ENDPOINT + "/matches/100-000000")
                get_matches_data = get_matches_response.json()['result']
                for match in get_matches_data:
                    if match['user_uid'] == user_uid:
                        print("\t\tMatch Found")
                        break
                if get_matches_response.status_code == 200:
                    response['APIs running successfully'].append('Get Matches API')
                else:
                    response['APIs failing'].append('Get Matches API')
                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Matches API')

            finally:
                pass

            # -------- test all Likes APIs --------
            try:
                print("\nIn test all Likes APIs")

                # -------- test POST Likes API --------
                print("\n\tIn test POST Likes API")
                post_likes_payload = {
                    "liker_user_id": "100-000000",
                    "liked_user_id": user_uid
                }
                post_likes_response = requests.post(ENDPOINT + "/likes", data=post_likes_payload)
                if post_likes_response.status_code == 200:
                    response['APIs running successfully'].append('Post Likes API')
                else:
                    response['APIs failing'].append('Post Likes API')
                response['No of APIs tested'] += 1

                # -------- test GET Likes API --------
                print("\n\tIn test GET Likes API")
                get_likes_response = requests.get(ENDPOINT + "/likes/100-000000")
                get_likes_data = get_likes_response.json()['people_whom_you_selected']
                for like in get_likes_data:
                    if like['user_uid'] == user_uid:
                        print("\t\tLike Foound")
                        break
                if get_likes_response.status_code == 200:
                    response['APIs running successfully'].append('Get likes API')
                else:
                    response['APIs failing'].append('Get likes API')
                response['No of APIs tested'] += 1

                # -------- test DELETE Likes API --------
                print("\n\tIn test DELETE Likes API")
                delete_likes_payload = {
                    "liker_user_id": "100-000000",
                    "liked_user_id": user_uid
                }
                delete_likes_response = requests.delete(ENDPOINT + "/likes", data=delete_likes_payload)
                if delete_likes_response.status_code == 200:
                    response['APIs running successfully'].append('Delete Likes API')
                else:
                    response['APIs failing'].append('Delete Likes API')
                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Likes API')

            finally:
                pass

            # -------- test all Meet APIs --------
            meet_uid = ""
            try:
                print("\nIn test all Meet APIs")

                # -------- test POST Meet API --------
                print("\n\tIn test POST Meet API")
                post_meet_payload = {
                    "meet_user_id": "100-000000",
                    "meet_date_user_id": user_uid,
                    "meet_day": "Saturday",
                    "meet_time": "7:00 PM"
                }
                post_meet_response = requests.post(ENDPOINT + "/meet", data=post_meet_payload)
                meet_uid = post_meet_response.json()['meet_uid']
                if post_meet_response.status_code == 200:
                    response['APIs running successfully'].append('Post Meet API')
                else:
                    response['APIs failing'].append('Post Meet API')
                response['No of APIs tested'] += 1

                # -------- test PUT Meet API --------
                print("\n\tIn test PUT Meet API")
                put_meet_payload = {
                    "meet_uid": meet_uid,
                    "meet_time": "8:00 PM"
                }
                put_meet_response = requests.put(ENDPOINT + "/meet", data=put_meet_payload)
                if put_meet_response.status_code == 200:
                    response['APIs running successfully'].append('PUT Meet API')
                else:
                    response['APIs failing'].append('PUT Meet API')
                response['No of APIs tested'] += 1

                # -------- test GET Meet API --------
                print("\n\tIn test GET Meet API")
                get_meet_response = requests.get(ENDPOINT + "/meet/100-000000")
                get_meet_data = get_meet_response.json()['result']
                for meet in get_meet_data:
                    if meet['meet_uid'] == meet_uid and meet['meet_time'] == "8:00 PM":
                        print("\t\tMeet Found")
                        break
                if get_meet_response.status_code == 200:
                    response['APIs running successfully'].append('Get Meet API')
                else:
                    response['APIs failing'].append('Get Meet API')
                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Meet API')

            finally:
                print("\n\tIn delete data from the Meet table")
                print(f"\tDeleting meet_uid: {meet_uid} from Meet table\n")
                if meet_uid != "":
                    with connect() as db:
                        delete_meet_uid_query = f'''DELETE FROM mmu.meet
                                                    WHERE meet_uid="{meet_uid}"'''
                        delete_meet_uid_query_response = db.delete(delete_meet_uid_query)
            
            # -------- test all Messages APIs --------
            message_uid = ""
            try:
                print("\nIn test all Messages APIs")

                # -------- test POST Messages API --------
                print("\n\tIn test POST Messages API")
                post_messages_payload = {
                    "sender_id": "100-000000",
                    "receiver_id": user_uid,
                    "message_content": "Hi, How are you?"
                }
                post_messages_response = requests.post(ENDPOINT + "/messages", data=json.dumps(post_messages_payload), headers=json_headers)
                message_uid = post_messages_response.json()['message_uid']
                if post_messages_response.status_code == 200:
                    response['APIs running successfully'].append('Post Messages API')
                else:
                    response['APIs failing'].append('Post Messages API')
                response['No of APIs tested'] += 1

                # -------- test GET Messages API --------
                print("\n\tIn test GET Messages API")
                get_messages_response = requests.get(ENDPOINT + f"/messages?sender_id=100-000000&receiver_id={user_uid}")
                if get_messages_response.status_code == 200:
                    response['APIs running successfully'].append('Get Messages API')
                else:
                    response['APIs failing'].append('Get Messages API')
                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Messages API')

            finally:
                print("\n\tIn delete data from the Messages table")
                print(f"\tDeleting message_uid: {message_uid} from the Messages table\n")
                if message_uid != "":
                    with connect() as db:
                        delete_message_uid_query = f'''DELETE FROM mmu.messages
                                                    WHERE message_uid="{message_uid}"'''
                        delete_message_uid_query_response = db.delete(delete_message_uid_query)

            # -------- test all Lists APIs --------
            try:
                print("\nIn test all Lists APIs")

                print("\n\tIn test GET Lists API")
                get_lists_response = requests.get(ENDPOINT + "/lists?list_category=activities")
                if get_lists_response.status_code == 200:
                    response['APIs running successfully'].append('Get Lists API')
                else:
                    response['APIs failing'].append('Get Lists API')
                response['No of APIs tested'] += 1

            except:
                response['Error in running APIs'].append('Lists API')

        except:
            response["cron fail"] = {'message': f'MySpace Test API CRON Job failed for {dt}' ,'code': 500}

        try:
            print("\n-------- Deleting temporary data from the MMU database --------")
            delete_user_query = """
                                        DELETE FROM mmu.users
                                        WHERE user_uid = "100-000000";
                                    """
            
            with connect() as db:
                delete_user_query_response = db.delete(delete_user_query)
                
                if user_uid != "":
                    delete_user_uid_query = f'''DELETE FROM mmu.users
                            WHERE user_uid="{user_uid}"'''
                    delete_user_uid_response = db.delete(delete_user_uid_query)
                
            print("\n-------- Completed deleting temporary data from the MMU database --------\n")
            response['delete_temporary_data'] = 'Passed: Deleted from MMU database'
            
        except:
            response['delete_temporary_data'] = 'Failed: Delete data from MMU database'

        return response



# ---------------- Testing Starts from here --------------------

# # ******** Userinfo ******** Completed
# def test_get_userinfo():

#     response = requests.get(BASE_URL + "/userinfo/100-000001")

#     assert response.status_code == 200

# def test_put_userinfo():

#     payload = {
#             "user_uid": "100-000006",
#             "user_email_id": "mollysymonds@gmail.com",
#             "user_first_name": "Molly",
#             "user_last_name": "Symonds",
#             "user_notification_preference": "True",
#             "user_location_service": "True",
#             "user_date_interests": "Coffee,Lunch,Dinner",
#             "user_available_time": '[{"day": "Wednesday", "end_time": "06:00 PM", "start_time": "02:00 PM"}, {"day": "Sunday", "end_time": "04:00 PM", "start_time": "01:00 PM"}, {"day": "Saturday", "end_time": "10:00 PM", "start_time": "11:00 AM"}]'
#             }

#     response = requests.put(BASE_URL + "/userinfo", data=payload)

#     assert response.status_code == 200

# # def test_post_userinfo():
# #     payload = {
# #             "user_email_id": "qwerty@gmail.com"
# #             }
# #     response = requests.post(BASE_URL + "/userinfo", data=payload)

# #     delete = response.json()
# #     print(delete)
# #     with connect() as db:
# #         query = f'''DELETE FROM mmu.users
# #                 WHERE user_uid="{delete['user_uid']}"'''

# #         result = db.delete(query)

# #         print(result)
    
# #     assert response.status_code == 200

# # ******** Likes ******** Completed
# def test_get_likes():

#     response = requests.get(BASE_URL + "/likes/100-000001")

#     assert response.status_code == 200

# def test_post_likes():

#     payload = {
#         "liker_user_id": "100-000001",
#         "liked_user_id": "100-000004"
#     }

#     response = requests.post(BASE_URL + "/likes", data=payload)

#     assert response.status_code == 200

# def test_delete_likes():

#     payload = {
#         "liker_user_id": "100-000001",
#         "liked_user_id": "100-000004"
#     }

#     response = requests.delete(BASE_URL + "/likes", data=payload)

#     assert response.status_code == 200

# # ******** Meet ******** Completed
# def test_get_meet():

#     response = requests.get(BASE_URL + "/meet/100-000001")

#     assert response.status_code == 200

# def test_post_meet():

#     payload = {
#         "meet_user_id": "100-000001",
#         "meet_date_user_id": "100-000004",
#         "meet_day": "Saturday",
#         "meet_time": "7:00 AM"
#     }
    
#     response = requests.post(BASE_URL + "/meet", data=payload)

#     delete = response.json()

#     with connect() as db:
#         query = f'''DELETE FROM mmu.meet
#                 WHERE meet_uid="{delete['meet_uid']}"'''

#         result = db.delete(query)

#     assert response.status_code == 200

# # ******** Lists ******** Completed
# def test_get_lists():

#     response = requests.get(BASE_URL + "/lists?list_category=activities")

#     assert response.status_code == 200

# # ******** Messages ******** Completed
# def test_get_messages():

#     response = requests.get(BASE_URL + "/messages?sender_id=100-000001&receiver_id=100-000007")

#     assert response.status_code == 200

# def test_post_message():

#     payload = {
#         "sender_id": "100-000001",
#         "receiver_id": "100-000002",
#         "message_content": "Hi, There"
#     }

#     headers = {
#         'Content-Type': 'application/json'
#     }
    
#     response = requests.post(BASE_URL + "/messages", data=json.dumps(payload), headers=headers)
    
#     delete = response.json()

#     with connect() as db:
#         query = f'''DELETE FROM mmu.messages
#                 WHERE message_uid="{delete['message_uid']}"'''

#         result = db.delete(query)

#     assert response.status_code == 200

# # ******** Matches ******** Completed
# def test_get_matches():
    
#     response = requests.get(BASE_URL + "/matches/100-000001")

#     assert response.status_code == 200

# # ******** Login ******** Completed
# user_uid = ""

# def test_create_account():
#     payload = {
#             "email": "testapi@gmail.com",
#             "password": "123",
#             "phone_number": "(408) 679-4332"
#         }

#     headers = {
#         'Content-Type': 'application/json'
#     }

#     response = requests.post(LOGIN_URL + "/CreateAccount/MMU", data=json.dumps(payload), headers=headers)
#     delete = response.json()

#     global user_uid
#     user_uid = delete['result'][0]['user_uid']

#     assert response.status_code == 200

# def test_email_login():
#     payload = {
#         "email": "testapi@gmail.com",
#         "password": "123"
#     }
#     headers = {
#         'Content-Type': 'application/json'
#     }

#     response = requests.post(LOGIN_URL + "/AccountSalt/MMU", data=json.dumps(payload), headers=headers)

#     method = response.json()

#     assert response.status_code == 200

#     print(' Now In Login Part')

#     def getHash(value):
#         base = str(value).encode()
#         return sha256(base).hexdigest()
    
#     def createHash(password, salt):
#         return getHash(password+salt)
    
#     password = createHash(payload["password"], method["result"][0]["password_salt"])

#     payload = {
#         "email": "testapi@gmail.com",
#         "password": password
#     }
#     response = requests.post(LOGIN_URL + "/Login/MMU", data=json.dumps(payload), headers=headers)

#     global user_uid
#     with connect() as db:
#         query = f'''DELETE FROM mmu.users
#                 WHERE user_uid="{user_uid}"'''

#         result = db.delete(query)
    
#     assert response.status_code == 200

# # ******** Announcements ******** Completed
# def test_get_announcements():
    # response = requests.get(BASE_URL + "/announcements/100-000002")

    # assert response.status_code == 200