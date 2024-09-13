from flask import jsonify
from flask_restful import Resource

from data import connect


class Match(Resource):

    def get(self, user_uid):

        with connect() as db:
            response = db.select('users', where={'user_uid': user_uid}, cols='user_prefer_age_min, user_prefer_age_max, user_prefer_height_min, user_prefer_distance, user_prefer_gender, user_latitude, user_longitude, user_open_to, user_height, user_gender, user_age, user_sexuality')

            response = response['result'][0]

                                #             user_uid, 
                                # user_first_name,
                                # user_last_name,
                                # user_age,
                                # user_gender,
                                # user_general_interests,
                                # user_date_interests,    
                                # user_profile_bio,
                                # user_height,
                                # user_star_sign,
                                # user_education,
                                # user_body_composition,
                                # user_job,
                                # user_smoking,
                                # user_nationality,
                                # user_photo_url,
                                # user_suburb,
                                # user_video_url,

            # Using Haversine formula
            query = f'''SELECT *, 
                                (6371 * acos(
                                    cos(radians("{response['user_latitude']}")) * cos(radians(user_latitude)) * 
                                    cos(radians(user_longitude) - radians("{response['user_longitude']}")) + 
                                    sin(radians("{response['user_latitude']}")) * sin(radians(user_latitude))
                                )) AS distance
                        FROM mmu.users
                        WHERE user_uid != "{user_uid}" AND user_gender = "{response['user_prefer_gender']}" AND user_height >= "{response['user_prefer_height_min']}" AND user_age BETWEEN {response['user_prefer_age_min']} AND {response['user_prefer_age_max']} AND user_sexuality = "{response['user_open_to']}"
                        HAVING distance < {response['user_prefer_distance']}
                        ORDER BY distance;'''
            
            matchQuery = db.execute(query)
            result = []
            for user in matchQuery['result']:
                if (user['user_prefer_gender'] == response['user_gender'] and 
                    user['user_prefer_height_min'] <= response['user_height'] and 
                    user['user_prefer_age_min']<=response['user_age']<=user['user_prefer_age_max'] and 
                    user['user_open_to'] == response['user_sexuality']):
                    result.append(user)


        return jsonify({
            "message": "Successfully executed SQL query",
            "code": 200,
            "result": result})