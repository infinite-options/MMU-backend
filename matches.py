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
        if not current_user_prefer_gender or current_user_prefer_gender is None or current_user_prefer_gender == "Either":
            current_user_prefer_gender = "'Male','Female'"
        else:
            current_user_prefer_gender = f"'{current_user_prefer_gender}'"
        
        with connect() as db:
            # query = f'''SELECT *
            #         FROM mmu.users
            #         WHERE user_uid != "{user_uid}"
            #         AND user_gender IN ({current_user_prefer_gender})
            #         -- AND user_sexuality IN ({current_user_open_to})
            #         '''
            query = f'''
                    SELECT u.* ,
                        if(l1.liked_user_id = "{user_uid}", 'YES', 'NO') AS "Likes",
                        if(l2.liker_user_id = "{user_uid}", 'YES', 'NO') AS "Liked by"
                    FROM mmu.users u
                    LEFT JOIN 
                        mmu.likes l1 ON u.user_uid = l1.liker_user_id AND l1.liked_user_id = "{user_uid}"
                    LEFT JOIN 
                        mmu.likes l2 ON u.user_uid = l2.liked_user_id AND l2.liker_user_id = "{user_uid}"
                    WHERE user_uid != "{user_uid}"
                    AND user_gender IN ({current_user_prefer_gender})
                    -- AND user_sexuality IN ({current_user_open_to})
                    '''
            # print(query)
            matched_users_response = db.execute(query, cmd='get')
            # print(matched_users_response)
            matched_users = [user['user_uid'] for user in matched_users_response['result']]
            print(matched_users)
            print("Matches after Sexuality Filter: ", len(matched_users))

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
        # print(f"Current User Preferences:\n"
        # f"- Min Age Preference: {current_user_min_age_preference} (type: {type(current_user_min_age_preference).__name__})\n"
        # f"- Max Age Preference: {current_user_max_age_preference} (type: {type(current_user_max_age_preference).__name__})\n"
        # f"- Min Height Preference: {current_user_min_height_preference} (type: {type(current_user_min_height_preference).__name__})\n"
        # f"- Max Distance Preference: {current_user_max_distance_preference} (type: {type(current_user_max_distance_preference).__name__})\n"
        # f"- Latitude: {current_user_latitude} (type: {type(current_user_latitude).__name__})\n"
        # f"- Longitude: {current_user_longitude} (type: {type(current_user_longitude).__name__})")


        result = []

        for match in matches:
            print(match['user_uid'])
            
            # Check if user has entered long & lat:
            if match['user_latitude'] not in (None, "") and match['user_longitude'] not in (None, ""):
                print("1")
                distance = calculate_distance(current_user_latitude, current_user_longitude, match['user_latitude'], match['user_longitude'])
                print(distance)
                match['distance'] = distance

            else:
                print("2")
                match['distance'] = 50000

            # print(match['user_uid'], match['user_age'], match['user_height'], match['distance'])
            # print(f"User UID: {match['user_uid']} (type: {type(match['user_uid']).__name__}), "
            # f"Age: {match['user_age']} (type: {type(match['user_age']).__name__}), "
            # f"Height: {match['user_height']} (type: {type(match['user_height']).__name__}), "
            # f"Distance: {match['distance']} (type: {type(match['distance']).__name__})")

            # check if user has entered height and age:
            # if match['user_age'] not in (None, 0, "") and match['user_height'] not in (None, 0, ""):


            print("3")
            if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference and
                int(match['user_height']) >= int(current_user_min_height_preference) and
                distance <= current_user_max_distance_preference
                ):
                print("4")
                result.append(match)
                # print("Cum Matches: ", len(result))

            # if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference): 
            #     print(match['user_uid'], match['user_age'], match['user_height'], match['distance'])
            #     result.append(match)
            #     print("Cum Matches: ", len(result))
            # else:
            #     print("This user did not match")
                # print("Cum Matches: ", len(result))
                # print(result)
            
            # print(result)
            # print([user['user_uid'] for user in result])
        print([user['user_uid'] for user in result])
        print(len(result))
        # return result
        # print(len(result)) 
        return result

    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches age height distance"
        })


def get_matches_extended_preferences(current_user_data, matches):
    """
    Extended matching function that includes lifestyle and preference matching
    """
    print("\n\n\t in extended preferences \n")
    # print(current_user_data, matches)
    try:
        result = []
        print(len(matches))
        for match in matches:
            # Initialize match flag
            is_match = True
            
            # Body Type Check (user_body_composition)
            if (current_user_data.get('user_body_composition') and 
                match.get('user_body_composition') and 
                current_user_data['user_body_composition'] != 'Any'):
                if match['user_body_composition'] not in ["Slim", "Athletic", "Curvy", "Plus Sized", "Few Extra Pounds"]:
                    is_match = False
                    
            # Smoking Preference Check
            if (current_user_data.get('user_smoking') and 
                match.get('user_smoking') and 
                current_user_data['user_smoking'] != 'Either'):
                if current_user_data['user_smoking'] != match['user_smoking']:
                    is_match = False
                    
            # Drinking Preference Check
            if (current_user_data.get('user_drinking') and 
                match.get('user_drinking') and 
                current_user_data['user_drinking'] != 'Either'):
                if current_user_data['user_drinking'] != match['user_drinking']:
                    is_match = False
                    
            # Religion Preference Check
            if (current_user_data.get('user_religion') and 
                match.get('user_religion') and 
                current_user_data['user_religion'] != 'Any'):
                if current_user_data['user_religion'] != match['user_religion']:
                    is_match = False
                    
            # Kids Preference Check
            if (current_user_data.get('user_prefer_kids') and 
                match.get('user_kids')):
                if not check_kids_preference(current_user_data['user_prefer_kids'], match['user_kids']):
                    is_match = False
            
            if is_match:
                result.append(match)

        # print(result)   
        print([user['user_uid'] for user in result])   
        print(len(result))
        print("Matches after Extended Preferences: ", len(result))        
        return result
    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches extended preferences",
            "error": str(e)
        })

def check_kids_preference(prefer_kids, actual_kids):
    """
    Helper function to check if the number of kids matches preferences
    Returns True if it's a match, False otherwise
    """
    try:
        if prefer_kids == '0' and actual_kids != '0':
            return False
        if prefer_kids == '1-2' and int(actual_kids) > 2:
            return False
        if prefer_kids == '3+' and int(actual_kids) < 3:
            return False
        return True
    except ValueError:
        # If we can't parse the values, we'll return True to not exclude matches
        return True

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
        print("In Matches Get")
        try:
            with connect() as db:

                current_user = db.select('users', where={'user_uid': user_uid})
                    
                if not current_user['result']:
                    return make_response(jsonify({
                        "message": f"User id {user_uid} doesn't exists"
                    }), 400)
                
                current_user_data = current_user['result'][0]
                # print("Got the current user's information")
                # print(current_user_data)

                check, response = get_matches_sexuality_open_to(current_user_data, user_uid)

                if not check:
                    return jsonify({
                        "message": "No Matches found because of preferred gender or open to list"
                    })

                result = get_matches_age_height_distance(current_user_data, response['result'])
                # print(result)
                print("Matches after Height Filter: ", len(result))

                if not result:
                    final_response = {}
                    final_response['message'] = "No matches found"

                    age_min_suggestions = suggest_age_min(current_user_data, response['result'])
                    age_max_suggestions = suggest_age_max(current_user_data, response['result'])
                    height_suggestions = suggest_height(current_user_data, response['result'])
                    distance_suggestions = suggest_distance(current_user_data, response['result'])

                    if (age_min_suggestions):
                        final_response['Lower minimum age'] = age_min_suggestions
                    if (age_max_suggestions):
                        final_response['Raise maximum age'] = age_max_suggestions
                    if (height_suggestions):
                        final_response['Lower minimum height'] = height_suggestions
                    if (distance_suggestions):
                        final_response['Raise maximum distance'] = distance_suggestions

                    if len(final_response.keys()) == 1:
                        final_response['message'] = "No matches found"
                        final_response['Lower minimum age'] = "No matches found"
                        final_response['Raise maximum age'] = "No matches found"
                        final_response['Lower minimum height'] = "No matches found"
                        final_response['Raise maximum distance'] = "No matches found"

                    return final_response

                # Apply extended preference filtering
                result = get_matches_extended_preferences(current_user_data, result)

                # print("After matching result: ", result)

                if not result:
                    return jsonify({
                        "message": "No matches found after applying lifestyle preferences"
                    })

                # Matching 2 way
                final_result = []
                print("Current User Preferences: ",current_user_data['user_age'], current_user_data['user_height'], current_user_data['user_sexuality'])
                for user in result:
                    print(user['user_uid'])
                    print(user['user_prefer_age_min'], user['user_prefer_age_max'], user['user_prefer_height_min'], user['user_open_to'])
                    if (user['user_prefer_age_min'] <= current_user_data['user_age'] <= user['user_prefer_age_max'] and
                        current_user_data['user_height'] >= user['user_prefer_height_min'] and
                        current_user_data['user_sexuality'] in ast.literal_eval(user['user_open_to'])
                        ):
                        final_result.append(user)
                
                
                if not final_result:
                    return jsonify({
                        "message": "No matches found because of 2 way matching",
                        "result of 1 way match": result
                    })
                else:
                    final_result.sort(key= lambda x: x['distance'])
                    return jsonify({
                        "message": "Matches Found",
                        "result": final_result,
                    })
        except Exception as e:
            return jsonify({
                "code": 400,
                "message": "There was an error while running the matching algorithm",
                "error": str(e)
            })