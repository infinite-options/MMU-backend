from flask import jsonify, request
from flask_restful import Resource

from data import connect

# matches/user_uid
class Match(Resource):

    def get(self, user_uid):

        with connect() as db:
            response = db.select('users', where={'user_uid': user_uid}, cols='user_prefer_age_min, user_prefer_age_max, user_prefer_height_min, user_prefer_distance, user_prefer_gender, user_latitude,user_longitude,user_open_to')

            response = response['result'][0]

            # Using Haversine formula
            query = f'''SELECT * .user_uid, 
                                user_first_name,
                                user_last_name,
                                user_age,
                                user_gender,
                                user_general_interests,
                                user_date_interests,    
                                user_profile_bio,
                                user_height,
                                user_star_sign,
                                user_education,
                                user_body_composition,
                                user_job,
                                user_smoking,
                                user_nationality,
                                user_photo_url,
                                user_suburb,
                                user_video_url,
                                (6371 * acos(
                                    cos(radians("{response['user_latitude']}")) * cos(radians(user_latitude)) * 
                                    cos(radians(user_longitude) - radians("{response['user_longitude']}")) + 
                                    sin(radians("{response['user_latitude']}")) * sin(radians(user_latitude))
                                )) AS distance
                        FROM mmu.users
                        WHERE user_uid != "{user_uid}" AND user_gender = "{response['user_prefer_gender']}" AND user_height >= "{response['user_prefer_height_min']}" AND user_age BETWEEN {response['user_prefer_age_min']} AND {response['user_prefer_age_max']} AND user_sexuality = "{response['user_open_to']}"
                        HAVING distance < {response['user_prefer_distance']}
                        ORDER BY distance;'''
            
            response = db.execute(query)

        return response


    # def put(self):
    #     user_uid = request.form.get('user_uid')
    #     distance = request.form.get('distance')
    #     prefer_min_age = request.form.get('prefer_min_age')
    #     prefer_max_age = request.form.get('prefer_max_age')
    #     prefer_min_height = request.form.get('prefer_min_height')
    #     prefer_gender = request.form.get('prefer_gender')

    #     # add keys instead of direct VALUES
    #     # what to do if lat, long are like 47.6061° N, 122.3328° W
    #     # optimized approach

    #     with connect() as db:
            
    #         response = db.select('users', where={'user_uid': user_uid}, cols='user_latitude,user_longitude,user_open_to')
            
    #         response = response['result'][0]

    #         # Using Haversine formula
    #         query = f'''SELECT user_uid, 
    #                             user_first_name,
    #                             user_last_name,
    #                             user_age,
    #                             user_gender,
    #                             user_interests,
    #                             user_profile_bio,
    #                             user_height,
    #                             user_sign,
    #                             user_education,
    #                             user_body,
    #                             user_job,
    #                             user_smoking,
    #                             user_nationality,
    #                             user_photo_url,
    #                             user_suburb,
    #                             user_video_url,
    #                             (6371 * acos(
    #                                 cos(radians("{response['user_latitude']}")) * cos(radians(user_latitude)) * 
    #                                 cos(radians(user_longitude) - radians("{response['user_longitude']}")) + 
    #                                 sin(radians("{response['user_latitude']}")) * sin(radians(user_latitude))
    #                             )) AS distance
    #                     FROM mmu.users
    #                     WHERE user_uid != "{user_uid}" AND user_gender = "{prefer_gender}" AND user_height >= "{prefer_min_height}" AND user_age BETWEEN {prefer_min_age} AND {prefer_max_age} AND user_sexuality = "{response['user_open_to']}"
    #                     HAVING distance < {distance}
    #                     ORDER BY distance;'''
            
    #         response = db.execute(query)

    #     return response