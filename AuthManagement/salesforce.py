"""
    Module to obtain Salesforce access
"""

import os
import re
import pickle
import requests
from bs4 import BeautifulSoup
from simple_salesforce import Salesforce
from .okta import OktaAuth

class SalesforceAuth:
    """
        Module to obtain Salesforce access
    """
    __instance = None
    __sf_instance = None
    __user_id = None
    __uat = False
    CLIENT_ID = "3MVG9zlTNB8o8BA2kI1ujIJp64pWE9Atbi1pvhFFtY6JybhpSjZsZrVgn6kYAC6NiAXclAVDp0N91F4JMkNJY"
    CLIENT_SECRET = "7818923507286520166"
    SESSION_DATA = ""
    ORG_NAME = "windriver"
    SALESFORCE_URL = "salesforce.com"
    TOKEN_REQUEST_URL = "/services/oauth2/token"  # mode.sales[...]
    CALLBACK_URL = "http://localhost:1197/salesforce/callback"
    SESSION_FILE = ".session_salesforce"

    @staticmethod
    def get_instance():
        """ Static access method. """
        if SalesforceAuth.__instance is None:
            SalesforceAuth()

        return SalesforceAuth.__instance

    @staticmethod
    def get_sf_instance():
        """ Returns the SF instance """
        return SalesforceAuth.__sf_instance

    @staticmethod
    def get_user_id():
        """ Returns te User ID of the session """
        return SalesforceAuth.__user_id

    @staticmethod
    def get_mode():
        """ Returns which mode the session is set """
        if SalesforceAuth.__uat:
            temp = "uat"
        else:
            temp = "production"

        return temp

    @staticmethod
    def test_session(verbose=False):
        """ Creates a request to verify the session has access """
        success = False
        try:
            print("Testing session...") if verbose else None
            survey_case_ids_query = "SELECT OwnerId FROM Case WHERE CreatedDate=LAST_WEEK AND Status != 'closed' LIMIT 1"
            SalesforceAuth.__sf_instance.query_all(survey_case_ids_query)
            success = True

        except Exception as ex:
            if verbose:
                print(ex)

        return success

    @staticmethod
    def login(okta=None, uat=False, verbose=False):
        """ Creates the new session using OKTA data or returns the session if is already created """
        SalesforceAuth.__uat = uat
        new_session = False
        success = False
        if uat:
            print("Error: UAT feature in development")
            return False
        try:
            if verbose:
                print("Trying to get the session from the file")
    
            session_file = open(
                f'{os.getcwd()}/{SalesforceAuth.SESSION_FILE}', "rb")
            response = pickle.load(session_file)
            session_file.close()

            if 'error' in response:
                print("Error has been found on the session file")
                new_session = True
            else:
                if SalesforceAuth.__uat:
                    sf_src = "test"
                else:
                    sf_src = "login"
                user = re.search(
                    f'https://{sf_src}.salesforce.com/id/\w+/(\w+)', response['id'])
                print(f"SalesforceAuth: user found: {user.group(1)}") if verbose else None
                if user is None:
                    new_session = True
                else:
                    SalesforceAuth.__user_id = user.group(1)
                    SalesforceAuth.__sf_instance = Salesforce(
                        instance_url=response['instance_url'], session_id=response['access_token'])
                    if SalesforceAuth.test_session():
                        success = True
                        print("SalesforceAuth: session is valid")
                    else:
                        print("SalesforceAuth: session is not valid")
                        new_session = True

        except Exception as ex:
            new_session = True
            if verbose:
                print(ex)

        print(new_session," --------  new_session") if verbose else None
        if new_session and not success and okta is not None:
            print("Salesforce: Creating a new session")
            cookie = okta.get_session_data()

            if cookie != "":
                if verbose:
                    print(
                        "\n> Accessing:", f"https://{SalesforceAuth.ORG_NAME}.my.{SalesforceAuth.SALESFORCE_URL}/services/oauth2/authorize?response_type=code&client_id={SalesforceAuth.CLIENT_ID}&redirect_uri={SalesforceAuth.CALLBACK_URL}")
                response = requests.get(f"https://{SalesforceAuth.ORG_NAME}.my.{SalesforceAuth.SALESFORCE_URL}/services/oauth2/authorize?response_type=code&client_id={SalesforceAuth.CLIENT_ID}&redirect_uri={SalesforceAuth.CALLBACK_URL}",
                                        allow_redirects=False)
                cookies1 = response.cookies
                browser_id = f'BrowserId={cookies1.get("BrowserId")}; BrowserId_sec={cookies1.get("BrowserId_sec")}'
                if verbose:
                    print("\n> Accessing:", response.headers["Location"])
                response = requests.get(response.headers["Location"],
                                        allow_redirects=False,
                                        headers={"cookie": browser_id})

                lineas_respuesta = response.content.decode().splitlines()

                for linea in lineas_respuesta:
                    if "var url" in linea:
                        redirect = linea.split(' ')[-1][1:-2]
                        if verbose:
                            print("\n> Accessing:",
                                  f"https://{SalesforceAuth.ORG_NAME}.my.{SalesforceAuth.SALESFORCE_URL}{redirect}")
                        break

                if redirect is not None:
                    response = requests.get(f"https://{SalesforceAuth.ORG_NAME}.my.{SalesforceAuth.SALESFORCE_URL}{redirect}",
                                            allow_redirects=False,
                                            headers={"cookie": browser_id})

                    if verbose:
                        print("\n> Accessing:", response.headers["Location"])
                    response = requests.get(response.headers["Location"],
                                            allow_redirects=False,
                                            headers={"cookie": cookie})

                    soup = BeautifulSoup(response.text, 'html.parser')
                    new_url = soup.find(id="appForm").get("action")
                    inputs = soup.find(id="appForm").find_all("input")
                    data = {}
                    for input_data in inputs:
                        data[input_data.get("name")] = input_data.get("value")

                    new_cookies = response.headers["set-cookie"]+';'+browser_id
                    if verbose:
                        print("\n> Accessing[POST]:", new_url)
                    response = requests.post(new_url,
                                             allow_redirects=False,
                                             headers={"cookie": new_cookies},
                                             data=data)

                    new_cookies = response.headers["set-cookie"]+';'+browser_id
                    oinfo = response.cookies.get("oinfo")
                    if verbose:
                        print("\n> Accessing:", response.headers["Location"])
                    response = requests.get(response.headers["Location"],
                                            allow_redirects=False,
                                            headers={"cookie": new_cookies})

                    sfdc_lv2 = response.cookies.get("sfdc_lv2")
                    disco = response.cookies.get("disco")
                    autocomplete = response.cookies.get("autocomplete")
                    sid = response.cookies.get("sid")
                    sid_client = response.cookies.get("sid_Client")
                    client_src = response.cookies.get("clientSrc")
                    oid = response.cookies.get("oid")

                    required_cookies = f'{browser_id}; oeinfo={oinfo}; sfdc_lv2={sfdc_lv2}; disco={disco}; autocomplete={autocomplete}; sid={sid}; sid_Client={sid_client}; clientSrc={client_src}; oid={oid}'

                    if verbose:
                        print(
                            "\n> Accessing:", f'https://{SalesforceAuth.ORG_NAME}.my.{SalesforceAuth.SALESFORCE_URL}/services/oauth2/authorize?response_type=code&client_id={SalesforceAuth.CLIENT_ID}&redirect_uri={SalesforceAuth.CALLBACK_URL}')
                    response = requests.get(f'https://{SalesforceAuth.ORG_NAME}.my.{SalesforceAuth.SALESFORCE_URL}/services/oauth2/authorize?response_type=code&client_id={SalesforceAuth.CLIENT_ID}&redirect_uri={SalesforceAuth.CALLBACK_URL}',
                                            allow_redirects=False,
                                            headers={"cookie": required_cookies})
                    if verbose:
                        print("\n> Accessing:", response.headers["Location"])
                    response = requests.get(response.headers["Location"],
                                            allow_redirects=False,
                                            headers={"cookie": required_cookies})

                    # Finally the code is ready
                    access_code = ""
                    lineas_respuesta = response.content.decode().splitlines()
                    for linea in lineas_respuesta:
                        if "window.location.href" in linea:
                            splitted = linea.split('\'')
                            if len(splitted) > 1:
                                definition = splitted[-2]
                                if len(definition.split('?')) > 0:
                                    code = definition.split('?')[-1]
                                    if len(code.split('=')) > 1:
                                        access_code = code.split(
                                            '=')[1][:-6]+"=="
                                        break

                    if access_code != "":
                        data = {
                            'grant_type': 'authorization_code',
                            'redirect_uri': SalesforceAuth.CALLBACK_URL,
                            'code': access_code,
                            'client_id': SalesforceAuth.CLIENT_ID,
                            'client_secret': SalesforceAuth.CLIENT_SECRET
                        }

                        headers = {
                            'content-type': 'application/x-www-form-urlencoded'
                        }
                        if SalesforceAuth.__uat:
                            token_url = f'https://test.{SalesforceAuth.SALESFORCE_URL}{SalesforceAuth.TOKEN_REQUEST_URL}'

                        else:
                            token_url = f'https://login.{SalesforceAuth.SALESFORCE_URL}{SalesforceAuth.TOKEN_REQUEST_URL}'

                        if verbose:
                            print("\n> Accessing:", token_url)
                        req = requests.post(
                            token_url, data=data, headers=headers)

                        print("Salesforce: Session created")
                        response = req.json()
                        outfile = open(
                            f'{os.getcwd()}/{SalesforceAuth.SESSION_FILE}', 'wb')
                        pickle.dump(response, outfile)
                        outfile.close()
                        if SalesforceAuth.__uat:
                            sf_src = "test"
                        else:
                            sf_src = "login"
                        user = re.search(r'https://' + sf_src +
                                         '.'+SalesforceAuth.SALESFORCE_URL+'/id/\w+/(\w+)', response['id'])
                        if user is not None:
                            SalesforceAuth.__user_id = user.group(1)
                            SalesforceAuth.__sf_instance = Salesforce(
                                instance_url=response['instance_url'], session_id=response['access_token'])
                            success = True
            else:
                print("Unable to create new session")
        return success

    def __init__(self):
        """ Virtually private constructor. """
        if SalesforceAuth.__instance is not None:
            raise Exception("Only one instance is allowed")
        else:
            SalesforceAuth.__instance = self
