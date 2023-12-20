#
# This script is intended to pull a list of defects from the csv file generated from fetch_csv_list.py
# It will create a new file, and obtain the status, resolution and last update time.
# This will generate a file called CVE_JIRA.csv
#
import csv
import getpass
import logging
import os
import requests
from requests.auth import HTTPBasicAuth


# This functions grabs the CVE document that comes from the salesforce app
# and obtaines the Jira Defect column.
def parseCSV(fileName):
    cveList = []
    with open(fileName) as f:
        reader = csv.reader(f, delimiter=',')
        for i in reader:
            # Jira Defect column
            cveList.append(i[3])
    # This removes the column name
    cveList.pop(0)
    return cveList


def getRequest(user, password, url, jiradefect):
    # Request
    data = {'jql': 'issue='+str(jiradefect), 'startAt': 0, 'maxResults': 1,
            'fields': ['status', 'resolution', 'updated']}
    # Sending get request and saving the response as response object
    r = requests.get(url=url, auth=HTTPBasicAuth(user, password), params=data)
    if r.status_code != 200:
        print('Authentication failed for JIRA')
        return []

    # Extracting data in json format
    data = r.json()
    status = ''
    resolution = ''
    updated = ''
    # First we search if there are issues with that code
    if(data['issues'] != []):
        # We grab the fields
        data = data['issues'][0]['fields']
        status = data['status']['name']
        updated = data['updated']
        # In jira resolution is null if not modified and is interpreted as Unresolved
        if(data['resolution'] is None):
            resolution = 'Unresolved'
        else:
            resolution = data['resolution']['name']
    return [status, resolution, updated]


def main(filename):
    url = 'http://jira.wrs.com:8080/rest/api/2/search'
    username = input('Username: ')
    password = getpass.getpass(prompt='Password: ')
    files = './files/CVE_SF.csv'
    cve_list = parseCSV(files)
    jira_results_list = []

    # Create directory
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(filename, 'w', newline='') as file:
        logging.debug('Saving JIRA CSV to: ' + filename)
        fieldnames = ['Defect', 'Status', 'Resolution', 'Last Updated']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(0, len(cve_list)):
            # I am adding it to a list in case you want to do something with that list later on.
            jira_results_list.append(getRequest(
                username, password, url, cve_list[i]))
            writer.writerow({'Defect': cve_list[i], 'Status': jira_results_list[i][0],
                             'Resolution': jira_results_list[i][1], 'Last Updated': jira_results_list[i][2]})

    print(jira_results_list)


if __name__ == '__main__':
    main('../files/CVE_JIRA.csv')
