""" Module to interact with reflektive """

import json
import requests
from bs4 import BeautifulSoup
from AuthManagement.okta import OktaAuth

REFLEKTIVE_URL = "https://www.reflektive.com"
WIND_REFLEKTIVE_URL = "http://reflektive.windriver.com"
THIRD_PARTY_TOKEN = "MvAyGxLAgdPeKEtJ7AV6"


def reflektive(verbose=False):
    """ Module to interact with reflektive """
    print("Reflektive: Creating a new session")
    okta = OktaAuth.get_instance()
    cookie = okta.get_session_data()
    if verbose:
        print("\n> Accessing:", WIND_REFLEKTIVE_URL)

    # First redirect to wind reflektive login
    response = requests.get(WIND_REFLEKTIVE_URL, allow_redirects=False)

    if verbose:
        print("\n> Accessing:", response.headers["location"])
    # Redirection to okta login
    response = requests.get(
        response.headers["location"], allow_redirects=False)

    cookies_inicial = response.headers["set-cookie"]

    if verbose:
        print("\n> Accessing:", response.headers["location"])
    # Redirects to SAML auth with okta credentials
    response = requests.get(
        response.headers["location"], allow_redirects=False, headers={"cookie": cookie+cookies_inicial})

    cookies = response.headers["set-cookie"]

    soup = BeautifulSoup(response.text, 'html.parser')
    new_url = soup.find(id="appForm").get("action")
    inputs = soup.find(id="appForm").find_all("input")
    data = {}
    for input_data in inputs:
        data[input_data.get("name")] = input_data.get("value")
    response = requests.post(new_url,
                             allow_redirects=True,
                             data=data, headers={"cookie": cookies+cookies_inicial})

    # Session ID temp
    cookies = f'_session_id={response.cookies.get("_session_id")};'

    if verbose:
        print("\n> Accessing:",
              f'{REFLEKTIVE_URL}/users/oauth?third_party_token={THIRD_PARTY_TOKEN}')
    response = requests.get(f'{REFLEKTIVE_URL}/users/oauth?third_party_token={THIRD_PARTY_TOKEN}',
                            allow_redirects=False, headers={"cookie": response.headers["set-cookie"]+cookies_inicial})

    print("Reflektive: Session succesfully created")
    session_id = f'_session_id={response.cookies.get("_session_id")};'

    # test query
    response = requests.get("https://www.reflektive.com/newsfeed/index/v2?offset=0&limit=25&page=0&type=all",
                            allow_redirects=False, headers={"cookie": session_id})
    print(json.dumps(json.loads(response.content.decode()), indent=4, sort_keys=True))

    '''
    content = {
        "audience": "everyone",
        "feedback_type": "positive",
        "hashtags": [
            "thewindway",
            "wecare",
            "cstool"
        ],
        "isSender": True,
        "likes": [],
        "points": 0,
        "recipients": [
            "b8d95a43-3330-4814-8714-0e8a2ef85d20"
        ],
        "source": "web:recognition_wall",
        "text": "I appreciate the encouragement you gave me to explore new challenges. I have been learning a lot from it, and I am thrilled to collaborate with the team.<p> #thewindway #wecare #cstool</p><br />",
        "type": "real_time_feedback"
    }
    '''

    # print(json.dumps(content))
    # response = requests.post("https://www.reflektive.com/constant_feedbacks",
    #                         allow_redirects=False, headers={"cookie": session_id, 'Content-type': 'application/json'}, data=json.dumps(content))

    #print(response, response.content)


'''
https://www.reflektive.com/users/extend_session

Get feed
https://www.reflektive.com/newsfeed/index/v2?offset=0&limit=25&page=0&type=all
_session_id=63476a360139722886af4f3c60933e12;
saml_client_type=web;

Give like
https://www.reflektive.com/likes/like [put]

Auth
https://www.reflektive.com/users/oauth?third_party_token=MvAyGxLAgdPeKEtJ7AV6

Search users
https://www.reflektive.com/search?query=Luis%20danie&page=1&resources[]=employees&participating_in=rtf


Send feedbak
https://www.reflektive.com/constant_feedbacks [post]
'Content-type': 'application/json'
{"audience":"everyone","feedback_type":"positive","hashtags":["thewindway","wecare"],"isSender":true,"likes":[],"points":0,"recipients":["eabb8e2d-7b9c-4ade-b04c-7e4146d50be1"],"source":"web:recognition_wall","text":"Thank you very much for taking the time and guided me through the Studio platform. It was beneficial, I learned a lot, and it was fascinating.<p> #thewindway #wecare</p><br />","type":"real_time_feedback"}
'''
