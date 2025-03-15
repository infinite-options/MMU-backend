# MEET ME UP BACKEND PYTHON FILE
# https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev/<enter_endpoint_details>


# To run program:  python3 mmu_api.py

# README:  if conn error make sure password is set properly in RDS PASSWORD section
# README:  Debug Mode may need to be set to False when deploying live (although it seems to be working through Zappa)
# README:  if there are errors, make sure you have all requirements are loaded
# pip3 install -r requirements.txt
# import eventlet
# eventlet.monkey_patch()

print("-------------------- New Program Run --------------------")

# SECTION 1:  IMPORT FILES AND FUNCTIONS
# from users import UserInfo
from lists import List
from user import UserInfo, AppleLogin
from matches import Match
from meet import Meet
from likes import Likes
from messages import Messages, get_conversation_id
from data import connect, disconnect
from announcements import Announcements
from password import Password
from test_api import test_endpoint_CLASS
from s3 import uploadImage, s3, S3Video_presigned_url

import os
import boto3
import requests
from hashlib import sha256
import json
# import time
# import sys
import pymysql
# import requests
import pytz
# import stripe
# import urllib.request
# import base64
# import math
# import string
# import random
# import hashlib
# import binascii
# import csv
# import re  # regex

from dotenv import load_dotenv
# from datetime import datetime as dt
# from datetime import timezone as dtz
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, render_template, url_for, redirect
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message  # used for email
# from flask_jwt_extended import JWTManager
from pytz import timezone as ptz  # Not sure what the difference is
# from decimal import Decimal
# from hashlib import sha512
from twilio.rest import Client
# from oauth2client import GOOGLE_REVOKE_URI, GOOGLE_TOKEN_URI, client
# from google_auth_oauthlib.flow import InstalledAppFlow
# from urllib.parse import urlparse
# from io import BytesIO
# from dateutil.relativedelta import relativedelta
# from dateutil.relativedelta import *
# from math import ceil
from werkzeug.exceptions import BadRequest, NotFound

# from flask_socketio import SocketIO, emit, join_room, leave_room, send


# used for serializer email and error handling
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature



# NEED to figure out where the NotFound or InternalServerError is displayed
# from werkzeug.exceptions import BadRequest, InternalServerError

#  NEED TO SOLVE THIS
# from NotificationHub import Notification
# from NotificationHub import NotificationHub

# BING API KEY
# Import Bing API key into bing_api_key.py

#  NEED TO SOLVE THIS
# from env_keys import BING_API_KEY, RDS_PW




# from env_file import RDS_PW, S3_BUCKET, S3_KEY, S3_SECRET_ACCESS_KEY
s3 = boto3.client('s3')


app = Flask(__name__)
# socketio = SocketIO(app, cors_allowed_origins="*")
api = Api(app)
# load_dotenv()

CORS(app)
# CORS(app, resources={r'/api/*': {'origins': '*'}})

# Set this to false when deploying to live application
app.config['DEBUG'] = True



# SECTION 2:  UTILITIES AND SUPPORT FUNCTIONS

# --------------- Google Scopes and Credentials------------------
# SCOPES = "https://www.googleapis.com/auth/calendar"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
# CLIENT_SECRET_FILE = "credentials.json"
# APPLICATION_NAME = "nitya-ayurveda"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
s = URLSafeTimedSerializer('thisisaverysecretkey')


# --------------- Stripe Variables ------------------
# STRIPE KEYS
stripe_public_test_key = os.getenv("stripe_public_test_key")
stripe_secret_test_key = os.getenv("stripe_secret_test_key")

stripe_public_live_key = os.getenv("stripe_public_live_key")
stripe_secret_live_key = os.getenv("stripe_secret_live_key")


# --------------- Twilio Setting ------------------
# Twilio's settings
# from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')



# --------------- Mail Variables ------------------
# Mail username and password loaded in .env file
app.config['MAIL_USERNAME'] = os.getenv('SUPPORT_EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('SUPPORT_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
# print("Sender: ", app.config['MAIL_DEFAULT_SENDER'])


# Setting for mydomain.com
app.config["MAIL_SERVER"] = "smtp.mydomain.com"
app.config["MAIL_PORT"] = 465

# Setting for gmail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465

app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True


# Set this to false when deploying to live application
app.config["DEBUG"] = True
# app.config["DEBUG"] = False

# MAIL  -- This statement has to be below the Mail Variables
mail = Mail(app)




# --------------- Time Variables ------------------
# convert to UTC time zone when testing in local time zone
utc = pytz.utc

# # These statment return Day and Time in GMT
# def getToday(): return datetime.strftime(datetime.now(utc), "%Y-%m-%d")
# def getNow(): return datetime.strftime(datetime.now(utc), "%Y-%m-%d %H:%M:%S")

# # These statment return Day and Time in Local Time - Not sure about PST vs PDT
def getToday():
    return datetime.strftime(datetime.now(), "%Y-%m-%d")

def getNow():
    return datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")


# NOTIFICATIONS - NEED TO INCLUDE NOTIFICATION HUB FILE IN SAME DIRECTORY
# from NotificationHub import AzureNotification
# from NotificationHub import AzureNotificationHub
# from NotificationHub import Notification
# from NotificationHub import NotificationHub
# For Push notification
# isDebug = False
# NOTIFICATION_HUB_KEY = os.environ.get('NOTIFICATION_HUB_KEY')
# NOTIFICATION_HUB_NAME = os.environ.get('NOTIFICATION_HUB_NAME')
# NOTIFICATION_HUB_NAME = os.environ.get('NOTIFICATION_HUB_NAME'




# -- Send Email Endpoints start here -------------------------------------------------------------------------------

def sendEmail(recipient, subject, body):
    with app.app_context():
        # print("In sendEmail: ", recipient, subject, body)
        sender="support@manifestmy.space"
        # print("sender: ", sender)
        msg = Message(
            sender=sender,
            recipients=[recipient],
            subject=subject,
            body=body
        )
        # print("sender: ", sender)
        # print("Email message: ", msg)
        mail.send(msg)
        # print("email sent")

# app.sendEmail = sendEmail

    
class SendEmail(Resource):
    def post(self):
        payload = request.get_json()
        print(payload)

        # Check if each field in the payload is not null
        if all(field is not None for field in payload.values()):
            sendEmail(payload["receiver"], payload["email_subject"], payload["email_body"])
            return "Email Sent"
        else:
            return "Some fields are missing in the payload", 400


class SendEmail_CLASS(Resource):
    def get(self, message):
        print("In Send EMail CRON get")
        try:
            conn = connect()

            recipient = "saumyashah4751@gmail.com"
            # recipient = "pmarathay@gmail.com"
            subject = "MMU CRON Jobs Completed"
            # body = "The Following CRON Jobs Ran:"
            body = message
            # mail.send(msg)
            sendEmail(recipient, subject, body)

            return "Email Sent", 200

        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            print("exit SendEmail")


def SendEmail_CRON(message):
        print("In Send EMail CRON get")
        try:
            conn = connect()

            recipients = ["saumyashah4751@gmail.com", "pmarathay@gmail.com"]
            subject = "MMU CRON Jobs Completed"
            # body = "The Following CRON Jobs Ran:"
            body = message
            # mail.send(msg)
            for recipient in recipients:
                sendEmail(recipient, subject, body)

            return "Email Sent", 200

        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            print("exit SendEmail")


def Send_Twilio_SMS(message, phone_number):
    items = {}
    numbers = phone_number
    message = message
    numbers = list(set(numbers.split(',')))
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    for destination in numbers:
        message = client.messages.create(
            body=message,
            from_='+19254815757',
            to="+1" + destination
        )
    items['code'] = 200
    items['Message'] = 'SMS sent successfully to the recipient'
    return items






# class Announcements(Resource):
#     def get(self, user_id):
#         print("In Announcements GET")
#         response = {}
#         with connect() as db:
#             # if user_id.startswith("600-"):
#             sentQuery = db.execute("""
#                     SELECT 
#                         a.*,
#                         COALESCE(b.business_name, c.owner_first_name, d.tenant_first_name) AS receiver_first_name,
#                         COALESCE(c.owner_last_name,  d.tenant_last_name) AS receiver_last_name,
#                         COALESCE(b.business_phone_number, c.owner_phone_number, d.tenant_phone_number) AS receiver_phone_number,
#                         COALESCE(b.business_photo_url, c.owner_photo_url, d.tenant_photo_url) AS receiver_photo_url
#                     , CASE
#                             WHEN a.announcement_receiver LIKE '600%' THEN 'Business'
#                             WHEN a.announcement_receiver LIKE '350%' THEN 'Tenant'
#                             WHEN a.announcement_receiver LIKE '110%' THEN 'Owner'
#                             ELSE 'Unknown'
#                       END AS receiver_role
#                     FROM space.announcements a
#                     LEFT JOIN space.businessProfileInfo b ON a.announcement_receiver LIKE '600%' AND b.business_uid = a.announcement_receiver
#                     LEFT JOIN space.ownerProfileInfo c ON a.announcement_receiver LIKE '110%' AND c.owner_uid = a.announcement_receiver
#                     LEFT JOIN space.tenantProfileInfo d ON a.announcement_receiver LIKE '350%' AND d.tenant_uid = a.announcement_receiver
#                     WHERE announcement_sender = \'""" + user_id + """\';
#             """)

#             response["sent"] = sentQuery

#             receivedQuery = db.execute("""
#                     SELECT 
#                         a.*,
#                         COALESCE(b.business_name, c.owner_first_name, d.tenant_first_name) AS sender_first_name,
#                         COALESCE(c.owner_last_name,  d.tenant_last_name) AS sender_last_name,
#                         COALESCE(b.business_phone_number, c.owner_phone_number, d.tenant_phone_number) AS sender_phone_number,
#                         COALESCE(b.business_photo_url, c.owner_photo_url, d.tenant_photo_url) AS sender_photo_url
#                         , CASE
#                             WHEN a.announcement_sender LIKE '600%' THEN 'Business'
#                             WHEN a.announcement_sender LIKE '350%' THEN 'Tenant'
#                             WHEN a.announcement_sender LIKE '110%' THEN 'Owner'
#                             ELSE 'Unknown'
#                         END AS sender_role
#                     FROM 
#                         space.announcements a
#                     LEFT JOIN 
#                         space.businessProfileInfo b ON a.announcement_sender LIKE '600%' AND b.business_uid = a.announcement_sender
#                     LEFT JOIN 
#                         space.ownerProfileInfo c ON a.announcement_sender LIKE '110%' AND c.owner_uid = a.announcement_sender
#                     LEFT JOIN 
#                         space.tenantProfileInfo d ON a.announcement_sender LIKE '350%' AND d.tenant_uid = a.announcement_sender
#                     WHERE 
#                         announcement_receiver = \'""" + user_id + """\';

#             """)

#             response["received"] = receivedQuery

#             # else:
#             #     response = db.execute("""
#             #                             -- Find the user details
#             #                             SELECT *
#             #                             FROM space.announcements AS a
#             #                             WHERE a.announcement_receiver = \'""" + user_id + """\'
#             #                             AND a.App = '1'
#             #                             ORDER BY a.announcement_date DESC;
#             #                             """)
#         return response

#     def post(self, user_id):
#         print("In Announcements POST")
#         payload = request.get_json()
#         # print("Post Announcement Payload: ", payload)
#         manager_id = user_id
#         if isinstance(payload["announcement_receiver"], list):
#             receivers = payload["announcement_receiver"]
#         else:
#             receivers = [payload["announcement_receiver"]]        

#         if isinstance(payload["announcement_properties"], list):
#             properties = payload["announcement_properties"]
#         else:
#             properties = [payload["announcement_properties"]]        

#         receiverPropertiesMap = {}

#         for propertyString in properties:
#             propertyObj = json.loads(propertyString)
#             # print("Property: ", propertyObj)

#             for key, value in propertyObj.items():
#                 receiverPropertiesMap[key] = value        

#         with connect() as db:
#             for i in range(len(receivers)):
#                 newRequest = {}
#                 newRequest['announcement_title'] = payload["announcement_title"]
#                 newRequest['announcement_msg'] = payload["announcement_msg"]
#                 newRequest['announcement_sender'] = manager_id
#                 newRequest['announcement_mode'] = payload["announcement_mode"]
#                 newRequest['announcement_properties'] = json.dumps(receiverPropertiesMap.get(receivers[i], []))
#                 newRequest['announcement_receiver'] = receivers[i]

#                 # Get the current date and time
#                 current_datetime = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    
#                 # Insert or update the "announcement_read" key with the current date and time
#                 newRequest['announcement_date'] = current_datetime
#                 # print("Announcement Date: ", newRequest['announcement_date'])

#                 user_query = None                    
#                 if(receivers[i][:3] == '350'):                    
#                     user_query = db.execute(""" 
#                                         -- Find the user details
#                                         SELECT tenant_email as email, tenant_phone_number as phone_number 
#                                         FROM space.tenantProfileInfo AS t
#                                         WHERE t.tenant_uid = \'""" + receivers[i] + """\';
#                                         """)                    
#                 elif(receivers[i][:3] == '110'):                                        
#                     user_query = db.execute(""" 
#                                         -- Find the user details
#                                         SELECT owner_email as email, owner_phone_number as phone_number 
#                                         FROM space.ownerProfileInfo AS o
#                                         WHERE o.owner_uid = \'""" + receivers[i] + """\';
#                                         """)
#                 elif(receivers[i][:3] == '600'):                                        
#                     user_query = db.execute(""" 
#                                         -- Find the user details
#                                         SELECT business_email as email, business_phone_number as phone_number
#                                         FROM space.businessProfileInfo AS b
#                                         WHERE b.business_uid = \'""" + receivers[i] + """\';
#                                         """)                                        
#                 for j in range(len(payload["announcement_type"])):
#                     if payload["announcement_type"][j] == "Email":
#                         newRequest['Email'] = "1"
#                         user_email = user_query['result'][0]['email']
#                         sendEmail(user_email, payload["announcement_title"], payload["announcement_msg"])
#                     if payload["announcement_type"][j] == "Text":
#                         continue
#                         newRequest['Text'] = "1"
#                         user_phone = user_query['result'][0]['phone_number']
#                         msg = payload["announcement_title"]+"\n" + payload["announcement_msg"]
#                         Send_Twilio_SMS(msg, user_phone)
#                     # if payload["announcement_type"][j] == "App":
#                     #     newRequest['App'] = "1"
#                 newRequest['App'] = "1"                
#                 response = db.insert('announcements', newRequest)

#         return response                

#     def put(self):
#         print("In Announcements PUT")
#         response = {}
#         payload = request.get_json()
#         if payload.get('announcement_uid') in {None, '', 'null'}:
#             print("No announcement_uid")
#             raise BadRequest("Request failed, no UID in payload.")
#         # print("Announcement Payload: ", payload)

#         # Get the current date and time
#         current_datetime = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    
#         # Insert or update the "announcement_read" key with the current date and time
#         payload['announcement_read'] = current_datetime


#         i = 0
#         for each in payload['announcement_uid']:
#             # print("current uid: ", each)
#             key = {'announcement_uid': each}
#             # print("Annoucement Key: ", key)
#             with connect() as db:
#                 response = db.update('announcements', key, payload)
#                 i = i + 1
#         response["rows affected"] = i
#         return response
    
# class LeaseExpiringNotify(Resource):
#     def get(self):
#         with connect() as db:
#             response = db.execute("""
#             SELECT *
#             FROM space.leases l
#             LEFT JOIN space.t_details t ON t.lt_lease_id = l.lease_uid
#             LEFT JOIN space.b_details b ON b.contract_property_id = l.lease_property_id
#             LEFT JOIN space.properties p ON p.property_uid = l.lease_property_id
#             WHERE l.lease_end = DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 2 MONTH), "%Y-%m-%d")
#             AND l.lease_status='ACTIVE'
#             AND b.contract_status='ACTIVE'; """)
#             print(response)
#             if len(response['result']) > 0:
#                 for i in range(len(response['result'])):
#                     name = response['result'][i]['tenant_first_name'] + \
#                            ' ' + response['result'][i]['tenant_last_name']
#                     address = response['result'][i]["tenant_address"] + \
#                               ' ' + response['result'][i]["tenant_unit"] + ", " + response['result'][i]["tenant_city"] + \
#                               ', ' + response['result'][i]["tenant_state"] + \
#                               ' ' + response['result'][i]["tenant_zip"]
#                     start_date = response['result'][i]['lease_start']
#                     end_date = response['result'][i]['lease_end']
#                     business_name = response['result'][i]['business_name']
#                     phone = response['result'][i]['business_phone_number']
#                     email = response['result'][i]['business_email']
#                     recipient = response['result'][i]['tenant_email']
#                     subject = "Lease ending soon..."
#                     body = (
#                             "Hello " + str(name) + "," + "\n"
#                              "\n"
#                              "Property: " + str(address) + "\n"
#                            "This is your 2 month reminder, that your lease is ending. \n"
#                            "Here are your lease details: \n"
#                            "Start Date: " +
#                             str(start_date) + "\n"
#                           "End Date: " +
#                             str(end_date) + "\n"
#                         "Please contact your Property Manager if you wish to renew or end your lease before the time of expiry. \n"
#                         "\n"
#                         "Name: " + str(business_name) + "\n"
#                         "Phone: " + str(phone) + "\n"
#                          "Email: " + str(email) + "\n"
#                                  "\n"
#                                  "Thank you - Team Property Management\n\n"
#                     )
#                     sendEmail(recipient, subject, body)
#                     print('sending')

#                 return response


# -- Stored Procedures start here -------------------------------------------------------------------------------


# RUN STORED PROCEDURES

# def get_new_billUID(conn):
#     newBillQuery = execute("CALL space.new_bill_uid;", "get", conn)
#     if newBillQuery["code"] == 280:
#         return newBillQuery["result"][0]["new_id"]
#     return "Could not generate new bill UID", 500


# def get_new_purchaseUID(conn):
#     newPurchaseQuery = execute("CALL space.new_purchase_uid;", "get", conn)
#     if newPurchaseQuery["code"] == 280:
#         return newPurchaseQuery["result"][0]["new_id"]
#     return "Could not generate new bill UID", 500

# def get_new_propertyUID(conn):
#     newPropertyQuery = execute("CALL space.new_property_uid;", "get", conn)
#     if newPropertyQuery["code"] == 280:
#         return newPropertyQuery["result"][0]["new_id"]
#     return "Could not generate new property UID", 500


# -- MMU Queries start here -------------------------------------------------------------------------------

class stripe_key(Resource):
    def get(self, desc):
        print(desc)
        if desc == "PMTEST":
            return {"publicKey": stripe_public_test_key}
        else:
            return {"publicKey": stripe_public_live_key}
    
        

# -- MMU CRON ENDPOINTS start here -------------------------------------------------------------------------------

# class endpointTest_CLASS(Resource):
    
#     def get(self):
#         print("In endpointTest CRON")
#         BASE_URL = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"
#         LOGIN_URL = "https://mrle52rri4.execute-api.us-west-1.amazonaws.com/dev/api/v2"
#         dt = datetime.now()
#         response = {}
#         count = 0
#         api_list_failed = []
#         api_list_successful = []

#         try:
#             with connect() as db:

#                 # ******** Userinfo ********
#                 print("\nIn UserInfo")
#                 get_userinfo_response = requests.get(BASE_URL + "/userinfo/100-000001")
#                 if not (get_userinfo_response.status_code == 200):
#                     api_list_failed.append('Get UserInfo API')
#                 else:
#                     api_list_successful.append('Get UserInfo API')
#                 count += 1

#                 put_userinfo_payload = {
#                     "user_uid": "100-000006",
#                     "user_email_id": "mollysymonds@gmail.com",
#                     "user_first_name": "Molly",
#                     "user_last_name": "Symonds",
#                     "user_notification_preference": "True",
#                     "user_location_service": "True",
#                     "user_date_interests": "Coffee,Lunch,Dinner",
#                     "user_available_time": '[{"day": "Wednesday", "end_time": "06:00 PM", "start_time": "02:00 PM"}, {"day": "Sunday", "end_time": "04:00 PM", "start_time": "01:00 PM"}, {"day": "Saturday", "end_time": "10:00 PM", "start_time": "11:00 AM"}]'
#                 }
#                 put_userinfo_response = requests.put(BASE_URL + "/userinfo", data=put_userinfo_payload)
#                 if not (put_userinfo_response.status_code == 200):
#                     api_list_failed.append('Put UserInfo API')
#                 else:
#                     api_list_successful.append('Put UserInfo API')
#                 count += 1

#                 # ******** Likes ********
#                 print("\nIn Likes")
#                 get_likes_response = requests.get(BASE_URL + "/likes/100-000001")
#                 if not (get_likes_response.status_code == 200):
#                     api_list_failed.append('Get likes API')
#                 else:
#                     api_list_successful.append('Get likes API')
#                 count += 1

#                 post_likes_payload = {
#                     "liker_user_id": "100-000001",
#                     "liked_user_id": "100-000004"
#                 }
#                 post_likes_response = requests.post(BASE_URL + "/likes", data=post_likes_payload)
#                 if not (post_likes_response.status_code == 200):
#                     api_list_failed.append('Post Likes API')
#                 else:
#                     api_list_successful.append('Post Likes API')
#                 count += 1

#                 delete_likes_payload = {
#                     "liker_user_id": "100-000001",
#                     "liked_user_id": "100-000004"
#                 }
#                 delete_likes_response = requests.delete(BASE_URL + "/likes", data=delete_likes_payload)
#                 if not (delete_likes_response.status_code == 200):
#                     api_list_failed.append('Delete Likes API')
#                 else:
#                     api_list_successful.append('Delete Likes API')
#                 count += 1

#                 # ******** Meet ********
#                 print("\nIn Meet")
#                 get_meet_response = requests.get(BASE_URL + "/meet/100-000001")
#                 if not (get_meet_response.status_code == 200):
#                     api_list_failed.append('Get Meet API')
#                 else:
#                     api_list_successful.append('Get Meet API')
#                 count += 1

#                 post_meet_payload = {
#                     "meet_user_id": "100-000001",
#                     "meet_date_user_id": "100-000004",
#                     "meet_day": "Saturday",
#                     "meet_time": "7:00 AM"
#                 }
#                 post_meet_response = requests.post(BASE_URL + "/meet", data=post_meet_payload)
#                 post_meet_delete = post_meet_response.json()
#                 query = f'''DELETE FROM mmu.meet
#                         WHERE meet_uid="{post_meet_delete['meet_uid']}"'''
#                 result = db.delete(query)
#                 if not (post_meet_response.status_code == 200):
#                     api_list_failed.append('Post Meet API')
#                 else:
#                     api_list_successful.append('Post Meet API')
#                 count += 1

#                 # ******** Lists ********
#                 print("\nIn Lists")
#                 get_lists_response = requests.get(BASE_URL + "/lists?list_category=activities")
#                 if not (get_lists_response.status_code == 200):
#                     api_list_failed.append('Get Lists API')
#                 else:
#                     api_list_successful.append('Get Lists API')
#                 count += 1

#                 # ******** Messages ********
#                 print("\nIn Messages")
#                 get_messages_response = requests.get(BASE_URL + "/messages?sender_id=100-000001&receiver_id=100-000007")
#                 if not (get_messages_response.status_code == 200):
#                     api_list_failed.append('Get Messages API')
#                 else:
#                     api_list_successful.append('Get Messages API')
#                 count += 1

#                 post_messages_payload = {
#                     "sender_id": "100-000001",
#                     "receiver_id": "100-000002",
#                     "message_content": "Hi, There"
#                 }
#                 headers = {
#                     'Content-Type': 'application/json'
#                 }
#                 post_messages_response = requests.post(BASE_URL + "/messages", data=json.dumps(post_messages_payload), headers=headers)
#                 delete = post_messages_response.json()
#                 query = f'''DELETE FROM mmu.messages
#                         WHERE message_uid="{delete['message_uid']}"'''
#                 result = db.delete(query)
#                 if not (post_messages_response.status_code == 200):
#                     api_list_failed.append('Post Messages API')
#                 else:
#                     api_list_successful.append('Post Messages API')
#                 count += 1

#                 # ******** Matches ********
#                 print("\nIn Matches")
#                 get_matches_response = requests.get(BASE_URL + "/matches/100-000001")
#                 if not (get_matches_response.status_code == 200):
#                     api_list_failed.append('Get Matches API')
#                 else:
#                     api_list_successful.append('Get Matches API')
#                 count += 1
                
#                 # ******** Login ********
#                 print("\nIn Login")
#                 user_uid = ""
#                 create_account_payload = {
#                         "email": "testapi1@gmail.com",
#                         "password": "123",
#                         "phone_number": "(408) 679-4332"
#                     }
#                 create_account_response = requests.post(LOGIN_URL + "/CreateAccount/MMU", data=json.dumps(create_account_payload), headers=headers)
#                 delete = create_account_response.json()
#                 user_uid = delete['result'][0]['user_uid']
#                 if not (create_account_response.status_code == 200):
#                     api_list_failed.append('Create Account API')
#                 else:
#                     api_list_successful.append('Create Account API')
#                 count += 1

#                 account_salt_payload = {
#                     "email": "testapi@gmail.com",
#                     "password": "123"
#                 }
#                 account_salt_response = requests.post(LOGIN_URL + "/AccountSalt/MMU", data=json.dumps(account_salt_payload), headers=headers)
#                 if not (account_salt_response.status_code == 200):
#                     api_list_failed.append("Account Salt API")
#                 else:
#                     print(' Now In Login Part')
#                     api_list_successful.append('Account Salt API')
#                     method = account_salt_response.json()
#                     def getHash(value):
#                         base = str(value).encode()
#                         return sha256(base).hexdigest()
#                     def createHash(password, salt):
#                         return getHash(password+salt)
#                     password = createHash(account_salt_payload["password"], method["result"][0]["password_salt"])
#                     email_login_payload = {
#                         "email": "testapi@gmail.com",
#                         "password": password
#                     }
#                     email_login_response = requests.post(LOGIN_URL + "/Login/MMU", data=json.dumps(email_login_payload), headers=headers)
#                     query = f'''DELETE FROM mmu.users
#                             WHERE user_uid="{user_uid}"'''
#                     result = db.delete(query)
#                     if not (email_login_response.status_code == 200):
#                         api_list_failed.append('Email Login API')
#                     else:
#                         api_list_successful.append('Email Login API')
#                 count += 1

#             print(" \n\n Successfully ran test APIs \n\n ")

#             try:
#                 if not api_list_failed:
#                     message_content = f"Hello,\n\nDate/Time: {dt}. \nEndpoint Test CRONJOB ran successfully. \n\nTotal number of APIs tested: {count}. \nList of APIs ran successfully: {api_list_successful}"
#                 else:
#                     message_content = f"Hello,\n\nDate/Time: {dt}. \nEndpoint Test CRONJOB ran successfully. \n\nTotal number of APIs tested: {count}. \n\nList of APIs ran successfully: {api_list_successful} \n\nList of APIs failed: {api_list_failed}"

#                 SendEmail_CRON(message_content)

#                 response["email"] = {'message': f'EndpointTest CRON Job Email for {dt} sent!' ,
#                         'code': 500}
#             except:
#                 response["email fail"] = {'message': f'EndpointTest CRON Job Email for {dt} could not be sent' ,
#                         'code': 500}
        
#         except:
#             try:
#                 message_content = f"Hello,\n\nDate/Time: {dt}. \nThere was some error while running Endpoint Test CRONJOB"

#                 SendEmail_CRON(message_content)

#                 response["email"] = {'message': f'EndpointTest CRON Job Fail Email for {dt} sent!' ,
#                         'code': 500}
#             except:
#                 response["email fail"] = {'message': f'EndpointTest CRON Job Fail Email for {dt} could not be sent' ,
#                         'code': 500}
#         return response

# def endpointTest_CRON():
#     print("In endpointTest CRON")
#     BASE_URL = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"
#     LOGIN_URL = "https://mrle52rri4.execute-api.us-west-1.amazonaws.com/dev/api/v2"
#     dt = datetime.now()
#     response = {}
#     count = 0
#     api_list_failed = []
#     api_list_successful = []

#     try:
#         with connect() as db:

#             # ******** Userinfo ********
#             get_userinfo_response = requests.get(BASE_URL + "/userinfo/100-000001")
#             if not (get_userinfo_response.status_code == 200):
#                 api_list_failed.append('Get UserInfo API')
#             else:
#                 api_list_successful.append('Get UserInfo API')
#             count += 1

#             put_userinfo_payload = {
#                 "user_uid": "100-000006",
#                 "user_email_id": "mollysymonds@gmail.com",
#                 "user_first_name": "Molly",
#                 "user_last_name": "Symonds",
#                 "user_notification_preference": "True",
#                 "user_location_service": "True",
#                 "user_date_interests": "Coffee,Lunch,Dinner",
#                 "user_available_time": '[{"day": "Wednesday", "end_time": "06:00 PM", "start_time": "02:00 PM"}, {"day": "Sunday", "end_time": "04:00 PM", "start_time": "01:00 PM"}, {"day": "Saturday", "end_time": "10:00 PM", "start_time": "11:00 AM"}]'
#             }
#             put_userinfo_response = requests.put(BASE_URL + "/userinfo", data=put_userinfo_payload)
#             if not (put_userinfo_response.status_code == 200):
#                 api_list_failed.append('Put UserInfo API')
#             else:
#                 api_list_successful.append('Put UserInfo API')
#             count += 1

#             # ******** Likes ********
#             get_likes_response = requests.get(BASE_URL + "/likes/100-000001")
#             if not (get_likes_response.status_code == 200):
#                 api_list_failed.append('Get likes API')
#             else:
#                 api_list_successful.append('Get likes API')
#             count += 1

#             post_likes_payload = {
#                 "liker_user_id": "100-000001",
#                 "liked_user_id": "100-000004"
#             }
#             post_likes_response = requests.post(BASE_URL + "/likes", data=post_likes_payload)
#             if not (post_likes_response.status_code == 200):
#                 api_list_failed.append('Post Likes API')
#             else:
#                 api_list_successful.append('Post Likes API')
#             count += 1

#             delete_likes_payload = {
#                 "liker_user_id": "100-000001",
#                 "liked_user_id": "100-000004"
#             }
#             delete_likes_response = requests.delete(BASE_URL + "/likes", data=delete_likes_payload)
#             if not (delete_likes_response.status_code == 200):
#                 api_list_failed.append('Delete Likes API')
#             else:
#                 api_list_successful.append('Delete Likes API')
#             count += 1

#             # ******** Meet ********
#             get_meet_response = requests.get(BASE_URL + "/meet/100-000001")
#             if not (get_meet_response.status_code == 200):
#                 api_list_failed.append('Get Meet API')
#             else:
#                 api_list_successful.append('Get Meet API')
#             count += 1

#             post_meet_payload = {
#                 "meet_user_id": "100-000001",
#                 "meet_date_user_id": "100-000004",
#                 "meet_day": "Saturday",
#                 "meet_time": "7:00 AM"
#             }
#             post_meet_response = requests.post(BASE_URL + "/meet", data=post_meet_payload)
#             post_meet_delete = post_meet_response.json()
#             query = f'''DELETE FROM mmu.meet
#                     WHERE meet_uid="{post_meet_delete['meet_uid']}"'''
#             result = db.delete(query)
#             if not (post_meet_response.status_code == 200):
#                 api_list_failed.append('Post Meet API')
#             else:
#                 api_list_successful.append('Post Meet API')
#             count += 1

#             # ******** Lists ********
#             get_lists_response = requests.get(BASE_URL + "/lists?list_category=activities")
#             if not (get_lists_response.status_code == 200):
#                 api_list_failed.append('Get Lists API')
#             else:
#                 api_list_successful.append('Get Lists API')
#             count += 1

#             # ******** Messages ********
#             get_messages_response = requests.get(BASE_URL + "/messages?sender_id=100-000001&receiver_id=100-000007")
#             if not (get_messages_response.status_code == 200):
#                 api_list_failed.append('Get Messages API')
#             else:
#                 api_list_successful.append('Get Messages API')
#             count += 1

#             post_messages_payload = {
#                 "sender_id": "100-000001",
#                 "receiver_id": "100-000002",
#                 "message_content": "Hi, There"
#             }
#             headers = {
#                 'Content-Type': 'application/json'
#             }
#             post_messages_response = requests.post(BASE_URL + "/messages", data=json.dumps(post_messages_payload), headers=headers)
#             delete = post_messages_response.json()
#             query = f'''DELETE FROM mmu.messages
#                     WHERE message_uid="{delete['message_uid']}"'''
#             result = db.delete(query)
#             if not (post_messages_response.status_code == 200):
#                 api_list_failed.append('Post Messages API')
#             else:
#                 api_list_successful.append('Post Messages API')
#             count += 1

#             # ******** Matches ********
#             get_matches_response = requests.get(BASE_URL + "/matches/100-000001")
#             if not (get_matches_response.status_code == 200):
#                 api_list_failed.append('Get Matches API')
#             else:
#                 api_list_successful.append('Get Matches API')
#             count += 1
            
#             # ******** Login ********
#             user_uid = ""
#             create_account_payload = {
#                     "email": "testapi@gmail.com",
#                     "password": "123",
#                     "phone_number": "(408) 679-4332"
#                 }
#             create_account_response = requests.post(LOGIN_URL + "/CreateAccount/MMU", data=json.dumps(create_account_payload), headers=headers)
#             delete = create_account_response.json()
#             user_uid = delete['result'][0]['user_uid']
#             if not (create_account_response.status_code == 200):
#                 api_list_failed.append('Create Account API')
#             else:
#                 api_list_successful.append('Create Account API')
#             count += 1

#             account_salt_payload = {
#                 "email": "testapi@gmail.com",
#                 "password": "123"
#             }
#             account_salt_response = requests.post(LOGIN_URL + "/AccountSalt/MMU", data=json.dumps(account_salt_payload), headers=headers)
#             if not (account_salt_response.status_code == 200):
#                 api_list_failed.append("Account Salt API")
#             else:
#                 print(' Now In Login Part')
#                 api_list_successful.append('Account Salt API')
#                 method = account_salt_response.json()
#                 def getHash(value):
#                     base = str(value).encode()
#                     return sha256(base).hexdigest()
#                 def createHash(password, salt):
#                     return getHash(password+salt)
#                 password = createHash(account_salt_payload["password"], method["result"][0]["password_salt"])
#                 email_login_payload = {
#                     "email": "testapi@gmail.com",
#                     "password": password
#                 }
#                 email_login_response = requests.post(LOGIN_URL + "/Login/MMU", data=json.dumps(email_login_payload), headers=headers)
#                 query = f'''DELETE FROM mmu.users
#                         WHERE user_uid="{user_uid}"'''
#                 result = db.delete(query)
#                 if not (email_login_response.status_code == 200):
#                     api_list_failed.append('Email Login API')
#                 else:
#                     api_list_successful.append('Email Login API')
#             count += 1

#         print(" \n\n Successfully ran test APIs \n\n ")

#         try:
#             if not api_list_failed:
#                 message_content = f"Hello,\n\nDate/Time: {dt}. \nEndpoint Test CRONJOB ran successfully. \n\nTotal number of APIs tested: {count}. \nList of APIs ran successfully: {api_list_successful}"
#             else:
#                 message_content = f"Hello,\n\nDate/Time: {dt}. \nEndpoint Test CRONJOB ran successfully. \n\nTotal number of APIs tested: {count}. \n\nList of APIs ran successfully: {api_list_successful} \n\nList of APIs failed: {api_list_failed}"

#             SendEmail_CRON(message_content)

#             response["email"] = {'message': f'EndpointTest CRON Job Email for {dt} sent!' ,
#                     'code': 500}
#         except:
#             response["email fail"] = {'message': f'EndpointTest CRON Job Email for {dt} could not be sent' ,
#                     'code': 500}
    
#     except:
#         try:
#             message_content = f"Hello,\n\nDate/Time: {dt}. \nThere was some error while running Endpoint Test CRONJOB"

#             SendEmail_CRON(message_content)

#             response["email"] = {'message': f'EndpointTest CRON Job Fail Email for {dt} sent!' ,
#                     'code': 500}
#         except:
#             response["email fail"] = {'message': f'EndpointTest CRON Job Fail Email for {dt} could not be sent' ,
#                     'code': 500}
#     return response


class endpointTest_CLASS(Resource):
    def get(self):
        print("\nIn Test API Endpoints Class - GET Method\n\n")
        response = {}
        dt = datetime.today()
        try:
            print("in try", dt)
            obj = test_endpoint_CLASS()
            response = obj.get()
            
            if "cron fail" in response.keys():
                raise Exception("Error in cronjob") 

            try:
                recipients = ["pmarathay@gmail.com",
                             "saumyashah4751@gmail.com"]
                subject = f"MMU Test API CRON JOB for {dt} Completed "
                body = f"MMU Test API CRON JOB has been executed. \n\n{response}\n\n" + "\n"

                for recipient in recipients:
                    sendEmail(recipient, subject, body)

                response["email"] = {'message': f'MMU Test API CRON Job Email for {dt} sent!' , 'code': 200}

            except:
                response["email fail"] = {'message': f'MMU Test API CRON Job Email for {dt} could not be sent' , 'code': 500}

        except:
            try:
                recipients = ["pmarathay@gmail.com",
                             "saumyashah4751@gmail.com"]
                subject = "MMU Test API CRON JOB Failed!"
                body = f"MMU Test API CRON JOB Failed. \n\n{response}\n\n"

                for recipient in recipients:
                    sendEmail(recipient, subject, body)

                response["email"] = {'message': f'MMU Test API CRON Job Fail Email for {dt} sent!' , 'code': 201}

            except:
                response["email fail"] = {'message': f'MMU Test API CRON Job Fail Email for {dt} could not be sent' , 'code': 500}

        return response

def endpointTest_CRON():
    print("\nIn Test API Endpoints Class - GET Method\n\n")
    response = {}
    dt = datetime.today()
    try:
        print("in try", dt)
        obj = test_endpoint_CLASS()
        response = obj.get()

        if "cron fail" in response.keys():
            raise Exception("Error in cronjob") 

        try:
            recipients = ["pmarathay@gmail.com",
                            "saumyashah4751@gmail.com"]
            subject = f"MMU Test API CRON JOB for {dt} Completed "
            body = f"MMU Test API CRON JOB has been executed. \n\n{response}\n\n" + "\n"

            for recipient in recipients:
                sendEmail(recipient, subject, body)

            response["email"] = {'message': f'MMU Test API CRON Job Email for {dt} sent!' , 'code': 200}

        except:
            response["email fail"] = {'message': f'MMU Test API CRON Job Email for {dt} could not be sent' , 'code': 500}

    except:
        try:
            recipients = ["pmarathay@gmail.com",
                            "saumyashah4751@gmail.com"]
            subject = "MMU Test API CRON JOB Failed!"
            body = f"MMU Test API CRON JOB Failed. \n\n{response}\n\n"

            for recipient in recipients:
                sendEmail(recipient, subject, body)

            response["email"] = {'message': f'MMU Test API CRON Job Fail Email for {dt} sent!' , 'code': 201}

        except:
            response["email fail"] = {'message': f'MMU Test API CRON Job Fail Email for {dt} could not be sent' , 'code': 500}

    return response


#  -- WEB SOCKET FOR CHATTING    -----------------------------------------
# def get_conversation_uid(sender_id, receiver_id, db):
#     conversation_query = f'''SELECT *
#                         FROM mmu.conversations
#                         WHERE conversation_user_id_1 = LEAST("{sender_id}","{receiver_id}") AND conversation_user_id_2 = GREATEST("{sender_id}","{receiver_id}");'''

#     response = db.execute(conversation_query)

#     if not response['result']:
#         new_conversation_id = db.call(procedure='new_conversation_uid')
#         conversation_id = new_conversation_id['result'][0]['new_id']

#     else: 
#         conversation_id = response['result'][0]['conversation_uid']

#     conversation_query = f'''INSERT INTO mmu.conversations (conversation_uid, conversation_user_id_1, conversation_user_id_2)
#                         VALUES ("{conversation_id}",LEAST("{sender_id}","{receiver_id}"),GREATEST("{sender_id}","{receiver_id}"));'''
#     response = db.execute(conversation_query, cmd='post')

#     return conversation_id


# @socketio.on('connect', namespace='/chat')
# def handle_connect():
#     print('Client Connected')

# @socketio.on('join_conversation', namespace='/chat')
# def handle_join_conversation(data):
#     print('\n\n', "In Join Conversation of Socket", '\n\n')

#     conversation_id = get_conversation_uid(data['user_id_1'], data['user_id_2'], connect())
#     room = conversation_id
#     print('\n\n Conversation ID:', conversation_id)

#     join_room(room)
#     emit('join_announcement', {'room_id': room, 'msg': f"Users has joined the conversation"}, room=room)

# @socketio.on('send_message', namespace='/chat')
# def handle_send_message(data):
#     print("\n\n In Send Message of Socket \n\n")

#     room = data['room']
#     sender_id = data['sender_id']

#     store_message_in_db(sender_id, data['message'], room)

#     emit('receive_message', data['message'], room=room)

# @socketio.on('leave_conversation', namespace='/chat')
# def handle_leave_conversation(data):
#     print("\n\n In Leave Conversation")

#     room = data['room']

#     leave_room(room)

#     emit('leave_announcement', {'msg': f"User {data['user_id']} has left the conversation"}, room=data['user_id'])

# def store_message_in_db(sender_id, message, conversation_id):
#     print("\n\n In Store Message DB \n\n")
#     try:   
#         with connect() as db:
#             new_message_id = db.call(procedure='new_message_uid')
#             new_message_id = new_message_id['result'][0]['new_id']
#             message_query = f'''INSERT INTO mmu.messages (message_uid, message_conversation_id, message_sender_user_id, message_content)
#                             VALUES ("{new_message_id}","{conversation_id}","{sender_id}","{message}")'''
            
#             response = db.execute(message_query, cmd="post")

#             return response
#     except:
#         return "Error in store message in db"

#  -- ACTUAL ENDPOINTS    -----------------------------------------

api.add_resource(AppleLogin, '/appleLogin')
api.add_resource(List, '/lists')
api.add_resource(stripe_key, "/stripe_key/<string:desc>")
api.add_resource(SendEmail_CLASS, "/sendEmail_CLASS")
api.add_resource(SendEmail, "/sendEmail")
api.add_resource(UserInfo, "/userinfo", "/userinfo/<user_id>")
api.add_resource(Match, "/matches", "/matches/<user_uid>")
api.add_resource(Meet, "/meet", "/meet/<user_id>")
api.add_resource(Likes,  "/likes", "/likes/<user_id>")
api.add_resource(Messages, "/messages")
api.add_resource(Announcements, "/announcements", "/announcements/<user_id>")
api.add_resource(Password, "/resetpassword")
api.add_resource(endpointTest_CLASS, "/testapi")
# api.add_resource(S3Video_presigned_url, "/s3")
# api.add_resource(test_endpoint_CLASS, "/v2/testapi")

if __name__ == '__main__':
    # socketio.run(app, host='127.0.0.1', port=4000, debug=True)
    app.run(host='127.0.0.1', port=4050)