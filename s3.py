from flask import request, make_response, jsonify

import requests
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
from flask_restful import Resource

bucket = os.getenv('BUCKET_NAME')
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('S3_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET'),
    region_name=os.getenv('S3_REGION')
)


# For Testing Purposes only - Not used in the program - Use this to apply S3Link and upload video to AWS S3
class Upload_Video(Resource):
    def post(self):
        # Get the presigned URL from form data
        presigned_url = request.form.get('presigned_url')
        video_file = request.files['user_video']

        print(presigned_url)
        print(video_file)
        
        # Save the file temporarily
        video_file_path = "/tmp/uploaded_video.mp4"
        video_file.save(video_file_path)
        
        # Upload the video using the presigned URL
        with open(video_file_path, 'rb') as file:
            # Send a PUT request to the presigned URL with the file data
            response = requests.put(  # Use requests.put instead of request.put
                presigned_url,
                data=file,
                headers={'Content-Type': 'video/mp4'}
            )
        
        # Check if the upload was successful
        if response.status_code in [200, 201, 204]:
            print(f"Video uploaded successfully. Status code: {response.status_code}")
            return {"status": "success", "code": response.status_code}, 200
        else:
            print(f"Upload failed. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return {"status": "failed", "code": response.status_code, "message": response.text}, 500

    

# # Function to generate a pre-signed URL
# def generate_presigned_url(file_name, file_type):
#     file_key = f"uploads/{uuid.uuid4()}-{file_name}"  # Unique file name
#     presigned_url = s3_client.generate_presigned_url(
#         "put_object",
#         Params={
#             "Bucket": S3_BUCKET,
#             "Key": file_key,
#             "ContentType": file_type
#         },
#         ExpiresIn=3600  # URL expires in 1 hour
#     )
#     return presigned_url, file_key

# # Function to store file metadata in MySQL
# def save_file_metadata(file_key, file_type):
#     try:
#         connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
#         cursor = connection.cursor()

#         sql = "INSERT INTO file_uploads (file_key, file_type) VALUES (%s, %s)"
#         cursor.execute(sql, (file_key, file_type))
#         connection.commit()

#         cursor.close()
#         connection.close()
#     except Exception as e:
#         print("Error saving to database:", e)

# # Actual API to generate link
# def S3Video_presigned_url():
#     data = request.json
#     file_name = data.get("file_name")
#     file_type = data.get("file_type")

#     if not file_name or not file_type:
#         return jsonify({"error": "Missing file_name or file_type"}), 400

#     presigned_url, file_key = generate_presigned_url(file_name, file_type)
    
#     # Optionally store metadata in MySQL
#     save_file_metadata(file_key, file_type)

#     return jsonify({"presigned_url": presigned_url, "file_key": file_key})

# Alternative API to generate link (Much better - eliminates need for File Name)

class Get_presigned_url(Resource):
    def post(self):    
    # def get_presigned_url():
        data = request.json
        key_uid = data.get("user_uid")
        file_type = data.get("user_video_filetype")
        print("S3 Link Inputs: ", key_uid, file_type)

        if not file_type:
            return jsonify({"error": "Missing file_type"}), 400

        # Generate a unique filename
        # file_key = f"videos/{uuid.uuid4()}.mp4"
        key_type = 'users'
        unique_filename = f"{key_uid}" + "_" + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
        image_key = f'{key_type}/{key_uid}/videos/{unique_filename}'
        print("File Name: ", unique_filename, image_key)


        # Create the pre-signed URL
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket":bucket,
                # "Key": file_key,
                "Key": f"users/{key_uid}/videos/{unique_filename}",
                "ContentType": file_type,
                "ACL": "public-read"
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        print("presigned URL: ", presigned_url)

        video_url = presigned_url.split('?')[0]

        # return jsonify({"presigned_url": presigned_url, "file_key": file_key})
        return jsonify({"url": presigned_url, "key": unique_filename, "videoUrl": video_url})


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
    # bucket = 'io-mmu'

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
            payload_delete_video = payload.pop('user_delete_video', None)  # Video to Delete
            print("Video to delete: ", payload_delete_video)
            #  GET images sent by Frontend. (img_0, img_1, ..)
            if 'img_0' in request.files or 'user_video' in request.files or payload_delete_images != None or payload_delete_video != None: 
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
        print("Video File: ", video_file)

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
                print("Video to delete: ", delete_video)
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

        if payload_delete_video:
            print("\nAbout to process DELETED video in database;")
            print("In video delete: ", payload_delete_video, type( payload_delete_video))
            delete_video = ast.literal_eval(payload_delete_video)
            print("After ast: ", delete_video, type(delete_video), len(delete_video))
            for video in delete_video:
                print("Video to Delete: ", video, type(video))
                # print("Payload Image:", current_images, type(current_images))
                # print("Current images before deletion:", [doc['link'] for doc in current_images])

                # Delete from db list assuming it is in db list
                # try:
                #     current_images.remove(video)   # Works becuase this is an Exact match
                # except:
                #     print("Image not in list")

                #  Delete from S3 Bucket
                try:
                    delete_key = video.split('io-mmu.s3.amazonaws.com/', 1)[1]
                    print("Delete key", delete_key)
                    deleteImage(delete_key)
                except: 
                    print("could not delete from S3")
            print("processed DELETED Images")


        print("\n\nCurrent Images in Function: ", current_images, type(current_images))

        if key_type == 'users': payload['user_photo_url'] = json.dumps(current_images) 
        # payload.pop('user_favorite_image')

        print("\n\nPayload before return: ", payload)
        return payload