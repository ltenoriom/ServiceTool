"""
    Module to obtain Okta oauth token
"""

import json
import time
import requests


class OktaAuth:
    """ Module to obtain Okta oauth token """
    __instance = None
    ORG_DOMAIN = "login.windriver.com"
    SESSION_DATA = ""

    @staticmethod
    def get_instance():
        """ Static access method. """
        if OktaAuth.__instance is None:
            OktaAuth()

        return OktaAuth.__instance

    @staticmethod
    def get_session_data():
        """ Returns the session token """
        return OktaAuth.SESSION_DATA

    @staticmethod
    def login(username="", password="", verbose=False):
        """ Create the session using 2-factor-auth """
        try:
            if verbose:
                print("Okta: Starting session (push verification only)")
            response = requests.post(f"https://{OktaAuth.ORG_DOMAIN}/api/v1/authn", data=json.dumps(
                {"username": username, "password": password}), headers={"Content-Type": "application/json"})
            response_data = json.loads(response.content.decode())

            if verbose:
                print("Response", response_data)

            if "_embedded" in response_data:
                if verbose:
                    print("Okta: Requesting confirmation...")

                # Only push verification is available with this method
                if response_data["status"] == "MFA_REQUIRED":
                    auth_method = response_data["_embedded"]["factors"][0]["id"]
                    state_token = response_data["stateToken"]
                    cookies = response.headers["set-cookie"]
                    push_tries = 0
                    last_response_data = {}

                    # Wait until the verification is performed
                    while push_tries < 10:
                        push_tries += 1

                        if verbose:
                            print("\n> Accessing:",
                                  f'https://{OktaAuth.ORG_DOMAIN}/api/v1/authn/factors/{auth_method}/verify')

                        response = requests.post(f'https://{OktaAuth.ORG_DOMAIN}/api/v1/authn/factors/{auth_method}/verify', data=json.dumps(
                            {"stateToken": state_token}), headers={"Content-Type": "application/json"})

                        last_response_data = json.loads(
                            response.content.decode())

                        if last_response_data["status"] == "SUCCESS":
                            if verbose:
                                print("Okta: Verification completed")
                            # Finalize by requesting the session data
                            response = requests.get(f"https://{OktaAuth.ORG_DOMAIN}/login/sessionCookieRedirect?checkAccountSetupComplete=true&token={last_response_data['sessionToken']}&redirectUrl=https%3A%2F%2F{OktaAuth.ORG_DOMAIN}",
                                                    allow_redirects=True,
                                                    headers={"cookie": f'{cookies}; sid={last_response_data["sessionToken"]}; oktaStateToken={state_token};'})
                            headers = response.headers["set-cookie"]
                            response = requests.get(f'{response.url}', allow_redirects=True, headers={
                                                    "cookie": f'{headers}'})

                            if verbose:
                                print("Okta: Session ready to be used")

                            # The session is ready to be used
                            OktaAuth.SESSION_DATA = response.headers["set-cookie"]
                            break

                        else:
                            time.sleep(5)

                elif response_data["status"] == "SUCCESS":
                    if verbose:
                        print("Okta: Verification completed")

                    cookies = response.headers["set-cookie"]
                    if verbose:
                        print("Cookies:", cookies)

                    # Finalize by requesting the session data
                    if verbose:
                        print(
                            "\n> Accessing:", f"https://{OktaAuth.ORG_DOMAIN}/login/sessionCookieRedirect?checkAccountSetupComplete=true&token={response_data['sessionToken']}&redirectUrl=https%3A%2F%2F{OktaAuth.ORG_DOMAIN}")

                    response = requests.get(f"https://{OktaAuth.ORG_DOMAIN}/login/sessionCookieRedirect?checkAccountSetupComplete=true&token={response_data['sessionToken']}&redirectUrl=https%3A%2F%2F{OktaAuth.ORG_DOMAIN}",
                                            allow_redirects=True,
                                            headers={"cookie": f'{cookies}; sid={response_data["sessionToken"]};'})
                    headers = response.headers["set-cookie"]
                    response = requests.get(f'{response.url}', allow_redirects=True, headers={
                                            "cookie": f'{headers}'})

                    if verbose:
                        print("Headers:", headers)

                    if verbose:
                        print("Okta: Session ready to be used")

                    # The session is ready to be used
                    OktaAuth.SESSION_DATA = response.headers["set-cookie"]

        except Exception as ex:
            if verbose:
                print("Error", ex)

        return OktaAuth.SESSION_DATA

    def __init__(self):
        """ Virtually private constructor. """
        if OktaAuth.__instance is not None:
            raise Exception("Only one instance is allowed")
        else:
            OktaAuth.__instance = self
