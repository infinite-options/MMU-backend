import requests
import pytest
import json

BASE_URL = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"

# Userinfo
def test_get_userinfo():

    response = requests.get(BASE_URL + "/userinfo/100-000001")

    assert response.status_code == 200

def test_put_userinfo():

    payload = {
            "user_uid": "100-000006",
            "user_email_id": "mollysymonds@gmail.com",
            "user_first_name": "Molly",
            "user_last_name": "Symonds",
            "user_notification_preference": "True",
            "user_location_service": "True",
            "user_date_interests": "Coffee,Lunch,Dinner",
            "user_available_time": '[{"day": "Wednesday", "end_time": "06:00 PM", "start_time": "02:00 PM"}, {"day": "Sunday", "end_time": "04:00 PM", "start_time": "01:00 PM"}, {"day": "Saturday", "end_time": "10:00 PM", "start_time": "11:00 AM"}]'
            }

    response = requests.put(BASE_URL + "/userinfo", data=payload)

    assert response.status_code == 200

# Likes
def test_get_likes():

    response = requests.get(BASE_URL + "/likes/100-000001")

    assert response.status_code == 200

def test_post_likes():

    payload = {
        "liker_user_id": "100-000001",
        "liked_user_id": "100-000004"
    }

    response = requests.post(BASE_URL + "/likes", data=payload)

    assert response.status_code == 200

def test_get_meet():

    response = requests.get(BASE_URL + "/meet/100-000001")

    assert response.status_code == 200

def test_get_lists():

    response = requests.get(BASE_URL + "/lists?list_category=activities")

    assert response.status_code == 200

def test_get_messages():

    response = requests.get(BASE_URL + "/messages?sender_id=100-000001&receiver_id=100-000007")

    assert response.status_code == 200
