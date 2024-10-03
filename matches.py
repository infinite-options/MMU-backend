from flask import jsonify, make_response
from flask_restful import Resource

from data import connect
import ast

class Match(Resource):

    def get(self, user_uid):
        
        with connect() as db:
            try:
                
                primary_user = db.select('users', where={'user_uid': user_uid})

                if not primary_user['result']:
                    return make_response(jsonify({
                        "message": f"User id {user_uid} doesn't exists"
                    }), 400)
                
                user = primary_user['result'][0]
                print('\n\n Information of primary user: \n', user, '\n\n')

                primary_user_open_to = ast.literal_eval(user['user_open_to'])
                formatted_user_open_to = ', '.join(f"'{item}'" for item in primary_user_open_to)

                if not user['user_prefer_gender'] or user['user_prefer_gender'] is None:
                    primary_user_prefer_gender = "'Male','Female','Non-Binary'"
                else:
                    primary_user_prefer_gender = f"'{user['user_prefer_gender']}'"
                
                # if not primary_user_prefer_gender or primary_user_prefer_gender == "None":
                #     print('\n\n In If')
                #     primary_user_prefer_gender = "'Male','Female','Non-Binary'"
                
                # get users that matches primary_user's preferences
                query = f'''SELECT *, 
                                    (6371 * acos(
                                        cos(radians("{user['user_latitude']}")) * cos(radians(user_latitude)) * 
                                        cos(radians(user_longitude) - radians("{user['user_longitude']}")) + 
                                        sin(radians("{user['user_latitude']}")) * sin(radians(user_latitude))
                                    )) AS distance
                            FROM mmu.users
                            WHERE user_uid != "{user_uid}"
                            AND user_height >= "{user['user_prefer_height_min']}"
                            AND user_gender IN ({primary_user_prefer_gender})
                            AND user_age BETWEEN {user['user_prefer_age_min']} AND {user['user_prefer_age_max']}
                            AND user_sexuality IN ({formatted_user_open_to})
                            HAVING distance < {user['user_prefer_distance']}
                            ORDER BY distance;'''

                matched_users = db.execute(query, cmd='get')

                if not matched_users['result']:
                    
                    query = f'''SELECT
                                    FLOOR(user_age / 10) * 10 AS min_age, 
                                    (FLOOR(user_age / 10) * 10 + 9) AS max_age,
                                    FLOOR(user_height / 10) * 10 AS min_height,
                                    FLOOR(6371 * acos(
                                        cos(radians("{user['user_latitude']}")) * cos(radians(user_latitude)) * 
                                        cos(radians(user_longitude) - radians("{user['user_longitude']}")) + 
                                        sin(radians("{user['user_latitude']}")) * sin(radians(user_latitude))
                                    )) AS min_distance,
                                    COUNT(*) AS user_count
                                FROM
                                    users
                                WHERE
                                    user_gender IN ({primary_user_prefer_gender})
                                GROUP BY FLOOR(user_age / 10)
                                ORDER BY user_count DESC;'''
                                                    
                    result = db.execute(query)
                    result["message"] = "No matching users found"
                    result["current_preferences"] = f"'user_prefered_age_min': {user['user_prefer_age_min']}, 'user_prefered_age_max': {user['user_prefer_age_max']}, 'user_prefer_height_min': {user['user_prefer_height_min']}, 'user_prefer_distance': {user['user_prefer_distance']}"
                    return jsonify(result)

                # matching it 2 way
                try:
                    print("In 2 way algorithm")
                    response = {}
                    result = []
                    for matched_user in matched_users['result']:
                        matcher_user_open_to = ast.literal_eval(matched_user['user_open_to'])

                        if (user['user_height'] >= matched_user['user_prefer_height_min'] and 
                            matched_user['user_prefer_age_min'] <= user['user_age'] <= matched_user['user_prefer_age_max'] and 
                            user['user_sexuality'] in matcher_user_open_to):

                            result.append(matched_user)

                    response['message'] = 'Algorithm ran successfully'
                    response['code'] = 200
                    response['result'] = result
                    
                except:
                    return jsonify({
                        "message": "error in 2 ways algorithm in the backend"
                    })

                return response

            except:
                return jsonify({
                    "message": "Error in algorithm"
                })