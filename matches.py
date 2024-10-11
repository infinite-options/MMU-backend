from flask import jsonify, make_response
from flask_restful import Resource
import json

from data import connect
import ast
import math

def get_matches_sexuality_open_to(current_user_data, user_uid):
    print(" \n\t In Sexuality Open To Function \n")
    try:
        current_user_prefer_gender = current_user_data['user_prefer_gender']

        current_user_open_to = ast.literal_eval(current_user_data['user_open_to'])
        current_user_open_to = ', '.join(f"'{item}'" for item in current_user_open_to)
        if not current_user_prefer_gender or current_user_prefer_gender is None:
            current_user_prefer_gender = "'Male','Female','Non-Binary'"
        else:
            current_user_prefer_gender = f"'{current_user_prefer_gender}'"
        
        with connect() as db:
            query = f'''SELECT *
                    FROM mmu.users
                    WHERE user_uid != "{user_uid}"
                    AND user_gender IN ({current_user_prefer_gender})
                    AND user_sexuality IN ({current_user_open_to})
                    '''

            matched_users_response = db.execute(query, cmd='get')

            if len(matched_users_response['result']) == 0:
                return (False, matched_users_response)
            
            return (True, matched_users_response)
        
    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches Sexuality"
        })

def calculate_distance(current_user_lat, current_user_long, user_lat, user_long):
    
    lat1 = math.radians(float(current_user_lat))
    lon1 = math.radians(float(current_user_long))
    lat2 = math.radians(float(user_lat))
    lon2 = math.radians(float(user_long))

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    R = 6371.0

    distance = R * c

    return distance

def get_matches_age_height_distance(current_user_data, matches):
    print("\n\n\t in age height \n")
    try:
        current_user_min_age_preference = current_user_data['user_prefer_age_min']
        current_user_max_age_preference = current_user_data['user_prefer_age_max']
        current_user_min_height_preference = current_user_data['user_prefer_height_min']
        current_user_max_distance_preference = current_user_data['user_prefer_distance']
        current_user_latitude = current_user_data['user_latitude']
        current_user_longitude = current_user_data['user_longitude']

        result = []

        for match in matches:
            distance = calculate_distance(current_user_latitude, current_user_longitude, match['user_latitude'], match['user_longitude'])
            match['distance'] = distance

            if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference and
                int(match['user_height']) >= int(current_user_min_height_preference) and
                distance <= current_user_max_distance_preference
                ):
                result.append(match)

        return result
    
    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches age height distance"
        })


def suggest_age_min(current_user_data, matches):
    print("In age min")
    current_user_min_age_preference = current_user_data['user_prefer_age_min']
    current_user_max_age_preference = current_user_data['user_prefer_age_max']
    current_user_min_height_preference = current_user_data['user_prefer_height_min']
    current_user_max_distance_preference = current_user_data['user_prefer_distance']

    matches.sort(key= lambda x: x['user_age'], reverse = True)
    for age_min in range(current_user_min_age_preference, 17, -1):
        for match in matches:
            if (age_min <= match['user_age'] <= current_user_max_age_preference and
                match['user_height'] >= current_user_min_height_preference and
                match['distance'] <= current_user_max_distance_preference
                ):
                    return age_min

    return 0

def suggest_age_max(current_user_data, matches):
    print("In age max")
    current_user_min_age_preference = current_user_data['user_prefer_age_min']
    current_user_max_age_preference = current_user_data['user_prefer_age_max']
    current_user_min_height_preference = current_user_data['user_prefer_height_min']
    current_user_max_distance_preference = current_user_data['user_prefer_distance']

    matches.sort(key= lambda x: x['user_age'])
    for age_max in range(current_user_max_age_preference, 80):
        for match in matches:

            if (current_user_min_age_preference <= match['user_age'] <= age_max and
                match['user_height'] >= current_user_min_height_preference and
                match['distance'] <= current_user_max_distance_preference
                ):
                    return age_max
    
    return 0

def suggest_height(current_user_data, matches):
    print("In height")
    

    current_user_min_age_preference = current_user_data['user_prefer_age_min']
    current_user_max_age_preference = current_user_data['user_prefer_age_max']
    current_user_min_height_preference = current_user_data['user_prefer_height_min']
    current_user_max_distance_preference = current_user_data['user_prefer_distance']
    
    matches.sort(key= lambda x: x['user_height'], reverse=True)
    for height in range(int(current_user_min_height_preference), 50, -1):
        for match in matches:
            
            if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference and
                int(match['user_height']) >= height and
                match['distance'] <= current_user_max_distance_preference
                ):
                    return height
    return 0

def suggest_distance(current_user_data, matches):
    print("In distance")
    current_user_min_age_preference = current_user_data['user_prefer_age_min']
    current_user_max_age_preference = current_user_data['user_prefer_age_max']
    current_user_min_height_preference = current_user_data['user_prefer_height_min']
    current_user_max_distance_preference = current_user_data['user_prefer_distance']

    matches.sort(key= lambda x: x['distance'])
    for max_distance in range(current_user_max_distance_preference, 250):
        for match in matches:

            if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference and
                match['user_height'] >= current_user_min_height_preference and
                match['distance'] <= max_distance
                ):
                    return max_distance
    
    return 0

class Match(Resource):

    def get(self, user_uid):
        print(" In Get ")
        try:
            with connect() as db:

                current_user = db.select('users', where={'user_uid': user_uid})
                    
                if not current_user['result']:
                    return make_response(jsonify({
                        "message": f"User id {user_uid} doesn't exists"
                    }), 400)
                
                current_user_data = current_user['result'][0]
                print("Got the current user's information")
                print(current_user_data)

                check, response = get_matches_sexuality_open_to(current_user_data, user_uid)

                if not check:
                    return jsonify({
                        "message": "No Matches found because of preferred gender or open to list"
                    })

                result =  get_matches_age_height_distance(current_user_data, response['result'])

                if not result:

                    final_response = {}
                    final_response['message'] = "No results were found. Please try changing preferences using the following suggestions"

                    age_min_suggestions = suggest_age_min(current_user_data, response['result'])
                    age_max_suggestions = suggest_age_max(current_user_data, response['result'])
                    height_suggestions = suggest_height(current_user_data, response['result'])
                    distance_suggestions = suggest_distance(current_user_data, response['result'])


                    if (age_min_suggestions):
                        final_response['Set preferred minimum age to'] = age_min_suggestions
                    if (age_max_suggestions):
                        final_response['Set preferred maximum age to'] = age_max_suggestions
                    if (height_suggestions):
                        final_response['Set preferred minimum height to'] = height_suggestions
                    if (distance_suggestions):
                        final_response['Set preferred maximum distance to'] = distance_suggestions

                    if len(final_response.keys()) == 1:
                        final_response['message'] = "No results were found due to 2 or more preferences"

                    return final_response
                
                # Matching 2 way
                final_result = []
                for user in result:
                    if (user['user_prefer_age_min'] <= current_user_data['user_age'] <= user['user_prefer_age_max'] and
                        current_user_data['user_height'] >= user['user_prefer_height_min'] and
                        current_user_data['user_sexuality'] in ast.literal_eval(user['user_open_to'])
                        ):
                        final_result.append(user)
                
                
                if not final_result:
                    return jsonify({
                        "message": "No result found because of 2 way matching",
                        "result of 1 way match": result
                    })
                else:
                    final_result.sort(key= lambda x: x['distance'])
                    return jsonify({
                        "message": "Matches Found",
                        "result": final_result,
                    })
        except:
            return jsonify({
                "code": 400,
                "message": "There was an error while running the matching algorithm"
            })