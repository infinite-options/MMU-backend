from flask import request, abort, make_response, jsonify
from flask_restful import Resource
import json

from data import connect
import ast
import math

def get_matches_sexuality_open_to(current_user_data, user_uid):
    print(" \n\t In Sexuality Open To Function \n")
    try:
        # current_user_prefer_gender = current_user_data['user_prefer_gender']
        # print("Gender Preferences: ",  current_user_prefer_gender)

        # current_user_open_to = ast.literal_eval(current_user_data['user_open_to'])
        # current_user_open_to = current_user_data['user_open_to']

        # Convert 'user_open_to' from string to list
        user_open_to_list = ast.literal_eval(current_user_data['user_open_to'])
        print(user_open_to_list)

        # Format the list into SQL-compatible string
        current_user_open_to = ', '.join(f'"{x}"' for x in user_open_to_list)
        current_user_open_to = f"({current_user_open_to})"
        print("Open To Preferences: ",  current_user_open_to)

        # current_user_open_to = ', '.join(f"'{item}'" for item in current_user_open_to)
        # if not current_user_prefer_gender or current_user_prefer_gender is None or current_user_prefer_gender == "Either":
        #     current_user_prefer_gender = "'Male','Female'"
        # else:
        #     current_user_prefer_gender = f"'{current_user_prefer_gender}'"

        # print(current_user_prefer_gender)
        
        with connect() as db:
            # query = f'''SELECT *
            #         FROM mmu.users
            #         WHERE user_uid != "{user_uid}"
            #         AND user_gender IN ({current_user_prefer_gender})
            #         -- AND user_sexuality IN ({current_user_open_to})
            #         '''
            query = f'''
                    SELECT u.*
                        -- , if(l1.liked_user_id = "100-000307", 'YES', 'NO') AS "Likes"
                        -- , if(l2.liker_user_id = "100-000307", 'YES', 'NO') AS "Liked by"
                        , if(l1.liked_user_id = "{user_uid}", 'YES', 'NO') AS "Likes"
                        , if(l2.liker_user_id = "{user_uid}", 'YES', 'NO') AS "Liked by"
                    FROM mmu.users u
                    LEFT JOIN 
                        -- mmu.likes l1 ON u.user_uid = l1.liker_user_id AND l1.liked_user_id = "100-000307"
                        mmu.likes l1 ON u.user_uid = l1.liker_user_id AND l1.liked_user_id = "{user_uid}"
                    LEFT JOIN 
                        -- mmu.likes l2 ON u.user_uid = l2.liked_user_id AND l2.liker_user_id = "100-000307"
                        mmu.likes l2 ON u.user_uid = l2.liked_user_id AND l2.liker_user_id = "{user_uid}"
                    -- WHERE user_uid != "100-000307"
                    WHERE user_uid != "{user_uid}"
                    -- AND user_identity_plural IN ("Women")
                    AND user_identity_plural IN {current_user_open_to}
                    '''
            # print(query)
            matched_users_response = db.execute(query, cmd='get')
            # print(matched_users_response)
            matched_users = [user['user_uid'] for user in matched_users_response['result']]
            # print(matched_users)
            print("Matches after Sexuality Filter: ", len(matched_users))

            if len(matched_users_response['result']) == 0:
                return (False, matched_users_response)
            
            return (True, matched_users_response['result'])
        
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

def get_matches_distance(current_user_data, matches):
    print("\n\n\t in distance \n")
    try:
        current_user_max_distance_preference = current_user_data['user_prefer_distance']
        current_user_latitude = current_user_data['user_latitude']
        current_user_longitude = current_user_data['user_longitude']
        print(f"Current User Preferences:\n"
        f"- Max Distance Preference: {current_user_max_distance_preference} (type: {type(current_user_max_distance_preference).__name__})\n"
        f"- Latitude: {current_user_latitude} (type: {type(current_user_latitude).__name__})\n"
        f"- Longitude: {current_user_longitude} (type: {type(current_user_longitude).__name__})")


        result = []

        for match in matches:
            # print(match['user_uid'])
            
            # if current_user_latitude not in (None, "") and current_user_longitude not in (None, ""):
                # Check if user has entered long & lat:
            if match['user_latitude'] not in (None, "") and match['user_longitude'] not in (None, ""):
                # print("1")
                distance = calculate_distance(current_user_latitude, current_user_longitude, match['user_latitude'], match['user_longitude'])
                # print(match['user_uid'], distance)

            else:
                # Assume user is too far away
                # print("2")
                distance = 50000

            # print(distance)

            if distance <= current_user_max_distance_preference:
                # print("Matched", match['user_uid'], distance)
                result.append(match)

            else:
                # print(" ---------------->>>>>>>   No Match!")
                continue

        # print([user['user_uid'] for user in result])
        print(len(result))
        # return result
        # print(len(result)) 
        return result

    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches distance"
        })

def get_matches_height(current_user_data, matches):
    # print("\n\n\t in height \n")
    try:
        current_user_min_height_preference = int(current_user_data['user_prefer_height_min'])

        print(f"Current User Preferences:\n"
        f"- Min Height Preference: {current_user_min_height_preference} (type: {type(current_user_min_height_preference).__name__})\n")

        result = []

        for match in matches:
            # print(match['user_uid'])
            
            # Check if user has entered height:
            if match['user_height'] and int(match['user_height']) >= int(current_user_min_height_preference):
                # print("Height Matched ", match['user_height'], int(current_user_min_height_preference))
                result.append(match)
            else:
                # print(" ---------------->>>>>>>   No Match!")
                continue

        # print([user['user_uid'] for user in result])
        print(len(result))
        # return result
        # print(len(result)) 
        return result

    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches height"
        })

def get_matches_age(current_user_data, matches):
    print("\n\n\t in age \n")
    try:
        current_user_min_age_preference = current_user_data['user_prefer_age_min']
        current_user_max_age_preference = current_user_data['user_prefer_age_max']

        print(f"Current User Preferences:\n"
        f"- Min Age Preference: {current_user_min_age_preference} (type: {type(current_user_min_age_preference).__name__})\n"
        f"- Max Age Preference: {current_user_max_age_preference} (type: {type(current_user_max_age_preference).__name__})\n")

        result = []

        for match in matches:
            # print(match['user_uid'])
            
            # Check if user has entered height:
            if current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference:
                # print("Age Matched ", match['user_age'], int(current_user_min_age_preference), int(current_user_max_age_preference))
                result.append(match)
            else:
                # print(" ---------------->>>>>>>   No Match!")
                continue

        # print([user['user_uid'] for user in result])
        print(len(result))
        # return result
        # print(len(result)) 
        return result

    except Exception as e:
        return jsonify({
            "message": "Error in Get Matches height"
        })



# def get_matches_age_height_distance(current_user_data, matches):
#     print("\n\n\t in age height \n")
#     try:
#         current_user_min_age_preference = current_user_data['user_prefer_age_min']
#         current_user_max_age_preference = current_user_data['user_prefer_age_max']
#         current_user_min_height_preference = int(current_user_data['user_prefer_height_min'])
#         current_user_max_distance_preference = current_user_data['user_prefer_distance']
#         current_user_latitude = current_user_data['user_latitude']
#         current_user_longitude = current_user_data['user_longitude']
#         print(f"Current User Preferences:\n"
#         f"- Min Age Preference: {current_user_min_age_preference} (type: {type(current_user_min_age_preference).__name__})\n"
#         f"- Max Age Preference: {current_user_max_age_preference} (type: {type(current_user_max_age_preference).__name__})\n"
#         f"- Min Height Preference: {current_user_min_height_preference} (type: {type(current_user_min_height_preference).__name__})\n"
#         f"- Max Distance Preference: {current_user_max_distance_preference} (type: {type(current_user_max_distance_preference).__name__})\n"
#         f"- Latitude: {current_user_latitude} (type: {type(current_user_latitude).__name__})\n"
#         f"- Longitude: {current_user_longitude} (type: {type(current_user_longitude).__name__})")


#         result = []

#         for match in matches:
#             print(match['user_uid'])
            
#             if current_user_latitude not in (None, "") and current_user_longitude not in (None, ""):
#                 # Check if user has entered long & lat:
#                 if match['user_latitude'] not in (None, "") and match['user_longitude'] not in (None, ""):
#                     print("1")
#                     distance = calculate_distance(current_user_latitude, current_user_longitude, match['user_latitude'], match['user_longitude'])
#                     print(distance)
#                     match['distance'] = distance

#                 else:
#                     print("2")
#                     match['distance'] = 50000
#             else:
#                 distance = 0

#             # print(match['user_uid'], match['user_age'], match['user_height'], match['distance'])
#             # print(f"User UID: {match['user_uid']} (type: {type(match['user_uid']).__name__}), "
#             # f"Age: {match['user_age']} (type: {type(match['user_age']).__name__}), "
#             # f"Height: {match['user_height']} (type: {type(match['user_height']).__name__}), "
#             # f"Distance: {match['distance']} (type: {type(match['distance']).__name__})")

#             # check if user has entered height and age:
#             # if match['user_age'] not in (None, 0, "") and match['user_height'] not in (None, 0, ""):


#             print("3")
#             # print(match['user_age'], type(match['user_age']))
#             # if(current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference):
#             #     print("True 1")
#             # print(match['user_height'], type(match['user_height']))
#             # if(int(match['user_height']) >= int(current_user_min_height_preference)):
#             #     print("True 2")
#             # print(distance, type(distance))
#             # if(distance <= current_user_max_distance_preference):
#             #     print("True 3")
#             if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference and
#                 int(match['user_height']) >= int(current_user_min_height_preference) and
#                 distance <= current_user_max_distance_preference
#                 ):
#                 print("Matched")
#                 result.append(match)
#             else:
#                 print(" ---------------->>>>>>>   No Match!")
#                 continue
#                 # print("Cum Matches: ", len(result))

#             # if (current_user_min_age_preference <= match['user_age'] <= current_user_max_age_preference): 
#             #     print(match['user_uid'], match['user_age'], match['user_height'], match['distance'])
#             #     result.append(match)
#             #     print("Cum Matches: ", len(result))
#             # else:
#             #     print("This user did not match")
#                 # print("Cum Matches: ", len(result))
#                 # print(result)
            
#             # print(result)
#             # print([user['user_uid'] for user in result])
#         print([user['user_uid'] for user in result])
#         print(len(result))
#         # return result
#         # print(len(result)) 
#         return result

#     except Exception as e:
#         return jsonify({
#             "message": "Error in Get Matches age height distance"
#         })


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
            # print(match['user_uid'])
            # Initialize match flag
            is_match = True
            
            # Body Type Check (user_body_composition)
            if (current_user_data.get('user_body_composition') and 
                match.get('user_body_composition') and 
                current_user_data['user_body_composition'] != 'Any'):
                if match['user_body_composition'] not in ["Slim", "Athletic", "Curvy", "Plus Sized", "Few Extra Pounds"]:
                    is_match = False
                    # print("No Match Body Type")
                    
            # Smoking Preference Check
            if (current_user_data.get('user_smoking') and 
                match.get('user_smoking') and 
                current_user_data['user_smoking'] != 'Either'):
                if current_user_data['user_smoking'] != match['user_smoking']:
                    is_match = False
                    # print("No Match Smoking")
                    
            # Drinking Preference Check
            if (current_user_data.get('user_drinking') and 
                match.get('user_drinking') and 
                current_user_data['user_drinking'] != 'Either'):
                if current_user_data['user_drinking'] != match['user_drinking']:
                    is_match = False
                    # print("No Match Drinking")
                    
            # Religion Preference Check
            if (current_user_data.get('user_religion') and 
                match.get('user_religion') and 
                current_user_data['user_religion'] != 'Any'):
                if current_user_data['user_religion'] != match['user_religion']:
                    is_match = False
                    # print("No Match Religion")
                    
            # Kids Preference Check
            if (current_user_data.get('user_prefer_kids') and 
                match.get('user_kids')):
                if not check_kids_preference(current_user_data['user_prefer_kids'], match['user_kids']):
                    is_match = False
                    # print("No Match Kids")
            
            if is_match:
                # print("Is match")
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
                # print('Current User: ', current_user)
                    
                if not current_user['result']:
                    return make_response(jsonify({
                        "message": f"User id {user_uid} doesn't exists"
                    }), 400)
                
                current_user_data = current_user['result'][0]
                # print("Got the current user's information")
                print(user_uid)
                print(current_user_data)


                # Sexuality
                check, response = get_matches_sexuality_open_to(current_user_data, user_uid)

                if not check:
                    return jsonify({
                        "message": "No Matches found because of preferred gender or open to list"
                    })
                
                # print(check)
                print("Back in main function 1: ", len(response))
                # print(response)


                # Distance
                print("In Distance")
                if current_user_data['user_latitude'] not in (None, "") and current_user_data['user_longitude'] not in (None, ""):
                    response = get_matches_distance(current_user_data, response)

                    print("Back in main function 2: ", len(response))
                    # print(response)


                # Height
                print("In Height")
                if current_user_data['user_prefer_height_min'] not in (None, ""):
                    response = get_matches_height(current_user_data, response)

                    print("Back in main function 3: ", len(response))
                    # print(response)


                # Age
                print("In Age")
                if current_user_data['user_prefer_age_min'] not in (None, "") and current_user_data['user_prefer_age_max'] not in (None, ""):
                    response = get_matches_age(current_user_data, response)

                    print("Back in main function 4: ", len(response))
                    # print(response)


                if not response:
                    final_response = {}
                    final_response['message'] = "No matches found"

                    age_min_suggestions = suggest_age_min(current_user_data, response)
                    age_max_suggestions = suggest_age_max(current_user_data, response)
                    height_suggestions = suggest_height(current_user_data, response)
                    distance_suggestions = suggest_distance(current_user_data, response)

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

                # Apply extended preference filtering - Off for Live Version
                # response = get_matches_extended_preferences(current_user_data, response)

                # print("After matching result: ", result)

                if not response:
                    return jsonify({
                        "message": "No matches found after applying lifestyle preferences"
                    })

                # Matching 2 way
                final_result = []
                print("\n Reverse Match")
                print("Current User Data: ",current_user_data['user_age'], current_user_data['user_height'], current_user_data['user_identity_plural'])
                for user in response:
                    print(user['user_uid'])
                    print('User Preferences: ', user['user_prefer_age_min'], user['user_prefer_age_max'], user['user_prefer_height_min'], user['user_open_to'])

                    # Ensure current_user_data fields are not None, null, or empty
                    if not all([
                        user.get('user_prefer_age_min') is not None,
                        user.get('user_prefer_age_max') is not None,
                        user.get('user_prefer_height_min') is not None,
                        user.get('user_open_to')  # Ensures it's not None or empty
                    ]):
                        print(user['user_uid'], " ---------------->>>>>>>   Skipped")
                        continue  # Skip this user if any required field is missing            

                    if (user['user_prefer_age_min'] <= current_user_data['user_age'] <= user['user_prefer_age_max']
                        and current_user_data['user_height'] >= user['user_prefer_height_min']
                        and current_user_data['user_identity_plural'] in ast.literal_eval(user['user_open_to'])):
                        print("Append User")
                        final_result.append(user)
                        # print(final_result['user_uid'])
                        print("Go on to next user")
                    else:
                       print(user['user_uid'], " ---------------->>>>>>>   No Match") 
                
                print(len(final_result))
                # print(final_result)

                if not final_result:
                    print("No Matches")
                    return jsonify({
                        "message": "No matches found because of 2 way matching",
                        "result of 1 way match": response
                    })
                else:
                    print("Match Success")
                    # print(final_result)
                    # final_result.sort(key= lambda x: x['distance'])
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


    def put(self):
        print("In Matches Put")
        try:
            with connect() as db:
                payload = request.form.to_dict()
                print(payload)
                user_uid = payload.pop('user_uid')
                key = {'user_uid': user_uid}
                # print(key)

                email = db.select('users', key, cols='user_email_id')
                if email['result'][0]['user_email_id'] != payload['user_email_id']:
                    return make_response(jsonify({
                            'code': 400,
                            'name': 'Bad Request',
                            'description': "Email-id doesn't match with the email-id linked with provided user_uid"
                        }), 400)

                userQuery = db.update('users', key, payload)
                print(userQuery)

                updated_data = self.get(user_uid)

                return updated_data

        except Exception as e:
            return jsonify({
                "code": 400,
                "message": "There was an error while running the matching algorithm",
                "error": str(e)
            })