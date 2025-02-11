from flask_restful import Resource
from flask import jsonify, make_response, request, json
import requests

from data import connect

from announcements import Announcements

class Likes(Resource):

    def get(self, user_id):
        response = {}
        response['code'] = 200
        response['message'] = "Successfully executed SQL query"
        response['result'] = []
        
        with connect() as db:

            try:

                # People who Match (Matched Results)
                # likeQuery = f'''
                #     -- PEOPLE WHO MATCH
                #     SELECT l1.*, l2.like_uid , users.*, meet.*
                #     FROM mmu.likes l1
                #     JOIN mmu.likes l2 ON l1.liker_user_id = l2.liked_user_id
                #     LEFT JOIN mmu.users ON l1.liked_user_id = user_uid
                #     LEFT JOIN mmu.meet ON (l1.liker_user_id = meet_user_id OR l1.liker_user_id = meet_date_user_id)
                #     -- WHERE l1.liker_user_id = '100-000307'
                #     WHERE l1.liker_user_id = "{user_id}"
                #     '''
                # result = db.execute(likeQuery)
                # response['matched_results'] = result['result']

                # Matched Results
                likeQuery = f'''
                                SELECT *
                                FROM (
                                    SELECT l1.like_uid, 
                                        u.user_uid, 
                                        u.user_email_id, 
                                        u.user_first_name, 
                                        u.user_last_name, 
                                        u.user_age, 
                                        u.user_gender,
                                        u.user_photo_url
                                    FROM mmu.likes l1
                                    LEFT JOIN mmu.users u ON l1.liked_user_id = u.user_uid
                                    -- WHERE l1.liker_user_id = "100-000307" 
                                    WHERE l1.liker_user_id = "{user_id}"
                                    AND EXISTS (
                                        SELECT 1
                                        FROM mmu.likes l2
                                        WHERE l2.liker_user_id = l1.liked_user_id
                                        AND l2.liked_user_id = l1.liker_user_id
                                    )
                                ) AS matches  -- Subquery alias placement fixed
                                LEFT JOIN mmu.meet m1 
                                    ON matches.user_uid = m1.meet_date_user_id 
                                    -- AND m1.meet_user_id = "100-000307"
                                    AND m1.meet_user_id = "{user_id}"
                                LEFT JOIN mmu.meet m2 
                                    ON matches.user_uid = m2.meet_user_id 
                                    -- AND m2.meet_date_user_id = "100-000307"
                                    AND m2.meet_date_user_id = "{user_id}"
                                '''
                result = db.execute(likeQuery)
                response['matched_results'] = result['result']
                response['result'].extend([{'matched_results': result['result']}])


                # People who I like (People whom you selected)
                # likeQuery = f'''
                #         -- PEOPLE WHO I LIKE
                #         SELECT * 
                #         FROM mmu.likes
                #         LEFT JOIN mmu.users ON liked_user_id = user_uid
                #         -- WHERE liker_user_id = '100-000307'
                #         WHERE liker_user_id = "{user_id}"
                #         '''
                # result = db.execute(likeQuery)
                # response['people_whom_you_selected'] = result['result']
                
                # People whom you selected
                likeQuery = f'''SELECT l1.like_uid, 
                                       u.user_uid, 
                                       u.user_email_id, 
                                       u.user_first_name, 
                                       u.user_last_name, 
                                       u.user_age, 
                                       u.user_gender,
                                       u.user_photo_url
                                FROM mmu.likes l1
                                LEFT JOIN mmu.users u ON l1.liked_user_id = u.user_uid
                                WHERE l1.liker_user_id = "{user_id}" AND NOT EXISTS (
                                    SELECT 1
                                    FROM mmu.likes l2
                                    WHERE l2.liker_user_id = l1.liked_user_id
                                        AND l2.liked_user_id = l1.liker_user_id
                                );'''
                result = db.execute(likeQuery)
                response['people_whom_you_selected'] = result['result']
                response['result'].extend([{'people_whom_you_selected': result['result']}])

                # People who like me (People who selected you)
                # likeQuery = f'''
                #         -- PEOPLE WHO LIKE ME
                #         SELECT * 
                #         FROM mmu.likes
                #         LEFT JOIN mmu.users ON liker_user_id = user_uid
                #         -- WHERE liked_user_id = '100-000307'
                #         WHERE liked_user_id = "{user_id}"
                #         '''
                # result = db.execute(likeQuery)
                # response['people_who_selected_you'] = result['result']


                # People who selected you
                likeQuery = f'''SELECT l1.like_uid, 
                                       u.user_uid, 
                                       u.user_email_id, 
                                       u.user_first_name, 
                                       u.user_last_name, 
                                       u.user_age, 
                                       u.user_gender,
                                       u.user_photo_url
                                FROM mmu.likes l1
                                LEFT JOIN mmu.users u ON l1.liker_user_id = u.user_uid
                                WHERE l1.liked_user_id = "{user_id}" AND NOT EXISTS (
                                    SELECT 1
                                    FROM mmu.likes l2
                                    WHERE l2.liker_user_id = l1.liked_user_id
                                        AND l2.liked_user_id = l1.liker_user_id
                                );'''
                result = db.execute(likeQuery)
                response['people_who_selected_you'] = result['result']
                response['result'].extend([{'people_who_selected_you': result['result']}])

            except Exception as e:
                return make_response(jsonify({
                    "code": 400,
                    "message": "Error in fetching data in people who you selected",
                    "error": e
                }), 400)

            return response
    
    def post(self):

        try:
            with connect() as db:
                payload = request.form.to_dict()
                print("In Likes: ", payload)

                try:
                    checkQuery = db.select('likes', where=payload)
                    if checkQuery['result']:
                        checkQuery["message"] = "You've already liked this user"

                        return checkQuery

                except:
                    return jsonify({
                        "message": "Error in check query"
                    })
                
                new_like_uid = db.call(procedure='new_like_uid')
                print(new_like_uid)

                payload['like_uid'] = new_like_uid['result'][0]['new_id']

                likeQuery = db.insert('likes', payload)
                likeQuery['like_uid'] = new_like_uid['result'][0]['new_id']

                userQuery = db.execute(f'''SELECT user_first_name FROM mmu.users WHERE user_uid = "{payload['liker_user_id']}"''', cmd='get')
                print(userQuery)
                userName = userQuery['result'][0]['user_first_name']

                data = {
                    "announcement_title": "New Like",
                    "announcement_message": f"You were liked by {userName}",
                    "announcement_mode": "Like",
                    "announcement_receiver": [f"{payload['liked_user_id']}"]
                }

                try:
                    # response = requests.post("http://127.0.0.1:4000/announcements", json=data)
                    response = Announcements().post(data)
                except:
                    return jsonify({
                        "message": "Error in anouncement API (from Likes)",
                        "code": 400
                    })
                
            return likeQuery


        except Exception as e:
            return make_response(jsonify({
                "code": 400,
                "message": "Error in post data method",
                "error": e
            }), 400)
    
    def delete(self):

        try:
            liker_user_id = request.form.get('liker_user_id')
            liked_user_id = request.form.get('liked_user_id')
            with connect() as db:
                likeQuery = f'''DELETE FROM mmu.likes
                            WHERE liker_user_id = "{liker_user_id}" AND liked_user_id = "{liked_user_id}";'''

                response = db.delete(likeQuery)
            
            return response
                
        except Exception as e:
            return make_response(jsonify({
                "code": 400,
                "message": "Error in delete data method",
                "error": e
            }), 400)