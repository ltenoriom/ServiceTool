
import pickle
import re

from simple_salesforce import Salesforce
from Misc import tools


def get_session(file, config):
    infile = open(file, 'rb')
    response = pickle.load(infile)
    if 'error' in response:
        print('Error: ' + response['error'] + \
              '. Description: ' + response['error_description'])
        return None, None

    sf_src = 'login'
    if config.test_mode:  # URL changes if using sandbox
        sf_src = 'test'

    user = re.search(r'https://' + sf_src + '.salesforce.com/id/\w+/(\w+)',
                     response['id'])
    if user == None:
        tools.print_failure("Failed to get session.\n"
                            "1. Check if the session expired (re-run sf session). \n"
                            "2. Check usage of the test flag (-t). Use it only if the session "
                            "was created with this mode")
        return None, None

    userid = user.group(1)
    infile.close()
    sf_ins = Salesforce(
        instance_url=response['instance_url'], session_id=response['access_token'])
    return sf_ins, userid
