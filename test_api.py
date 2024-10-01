import requests
import pytest

BASE_URL = "https://41c664jpz1.execute-api.us-west-1.amazonaws.com/dev"

def test_get_userinfo():

    response = requests.get(BASE_URL + "/userinfo/100-000001")

    assert response.status_code == 200

def test_get_likes():

    response = requests.get(BASE_URL + "/likes/100-000001")

    assert response.status_code == 200

def test_get_meet():

    response = requests.get(BASE_URL + "/meet/100-000001")

    assert response.status_code == 200