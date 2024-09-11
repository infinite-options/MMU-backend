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
from data import connect, disconnect

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('S3_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET'),
    region_name=os.getenv('S3_REGION')
)


def deleteImage(key):
    bucket = 'io-mmu'
    try:
        print("Before Delete: ", bucket, key)
        delete_file = s3.delete_object(
            Bucket=bucket,
            Key=key
        )
        print("After Delete: ", delete_file)
        print("After Delete Status Code: ", delete_file['ResponseMetadata']['HTTPStatusCode'])
        print(f"Deleted existing file {key} from bucket {bucket}")
        return True
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"File {key} does not exist in bucket {bucket}")
        else:
            print(f"Error deleting file {key} from bucket {bucket}: {e}")
        return False


def uploadImage(file, key, content):
    print("\nIn Upload Image: ")
    # print("File: ", file)
    # print("Key: ", key)
    # print("Content: ", content)
    bucket = 'io-mmu'

    if isinstance(file, FileStorage): 
        print("In Upload Image isInstance File Storage: ", FileStorage)
        file.stream.seek(0)
        file_content = file.stream.read()
        content_type, _ = mimetypes.guess_type(file.filename)
        contentType = content_type if content_type else 'application/octet-stream'  # Fallback if MIME type is not detected
        print("In Upload Image contentType: ", contentType) # This returns jpeg, png, ect

    elif isinstance(file, StreamingBody):
        print("In Upload Image isInstance Streaming Body")
        file_content = file.read()
        contentType = content
        print("In Upload Image contentType: ", contentType)
        # Set content type based on your logic or metadata
        # Example: contentType = 'image/jpeg' or other appropriate content type


    if file_content:
        # Return hexedemical file info
        filename = f'https://s3-us-west-1.amazonaws.com/{bucket}/{key}'
        # print("Before Upload: ", bucket, key, filename, contentType)

        # This Statement Actually uploads the file into S3
        upload_file = s3.put_object(
            Bucket=bucket,
            Body=file_content,
            Key=key,
            ContentType=contentType
        )
        print("After Upload: ", upload_file)
        print("After Upload Status Code: ", upload_file['ResponseMetadata']['HTTPStatusCode'])
        print("Derived Filename: ", filename)
        return filename
    
    return None

# --------------- PROCESS IMAGES ------------------

def processImage(key, payload):

    print("\nIn Process Image: ", payload)

    response = {}

    with connect() as db:
        

        if 'user_uid' in key:
            print("\n\n-----------User Key passed----------------\n\n")
            key_type = 'users'
            key_uid = key['user_uid']
            payload_delete_images = payload.pop('delete_images', None)  # Images to Delete

            #  GET images sent by Frontend. (img_0, img_1, ..)
            if 'img_0' in request.files or payload_delete_images != None: 
                # Current Images in the database  
                payload_query = db.execute(""" SELECT user_photo_url FROM mmu.users WHERE user_uid = \'""" + key_uid + """\'; """)     
                
                payload_images = payload_query['result'][0]['user_photo_url'] 
                payload_fav_images = payload.get("user_favorite_photo") #or payload.get("img_favorite")   # (PUT & POST)
            else:
                return payload

        else:
            print("No UID found in key")
            return
        

        # print("key_type: ", key_type, type(key_type))
        # print("key_uid: ", key_uid, type(key_uid))
        # print("payload_images: ", payload_images, type(payload_images))        
        # print("payload_images delete: ", payload_delete_images, type(payload_delete_images))

        # Check if images already exist
        # Put current db images into current_images
        current_images = []
        if payload_images is not None and payload_images != '' and payload_images != 'null':
            print("---Payload Images: ", payload_images)
            current_images =ast.literal_eval(payload_images)
            print('\n\n\n Current Images: ', current_images, '\n\n\n')
            print("---Current images: ", current_images, type(current_images))

        # Check if images are being added OR deleted
        images = []
        i = 0
        imageFiles = {}

        print("\n\n\n--------------About to Add Images--------------\n\n\n")

        # ADD Images
        while True:
            filename = f'img_{i}'
            # print("\n\nPut image file into Filename: ", filename)

            file = request.files.get(filename)
            # print("\n\nFile:" , file)        

            s3Link = payload.get(filename) # Used for fav images
            # print("\n\nS3Link: ", s3Link)

            if file:
                # print("\n\nIn 'if file' Statement")
                imageFiles[filename] = file
                unique_filename = filename + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
                image_key = f'{key_type}/{key_uid}/photos/{unique_filename}'

                # This calls the uploadImage function that generates the S3 link
                image = uploadImage(file, image_key, '')
                
                # print("\n\nImage after upload: ", image)

                images.append(image)

                if filename == payload_fav_images:
                    payload["user_favorite_photo"] = json.dumps(image)

            elif s3Link:
                imageFiles[filename] = s3Link
                images.append(s3Link)

                if filename == payload_fav_images:
                    if key_type == 'user_uid': payload["user_favorite_photo"] = image
            
            else:
                break
            i += 1
        
        print("Images after loop: ", images)
        if images != []:
            current_images.extend(images)
            
        # try:
        #     file = request.files.get('user_video')
        #     if file:
        #         unique_filename = f"{key_uid}" + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
        #         image_key = f'{key_type}/{key_uid}/videos/{unique_filename}'

        #         video = uploadImage(file, image_key, '')
        # except Exception as e:
        #     return (e)

        # Delete Images
        # if payload_delete_images:
        #     print("In image delete: ", payload_delete_images, type( payload_delete_images))
        #     delete_images = ast.literal_eval(payload_delete_images)
        #     print("After ast: ", delete_images, type(delete_images), len(delete_images))
        #     for image in delete_images:
        #         # print("Image to Delete: ", image, type(image))
        #         # print("Payload Image:", current_images, type(current_images))
        #         # print("Current images before deletion:", [doc['link'] for doc in current_images])

        #         # Delete from db list assuming it is in db list
        #         try:
        #             current_images.remove(image)   # Works becuase this is an Exact match
        #         except:
        #             print("Image not in list")

        #         #  Delete from S3 Bucket
        #         try:
        #             delete_key = image.split('io-pm/', 1)[1]
        #             # print("Delete key", delete_key)
        #             deleteImage(delete_key)
        #         except: 
        #             print("could not delete from S3")
            
        # print("\n\nCurrent Images in Function: ", current_images, type(current_images))

        if key_type == 'users': payload['user_photo_url'] = json.dumps(current_images) 
        # payload['user_video_url'] = json.dumps(video) 
        # payload.pop('user_favorite_image')

        print("\n\nPayload before return: ", payload)
        return payload