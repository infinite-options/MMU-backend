from flask import request, make_response, jsonify

import os
import pymysql
import datetime
import json
import boto3
from boto3.s3.transfer import TransferConfig
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


def upload_multipart(file_content, bucket, key, content_type):
    print("\nIn Upload Multipart:")
    try:
        # Step 1: Initiate the multipart upload
        multipart_upload = s3.create_multipart_upload(
            Bucket=bucket,
            Key=key,
            ACL='public-read',
            ContentType=content_type
        )
        upload_id = multipart_upload['UploadId']
        print("Multipart upload initiated with UploadId:", upload_id)
        # Step 2: Upload parts
        parts = []
        part_number = 1
        chunk_size = 5 * 1024 * 1024  # Set chunk size (5 MB)
        # Split file content into chunks
        for i in range(0, len(file_content), chunk_size):
            chunk = file_content[i:i + chunk_size]
            response = s3.upload_part(
                Bucket=bucket,
                Key=key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=chunk
            )
            parts.append({'PartNumber': part_number, 'ETag': response['ETag']})
            print(f"Uploaded part {part_number}")
            part_number += 1
        # Step 3: Complete the multipart upload
        response = s3.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        print("Multipart upload completed successfully:", response)
        # Return the S3 file URL
        filename = f'https://{bucket}.s3.amazonaws.com/{key}'
        print("Derived Filename:", filename)
        return filename
    except Exception as e:
        # Abort the multipart upload in case of an error
        if 'upload_id' in locals():
            s3.abort_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id
            )
            print("Multipart upload aborted.")
        print("Error during multipart upload:", str(e))
        return None

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

        # config = TransferConfig(
        #     multipart_threshold=5 * 1024 * 1024,  # Files larger than 5 MB will be split
        #     multipart_chunksize=5 * 1024 * 1024   # Each part will be 5 MB
        # )

        # This Statement Actually uploads the file into S3
        # upload_file = s3.put_object(
        #     Bucket=bucket,
        #     Body=file_content,
        #     Key=key,
        #     ACL='public-read',
        #     ContentType=contentType,
        #     Config = config
        # )

        # Call the multipart upload function
        upload_file = upload_multipart(file_content, bucket, key, content_type)

        print("\nAfter Upload: ", upload_file)
        # print("After Upload Status Code: ", upload_file['ResponseMetadata']['HTTPStatusCode'])
        print("Derived Filename: ", filename)
        return filename
    
    return None

# --------------- PROCESS IMAGES ------------------

def processImage(key, payload):
    print("\nIn Process Image: ", payload)
    # print("Key Passed into processImage: ", key)
    response = {}
    # bucket = os.getenv('BUCKET_NAME')
    # payload_fav_images = None
    with connect() as db:
        
        if 'user_uid' in key:
            print("\n\n-----------User Key passed----------------\n\n")
            key_type = 'users'
            key_uid = key['user_uid']
            payload_delete_images = payload.pop('user_delete_photo', None)  # Images to Delete
            #  GET images sent by Frontend. (img_0, img_1, ..)
            if 'img_0' in request.files or 'user_video' in request.files or payload_delete_images != None: 
                # Current Images in the database  
                payload_query = db.execute(""" SELECT user_photo_url FROM mmu.users WHERE user_uid = \'""" + key_uid + """\'; """)     
                # print("2: ", payload_query['result'], type(payload_query['result']))
                if len(payload_query['result']) > 0:
                    print("4: ", payload_query.get('result', [{}])[0].get('user_photo_url', None))
                payload_images = payload_query['result'][0]['user_photo_url'] if payload_query['result'] else None  # Current Images from database
                payload_fav_images = payload.get("user_favorite_photo") #or payload.get("img_favorite")   # (PUT & POST)
            else:
                return payload

        else:
            print("No UID found in key")
            return
        print("Verified Add or Delete Images in Payload")

        # print("key_type: ", key_type, type(key_type))
        # print("key_uid: ", key_uid, type(key_uid))
        # print("payload_images: ", payload_images, type(payload_images))        
        print("payload_images delete: ", payload_delete_images, type(payload_delete_images))
        if key_type in ['users']: print("payload_fav_images: ", payload_fav_images, type(payload_fav_images))



        # Check if images already exist
        # Put current db images into current_images
        print("\nAbout to process CURRENT imagess in database")
        current_images = []
        if payload_images not in {None, '', 'null'}:
            print("---Payload Images: ", payload_images, type(payload_images))
            current_images =ast.literal_eval(payload_images)
            print("---Current images: ", current_images, type(current_images))
        print("processed current images ", current_images)

        video_file = request.files.get('user_video')

        # Check if images are being added OR deleted
        images = []
        i = 0
        imageFiles = {}
        video_count = 0



        # ADD Images
        print("\n\n\n--------------About to Add Images--------------\n")

        while True:
            filename = f'img_{i}'
            # print("\n\nPut image file into Filename: ", filename)
            file = request.files.get(filename)
            # print("\n\nFile:" , file)       
            s3Link = payload.get(filename) # Used for fav 
            # print("\nS3Link: ", s3Link) 

            
            if file:
                print("\n\nIn 'if file' Statement")
                imageFiles[filename] = file
                unique_filename = filename + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
                image_key = f'{key_type}/{key_uid}/photos/{unique_filename}'
                # This calls the uploadImage function that generates the S3 link
                image = uploadImage(file, image_key, '')
                # print("\nImage after upload: ", image)

                images.append(image)

                if filename == payload_fav_images:
                    payload["user_favorite_photo"] = image

            elif s3Link:
                imageFiles[filename] = s3Link
                images.append(s3Link)

                if filename == payload_fav_images:
                    payload["user_favorite_photo"] = s3Link
            
            elif video_file and video_count == 0:
                print("\n\nIn 'if video' Statement")
                video_query = db.execute(""" SELECT user_video_url FROM mmu.users WHERE user_uid = \'""" + key_uid + """\'; """)
                delete_video = video_query['result'][0]['user_video_url']
                unique_filename = f"{key_uid}" + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
                image_key = f'{key_type}/{key_uid}/videos/{unique_filename}'

                video = uploadImage(video_file, image_key, '')
                payload['user_video_url'] = json.dumps(video)

                try:
                    print('\n\n\n*****', delete_video, '\n\n\n*****')
                    if delete_video:
                        delete_video =ast.literal_eval(delete_video)
                        delete_key = delete_video.split('io-mmu/', 1)[1]
                        print("\n\nDelete key\n\n\n\n", delete_key)
                        deleteImage(delete_key)
                except: 
                    print("could not delete from S3")

                video_count += 1
            else:
                break
            i += 1
        
        print("Images after loop: ", images)
        if images != []:
            current_images.extend(images)
        
        print("processed ADDED documents")


        # Delete Images
        if payload_delete_images:
            print("\nAbout to process DELETED images in database;")
            print("In image delete: ", payload_delete_images, type( payload_delete_images))
            delete_images = ast.literal_eval(payload_delete_images)
            print("After ast: ", delete_images, type(delete_images), len(delete_images))
            for image in delete_images:
                # print("Image to Delete: ", image, type(image))
                # print("Payload Image:", current_images, type(current_images))
                # print("Current images before deletion:", [doc['link'] for doc in current_images])

                # Delete from db list assuming it is in db list
                try:
                    current_images.remove(image)   # Works becuase this is an Exact match
                except:
                    print("Image not in list")

                #  Delete from S3 Bucket
                try:
                    delete_key = image.split('io-mmu/', 1)[1]
                    # print("Delete key", delete_key)
                    deleteImage(delete_key)
                except: 
                    print("could not delete from S3")
            print("processed DELETED Images")

        print("\n\nCurrent Images in Function: ", current_images, type(current_images))

        if key_type == 'users': payload['user_photo_url'] = json.dumps(current_images) 
        # payload.pop('user_favorite_image')

        print("\n\nPayload before return: ", payload)
        return payload