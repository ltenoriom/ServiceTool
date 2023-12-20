import getpass
import json
import os


def check(config):
    if os.path.exists(config.jira_creedentials_file):
        with open(config.jira_creedentials_file) as f:
            data = json.load(f)
            USER = "".join(data['user'])
            PASSWORD = "".join(data['passwd'])
        return USER, PASSWORD
    else:
        try:
            user = input("Username:")
            passwd = getpass.getpass("Password for " + user + ":")
        except Exception as error:
            print('ERROR', error)
        else:
            print("Got user:" + str(user) + " and pass: ***")
            data_set = {"user": [user], "passwd": [passwd]}
            json_dump = json.dumps(data_set)
            json_object = json.loads(json_dump)
            with open(config.jira_creedentials_file, 'w') as json_file:
                json.dump(json_object, json_file)
            return 0, 0
