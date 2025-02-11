from flask import request, make_response, jsonify

import os
import pymysql
import datetime
import json
import boto3
from botocore.response import StreamingBody
from decimal import Decimal
# from datetime import date, datetime, timedelta
from werkzeug.datastructures import FileStorage
import mimetypes
import ast
# from s3 import processImage, uploadImage, deleteImage

from dotenv import load_dotenv
load_dotenv()

# s3 = boto3.client(
#     's3',
#     aws_access_key_id=os.getenv('S3_KEY'),
#     aws_secret_access_key=os.getenv('S3_SECRET'),
#     region_name=os.getenv('S3_REGION')
# )


# def deleteImage(key):
#     bucket = 'io-mmu'
#     try:
#         print("Before Delete: ", bucket, key)
#         delete_file = s3.delete_object(
#             Bucket=bucket,
#             Key=key
#         )
#         print("After Delete: ", delete_file)
#         print("After Delete Status Code: ", delete_file['ResponseMetadata']['HTTPStatusCode'])
#         print(f"Deleted existing file {key} from bucket {bucket}")
#         return True
#     except s3.exceptions.ClientError as e:
#         if e.response['Error']['Code'] == 'NoSuchKey':
#             print(f"File {key} does not exist in bucket {bucket}")
#         else:
#             print(f"Error deleting file {key} from bucket {bucket}: {e}")
#         return False


# def uploadImage(file, key, content):
#     print("\nIn Upload Image: ")
#     # print("File: ", file)
#     # print("Key: ", key)
#     # print("Content: ", content)
#     bucket = 'io-mmu'

#     if isinstance(file, FileStorage): 
#         print("In Upload Image isInstance File Storage: ", FileStorage)
#         file.stream.seek(0)
#         file_content = file.stream.read()
#         content_type, _ = mimetypes.guess_type(file.filename)
#         contentType = content_type if content_type else 'application/octet-stream'  # Fallback if MIME type is not detected
#         print("In Upload Image contentType: ", contentType) # This returns jpeg, png, ect

#     elif isinstance(file, StreamingBody):
#         print("In Upload Image isInstance Streaming Body")
#         file_content = file.read()
#         contentType = content
#         print("In Upload Image contentType: ", contentType)
#         # Set content type based on your logic or metadata
#         # Example: contentType = 'image/jpeg' or other appropriate content type


#     if file_content:
#         # print("file_content: ", file_content )   # Unnecessary print statement.  Return hexedemical file info
#         filename = f'https://s3-us-west-1.amazonaws.com/{bucket}/{key}'
#         print("Before Upload: ", bucket, key, filename, contentType)
#         # This Statement Actually uploads the file into S3
#         upload_file = s3.put_object(
#             Bucket=bucket,
#             Body=file_content,
#             Key=key,
#             # ACL='public-read',
#             ContentType=contentType
#         )
#         print("After Upload: ", upload_file)
#         print("After Upload Status Code: ", upload_file['ResponseMetadata']['HTTPStatusCode'])
#         print("Derived Filename: ", filename)
#         return filename
    
#     return None

# # --------------- PROCESS IMAGES ------------------

# def processImage(key, payload):

#     print("\nIn Process Image: ", payload)

#     response = {}

#     with connect() as db:

#         if 'user_uid' in key:
#             print("\n\n-----------User Key passed----------------\n\n")
#             key_type = 'users'
#             key_uid = key['user_uid']
#             payload_delete_images = payload.pop('delete_images', None)  # Images to Delete

#             #  GET images sent by Frontend. (img_0, img_1, ..)
#             if 'img_0' in request.files or payload_delete_images != None: 
#                 # Current Images in the database  
#                 payload_query = db.execute(""" SELECT user_photo_url FROM mmu.users WHERE user_uid = \'""" + key_uid + """\'; """)     
                
#                 payload_images = payload_query['result'][0]['user_photo_url'] 
#                 payload_fav_images = payload.get("user_favorite_image") or payload.get("img_favorite")   # (PUT & POST)
#             else:
#                 return payload

#         else:
#             print("No UID found in key")
#             return
        

#         print("key_type: ", key_type, type(key_type))
#         print("key_uid: ", key_uid, type(key_uid))
#         print("payload_images: ", payload_images, type(payload_images))        
#         print("payload_images delete: ", payload_delete_images, type(payload_delete_images))

#         # Check if images already exist
#         # Put current db images into current_images
#         current_images = []
#         if payload_images is not None and payload_images != '' and payload_images != 'null':
#             print("---Payload Images: ", payload_images)
#             current_images =ast.literal_eval(payload_images)
#             print('\n\n\n Current Images: ', current_images, '\n\n\n')
#             print("---Current images: ", current_images, type(current_images))

#         # Check if images are being added OR deleted
#         images = []
#         i = 0
#         imageFiles = {}

#         print("\n\n\n--------------About to Add Images--------------\n\n\n")

#         # ADD Images
#         while True:
#             filename = f'img_{i}'
#             print("\n\nPut image file into Filename: ", filename)

#             file = request.files.get(filename)
#             print("\n\nFile:" , file)        

#             s3Link = payload.get(filename) # Used for fav images
#             print("\n\nS3Link: ", s3Link)

#             if file:
#                 print("\n\nIn 'if file' Statement")
#                 imageFiles[filename] = file
#                 unique_filename = filename + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
#                 image_key = f'{key_type}/{key_uid}/{unique_filename}'

#                 # This calls the uploadImage function that generates the S3 link
#                 image = uploadImage(file, image_key, '')
                
#                 print("\n\nImage after upload: ", image)

#                 images.append(image)

#                 if filename == payload_fav_images:
#                     if key_type == 'user_uid': payload["user_favorite_photo"] = image

#             elif s3Link:
#                 imageFiles[filename] = s3Link
#                 images.append(s3Link)

#                 if filename == payload_fav_images:
#                     if key_type == 'user_uid': payload["user_favorite_photo"] = image
            
#             else:
#                 break
#             i += 1
        
#         print("Images after loop: ", images)
#         if images != []:
#             current_images.extend(images)

#         # Delete Images
#         # if payload_delete_images:
#         #     print("In image delete: ", payload_delete_images, type( payload_delete_images))
#         #     delete_images = ast.literal_eval(payload_delete_images)
#         #     print("After ast: ", delete_images, type(delete_images), len(delete_images))
#         #     for image in delete_images:
#         #         # print("Image to Delete: ", image, type(image))
#         #         # print("Payload Image:", current_images, type(current_images))
#         #         # print("Current images before deletion:", [doc['link'] for doc in current_images])

#         #         # Delete from db list assuming it is in db list
#         #         try:
#         #             current_images.remove(image)   # Works becuase this is an Exact match
#         #         except:
#         #             print("Image not in list")

#         #         #  Delete from S3 Bucket
#         #         try:
#         #             delete_key = image.split('io-pm/', 1)[1]
#         #             # print("Delete key", delete_key)
#         #             deleteImage(delete_key)
#         #         except: 
#         #             print("could not delete from S3")
            
#         print("\n\nCurrent Images in Function: ", current_images, type(current_images))

#         if key_type == 'users': payload['user_photo_url'] = json.dumps(current_images) 

#         print("\n\n\Payload before return: ", payload)
#         return payload



# --------------- PROCESS DOCUMENTS ------------------

# def processDocument(key, payload):
#     print("\nIn Process Documents: ", payload)
#     # print("Key Passed into processDocuments: ", key)
#     response = {}
#     with connect() as db:

#         if 'contract_uid' in key:
#             print("Contract Key passed")
#             key_type = 'contracts'
#             key_uid = key['contract_uid']
#             payload_changed_documents = payload.pop('contract_documents', None)             # Current Documents     (if there is a change in a current document)
#             payload_document_details = payload.pop('contract_documents_details', None)      # New Documents         (if there are New documents being added)
#             payload_delete_documents = payload.pop('delete_documents', None)                # Documents to Delete   (if documents are being deleted)
#             if payload_changed_documents != None or payload_document_details != None or payload_delete_documents != None:
#                 payload_query = db.execute(""" SELECT contract_documents FROM space.contracts WHERE contract_uid = \'""" + key_uid + """\'; """)     # Get Current Documents from db
#                 # print("1: ", payload_query)
#                 # print("2: ", payload_query['result'], type(payload_query['result']))
#                 # if payload_query['result']: print("3: ", payload_query['result'][0] ) 
#                 # if payload_query['result']: print("4: ", payload_query['result'][0]['contract_documents'], type(payload_query['result'][0]['contract_documents']))
#                 payload_documents = payload_query['result'][0]['contract_documents'] if payload_query['result'] else "None"
#             else:
#                 return payload
            

#         elif 'lease_uid' in key:
#             print("Lease Key passed")
#             key_type = 'leases'
#             key_uid = key['lease_uid']
#             payload_changed_documents = payload.pop('lease_documents', None)                # Current Documents     (if there is a change in a current document)
#             payload_document_details = payload.pop('lease_documents_details', None)         # New Documents
#             payload_delete_documents = payload.pop('delete_documents', None)                # Documents to Delete
#             if payload_changed_documents != None or payload_document_details != None or payload_delete_documents != None:
#                 payload_query = db.execute(""" SELECT lease_documents FROM space.leases WHERE lease_uid = \'""" + key_uid + """\'; """)     # Current Documents
#                 # print("1: ", payload_query)
#                 # print("2: ", payload_query['result'], type(payload_query['result']))
#                 # if payload_query['result']: print("3: ", payload_query['result'][0] ) 
#                 # if payload_query['result']: print("4: ", payload_query['result'][0]['lease_documents'], type(payload_query['result'][0]['lease_documents']))
#                 payload_documents = payload_query['result'][0]['lease_documents'] if payload_query['result'] else "None"
#             else:
#                 return payload

#         elif 'maintenance_quote_uid' in key:
#             print("Quote Key passed")
#             key_type = 'quotes'
#             key_uid = key['maintenance_quote_uid']
#             payload_changed_documents = payload.pop('quote_documents', None)                # Current Documents     (if there is a change in a current document)
#             payload_document_details = payload.pop('quote_documents_details', None)         # New Documents
#             payload_delete_documents = payload.pop('delete_documents', None)                # Documents to Delete
#             if payload_changed_documents != None or payload_document_details != None or payload_delete_documents != None:
#                 payload_query =  db.execute(""" SELECT quote_documents FROM space.maintenanceQuotes WHERE maintenance_quote_uid = \'""" + key_uid + """\'; """)                # Current Documents
#                 payload_documents = payload_query['result'][0]['quote_documents'] if payload_query['result'] else "None"
#             else:
#                 return payload

#         elif 'tenant_uid' in key:
#             print("Tenant Key passed")
#             key_type = 'tenants'
#             key_uid = key['tenant_uid']
#             payload_changed_documents = payload.pop('tenant_documents', None)                # Current Documents     (if there is a change in a current document)
#             payload_document_details = payload.pop('tenant_documents_details', None)         # New Documents
#             payload_delete_documents = payload.pop('delete_documents', None)                     # Documents to Delete
#             if payload_changed_documents != None or payload_document_details != None or payload_delete_documents != None:
#                 payload_query = db.execute(""" SELECT tenant_documents FROM space.tenantProfileInfo WHERE tenant_uid = \'""" + key_uid + """\'; """)                 # Current Documents
#                 payload_documents = payload_query['result'][0]['tenant_documents'] if payload_query['result'] else "None"
#             else:
#                 return payload

#         elif 'business_uid' in key:
#             print("Business Key passed")
#             key_type = 'business'
#             key_uid = key['business_uid']
#             payload_changed_documents = payload.pop('business_documents', None)                # Current Documents     (if there is a change in a current document)
#             payload_document_details = payload.pop('business_documents_details', None)         # New Documents
#             payload_delete_documents = payload.pop('delete_documents', None)                   # Documents to Delete
#             if payload_changed_documents != None or payload_document_details != None or payload_delete_documents != None:
#                 payload_query = db.execute(""" SELECT business_documents FROM space.businessProfileInfo WHERE business_uid = \'""" + key_uid + """\'; """)                # Current Documents
#                 payload_documents = payload_query['result'][0]['business_documents'] if payload_query['result'] else "None"                                          
#             else:
#                 return payload

#         else:
#             print("No UID found in key")
#             return

#         print("\nkey_type: ", key_type, type(key_type))
#         print("key_uid: ", key_uid, type(key_uid))
#         print("payload_documents: ", payload_documents, type(payload_documents))                            # Current Documents
#         print("payload_changed_documents: ", payload_changed_documents, type(payload_changed_documents))    # Documents being Changed
#         print("payload_document_details: ", payload_document_details, type(payload_document_details))       # New Documents  
#         print("payload_documents delete: ", payload_delete_documents, type(payload_delete_documents))       # Documents to Delete
        
#         print("Verified Add or Delete Documents in Payload")


#         # Put current db files into current_documents
#         current_documents = []
#         print("\nAbout to process CURRENT documents in database;")
#         if payload_documents not in {None, '', 'null'}:
#             print("Payload Documents: ", payload_documents)
#             current_documents =ast.literal_eval(payload_documents)
#             print("Current documents: ", current_documents, type(current_documents))
#         print("processed current documents")


#         # Replace current_document details with changed_document details
#         print("\nAbout to process CHANGED documents in database;")
#         # [{"link":"https://s3-us-west-1.amazonaws.com/io-pm/contracts/010-000001/file_0_20240827021719Z","type":"application/pdf","filename":"Sample Document 5.pdf"}]
#         # Get Changed documents in a list
#         if payload_changed_documents not in {None, '', 'null'}:
#             changed_documents = json.loads(payload_changed_documents)
#             print("changed_documents: ", changed_documents, type(changed_documents))

#             try:
#                 list2_dict = {doc['link']: doc for doc in changed_documents}
#                 current_documents = [list2_dict.get(doc['link'], doc) for doc in current_documents]
#                 print(current_documents)
#             except:
#                 print("No Current Documents")
            

#         print("processed changed documents")
        

#         # Put New Document Details into document_details
#         print("\nAbout to process NEW documents in database;")
#         if payload_document_details not in {None, '', 'null'}:
#             documents_details = json.loads(payload_document_details)
#             print("documents_details: ", documents_details, type(documents_details))
#         print("processed new documents")

#         # Initialize documents
#         documents = []
#         i = 0
#         documentFiles = {}

#         print("here 2 - About to process ADDED Documents")
        
#         # ADD Documents
#         while True:
#             filename = f'file_{i}'
#             print("\nPut file into Filename: ", filename) 
#             file = request.files.get(filename)
#             print("File:" , file)    
#             s3Link = payload.get(filename)
#             print("S3Link: ", s3Link)

#             if file:
#                 print("In File if Statement")
#                 documentFiles[filename] = file
#                 unique_filename = filename + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
#                 doc_key = f'{key_type}/{key_uid}/{unique_filename}'
#                 # This calls the uploadImage function that generates the S3 link
#                 document = uploadImage(file, doc_key, '')  # This returns the document http link
#                 print("Document after upload: ", document)

#                 print("docObject: ", file)
#                 print("docObject: ", file.mimetype)
#                 print("docObject: ", file.filename)
#                 print("docObject: ", documents_details[i]['contentType'])

#                 docObject = {}
#                 docObject["link"] = document
#                 docObject["filename"] = file.filename
#                 docObject["contentType"] = documents_details[i]['contentType']
#                 docObject["fileType"] = file.mimetype
#                 print("Doc Object: ", docObject)

#                 documents.append(docObject)


#             elif s3Link:
#                 documentFiles[filename] = s3Link
#                 documents.append(s3Link)

            
#             else:
#                 break
#             i += 1
        
#         print("Documents after loop: ", documents)
#         if documents != []:
#             current_documents.extend(documents)
#             # if key_type == 'contracts': payload['contract_documents'] = json.dumps(current_documents) 
#             # if key_type == 'leases': payload['lease_documents'] = json.dumps(current_documents) 
#             # if key_type == 'quotes': payload['quote_documents'] = json.dumps(current_documents) 
#             # if key_type == 'tenants': payload['tenant_documents'] = json.dumps(current_documents) 
#             # if key_type == 'business': payload['business_documents'] = json.dumps(current_documents) 

#         print("processed ADDED documents")

#         # Delete Documents
#         print("\nAbout to process DELETED documents in database;")
#         if payload_delete_documents:
#             print("In document delete: ", payload_delete_documents, type( payload_delete_documents))
#             delete_documents = ast.literal_eval(payload_delete_documents)
#             print("After ast: ", delete_documents, type(delete_documents), len(delete_documents))
#             for document in delete_documents:
#                 # print("Document to Delete: ", document, type(document))
#                 # print("Payload Doc:", current_documents, type(current_documents))
#                 # print("Current documents before deletion:", [doc['link'] for doc in current_documents])

#                 # Delete from db list assuming it is in db list
#                 try:
#                     current_documents = [doc for doc in current_documents if doc['link'] != document]
#                 except:
#                     print("Document not in list")

#                 #  Delete from S3 Bucket
#                 try:
#                     delete_key = document.split('io-pm/', 1)[1]
#                     # print("Delete key", delete_key)
#                     deleteImage(delete_key)
#                 except: 
#                     print("could not delete from S3")
#         print("processed DELETED documents")
            
#         print("\nCurrent Images in Function: ", current_documents, type(current_documents))
#         # print("Key Type: ", key_type)
#         if key_type == 'contracts': payload['contract_documents'] = json.dumps(current_documents)
#         if key_type == 'leases': payload['lease_documents'] = json.dumps(current_documents)
#         if key_type == 'quotes': payload['quote_documents'] = json.dumps(current_documents)
#         if key_type == 'tenants': payload['tenant_documents'] = json.dumps(current_documents)
#         if key_type == 'business': payload['business_documents'] = json.dumps(current_documents) 
            
        
#         print("Payload before return: ", payload)
#         return payload



# --------------- DATABASE CONFIGUATION ------------------
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
        # print("In execute.  SQL: ", sql)
        # print("In execute.  args: ",args)
        # print("In execute.  cmd: ",cmd)
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
                    # print('IN GET')
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
            # print(sql % where)
            response = self.execute(sql, where, 'get')
        except Exception as e:
            print(e)
        return response

    # def insert(self, table, object):
    #     response = {}
    #     try:
    #         sql = f'INSERT INTO {table} SET '
    #         for i, key in enumerate(object.keys()):
    #             sql += f'{key} = %({key})s'
    #             if i != len(object.keys()) - 1:
    #                 sql += ', '
    #         print(sql)
    #         # print(object)
    #         response = self.execute(sql, object, 'post')
    #     except Exception as e:
    #         print(e)
    #     return response
    
    def insert(self, table, object):
        response = {}
        try:
            sql = f'INSERT INTO {table} SET '
            debug_sql = f'INSERT INTO {table} SET '

            single_quote = "'"
            
            for key in object.keys():
                sql += f'{key} = %({key})s, '
                
                # Add to debug SQL with formatted values
                value = object[key]
                if value is None:
                    formatted_value = 'NULL'
                elif isinstance(value, (int, float, bool)):
                    formatted_value = str(value)
                else:
                    # Escape single quotes and wrap in quotes
                    formatted_value = f"{single_quote}{str(value).replace(single_quote, single_quote*2)}{single_quote}"

                debug_sql += f'{key} = {formatted_value}, '
            
            # Remove trailing commas and finalize SQL
            sql = sql.rstrip(', ')
            debug_sql = debug_sql.rstrip(', ')
            
            # print("Executing SQL:", sql)
            # print("Debug SQL:", debug_sql)
            
            response = self.execute(sql, object, 'post')
            
        except Exception as e:
            print(f"Database Error: {str(e)}")
            response = {'error': str(e)}
            
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
            # print("SQL Query: ", sql, object)
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