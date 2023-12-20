#
# Starts the Salesforce session
# You dont need to edit anything here just run it and then you are abe to query using the Salesforce API
#
import flask
import os
import pickle
import requests
import socket
import webbrowser

from simple_salesforce import Salesforce

app = flask.Flask(__name__)

CONSUMER_KEY = '3MVG9zlTNB8o8BA2kI1ujIJp64pWE9Atbi1pvhFFtY6JybhpSjZsZrVgn6kYAC6NiAXclAVDp0N91F4JMkNJY'
CONSUMER_SECRET = 'vMZIM6SQ9TxhmSxTw6dUZUpiX'
REDIRECT_URI = 'http://localhost:1337/salesforce/callback'
AUTHORIZE_URL = '/services/oauth2/authorize?response_type=code&client_id=' + \
                CONSUMER_KEY + "&redirect_uri=" + REDIRECT_URI

SESSION_FILE = "salesforce_session"
only_one = False


@app.route('/')
def home():
    return flask.redirect(AUTHORIZE_URL, code=302)


@app.route('/salesforce/callback')
def callback():
    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': flask.request.args.get('code'),
        'client_id': CONSUMER_KEY,
        'client_secret': CONSUMER_SECRET
    }
    
    headers = {
        'content-type': 'application/x-www-form-urlencoded'
    }
    req = requests.post(REQUEST_TOKEN_URL, data=data, headers=headers)
    response = req.json()
    outfile = open(SESSION_FILE, 'wb')
    pickle.dump(response, outfile)
    outfile.close()
    global sf
    sf = Salesforce(
        instance_url=response['instance_url'], session_id=response['access_token'])
    return "Logged in! Session saved. \n <a href=\"query\">Run test query</a>"


@app.route('/salesforce/query')
def query():
    global sf
    if not 'sf' in globals():
        infile = open(SESSION_FILE, 'rb')
        response = pickle.load(infile)
        infile.close()
        sf = Salesforce(
            instance_url=response['instance_url'], session_id=response['access_token'])
    survey_case_ids_query = "SELECT Account_Name__c, CaseNumber, OwnerId, JIRA_ID__c FROM Case WHERE Account_Name__c " \
                            "LIKE '%cisco%' AND Status != 'closed' "
    survey_case_ids = sf.query_all(survey_case_ids_query)

    return survey_case_ids


def main(config):
    global AUTHORIZE_URL
    global REQUEST_TOKEN_URL
    AUTHORIZE_URL = "https://" + config.sf_url + AUTHORIZE_URL

    REQUEST_TOKEN_URL = config.request_token

    print(AUTHORIZE_URL)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    global only_one
    if only_one is False:
        only_one = True
        print('Browser will be open to review the test query')
        url = 'http://' + s.getsockname()[0] + ":1337"
        print("Click on this url :" + url)
        webbrowser.open(url, new=1)
    s.close()
    port = int(os.environ.get('PORT', 1337))
    app.run(host='0.0.0.0', port=port, debug=True)
