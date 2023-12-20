''' Module to interact with Jira
'''
import click
import enquiries
import json
import logging
import re
from numpy import fromfunction
from prettytable import PrettyTable
import requests
from requests.auth import HTTPBasicAuth
from requests_html import HTMLSession
import xlsxwriter
import os
import csv
import pandas as pd

from JIRA import credentials
from Misc import tools
from Salesforce import case

JIRA_URL = "http://jira.wrs.com:8080/rest/api/2/"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Not all versions are required to be listed with Cisco. If the tool is used for other products then
# just add them to the list like the below example
WRL_V_TRANSLATE = {"Linux 6 - Legacy": "LIN6",
                   "Linux 8 - Legacy": "LIN8",
                   "Linux LTS 18": "LIN1018"}


LINCCM_TRANSLATION = {"LIN6": "WRL 6.0",
                      "LIN8": "WRL 8.0",
                      "LIN1018": "WRL LTS18"}


def bulk_search(filename, project, config):
    bulk_results = []
    print('Searching for ' + project + ' in Jira')
    print('---------------------------------')
    filename_out = filename.replace('.txt', '.html')
    with open(filename_out, "w") as file:
        html = '<html><head><title>Bulk Search</title></head>'
        html += '<h1>Bulk Search Results </h1>'
    with open(filename) as f_in:
        '''convert the lines into a list of strings'''
        lines = list(line for line in (l.strip() for l in f_in) if line)

        '''traverse all the list of strings'''
        for line in lines:
            print('Searching for ' + line)
            html ='<h2>' + 'Results for :' +  line + '</h2>'
            with open(filename_out, "a") as file:
                file.write(html)
            
            print('---------------------------------')
            result = cve_check(line, project, config)
            df = pd.DataFrame.from_dict(result)
            reshtml1 = df.to_html( index=False, classes='stocktable', table_id='table1',escape=False)
            reshtml1 = reshtml1.replace('class="dataframe ','class="')  # It always adds a dataframe class so this removes it
            reshtml1 = coloring_html(reshtml1)
            with open(filename_out, "a") as file:
                file.write(reshtml1)

def check_if_exist_and_valid(key,object,value):
    print('Checking if ' + key + ' exists and is valid')
    if key in object and object[key] is not None:
        return value
    else:
        return "Not Found"

def cve_check(number, project, config,Verbose=True):
    url = JIRA_URL + "search"
    # Request
    data = {"jql": "text~" + number, "startAt": 0, "maxResults": 50,
            "fields": ["summary", "status", "description","customfield_12200", "customfield_11002","customfield_11000", "resolution", "labels"]}
    # Sending get request and saving the response as response object
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER,PASSWORD), params=data)
    if r.status_code == 200:
        data = r.json()
    else:
        print('The request was not successful. Status code: ' + str(r.status_code))
        return
 
    # Extracting data in json format
    status = ""
    resolution = ""
    updated = ""

    if 'issues' not in data:
        print('No issues found')
        return None
    
    values_return_list = []
    if data['issues']:
        for d in data['issues']:
            __dict__ = {}
            fields = d['fields']
            __dict__['status'] = d['fields']['status']['name']
            __dict__['description'] = d['fields']['status']['description']
            __dict__['summary'] = d['fields']['summary']
            __dict__['id'] = '<a href="https://jira.wrs.com/browse/{}">{}</a>'.format(d['key'],d['key']) 
            print('ID:', __dict__['id'])

            __dict__['foundver'] = check_if_exist_and_valid( 'customfield_11000',fields,fields["customfield_11000"][0]['name'])
            
            if 'customfield_11002' in fields and fields['customfield_12200']:
                __dict__['foundrel'] = fields['customfield_12200'][0]['name']
            else:
                __dict__['foundrel'] = 'Not Found'


            if 'resolution' in fields and fields['resolution'] is not None:
                __dict__['resolution'] = fields['resolution']['name']
            else:
                __dict__['resolution'] = 'Not Found'

            __dict__['labels'] = check_if_exist_and_valid( 'labels',fields,fields["labels"])
            
        
            values_return_list.append(__dict__)                
                
    return values_return_list

def cve(number, config):
    url = JIRA_URL + "search"
    # Request
    data = dict(jql="text~" + number, startAt=0, maxResults=20,
                fields=["summary", "status", "resolution", "labels", "customfield_11000", "customfield_11002"])
    # Sending get request and saving the response as response object
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    if r.status_code != 200:
        print("Authentication failed for JIRA")
        return []

    # Extracting data in json format
    data = r.json()
    status = ""
    resolution = ""
    data_dict = []
    # First we search if there are issues with that code
    for defect in data['issues']:
        print( 'https://jira.wrs.com/browse/' + defect['key'])
        fields = defect['fields']
        status = fields["status"]["name"]
        description = fields["status"]["description"]
        summary = fields["summary"]
        defect_id = defect["key"]

        if 'customfield_11000' in fields:
            if fields['customfield_11000'] is not None:
                foundin = str(fields['customfield_11000'][0]["name"])
            else:
                foundin = "Not Found"
        else:
            foundin = "Not Found"

        if 'customfield_11002' in fields:
            if fields['customfield_11002'] is not None:
                fixver = str(fields['customfield_11002']["name"])
            else:
                fixver = "Not Fixed"
        else:
            fixver = "Not Fixed"

        if fields["resolution"] is not None:
            resolution = fields["resolution"]["name"]
        else:
            resolution = "Unresolved"

        labels = ' , '.join(fields["labels"])

        ''' append data into a dictionary '''
        html_url = '<a href="https://jira.wrs.com/browse/{}">{}</a>'.format(defect_id,defect_id)
        dict01 = {'defect_id':html_url , 'summary': summary, 'description': description,'status': status, 'resolution': resolution, 'foundin': foundin,
                'fixver': fixver, 'labels': labels}
        data_dict.append(dict01)

    df = pd.DataFrame.from_dict(data_dict)
    html_d = df.to_html( index=False, classes='stocktable', table_id='table1',escape=False)
    html_d = html_d.replace('class="dataframe ','class="')  # It always adds a dataframe class so this removes it
    html_d = coloring_html(html_d)

    with open("table.html", "w") as file:
        file.write(html_d)

    print('Open the file table.html in your browser')

def coloring_html(html_buffer):
    '''color Resolved string on the html buffer'''
    html_buffer = html_buffer.replace('Resolved', '<font color="green">Resolved</font>')
    '''color Unresolved string on the html buffer'''
    html_buffer = html_buffer.replace('Unresolved', '<font color="red">Unresolved</font>')
    '''color Not Found string on the html buffer'''
    html_buffer = html_buffer.replace('Not Found', '<font color="red">Not Found</font>')
    '''color Rejected string on the html buffer'''
    html_buffer = html_buffer.replace('Rejected', '<font color="red">Rejected</font>')
    '''color closed string on the html buffer'''
    html_buffer = html_buffer.replace('Closed', '<font color="blue">closed</font>')
    return html_buffer

def cve_project(number, project, config):
    url = JIRA_URL + "search"
    # Request
    data = {"jql": "text~" + number + " and project = " + project, "startAt": 0, "maxResults": 20,
            "fields": ["priority", "summary", "status", "customfield_11002", "customfield_11000", "customfield_13702",
                       "resolution"]}
    # Sending get request and saving the response as response object
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)

    # Extracting data in json format
    data = r.json()
    result = []
    if data['issues']:
        print("--------------------")
        print("CVE: " + number)
        print("--------------------")
        for data in data['issues']:
            fields = data['fields']
            status = fields["status"]["name"]
            found_version = fields["customfield_11000"][0]["name"]
            if fields["customfield_11002"] is None:
                fixed_version = "NOT FIXED"
            else:
                if fields["customfield_11002"]["name"] is None:
                    fixed_version = "NOT FIXED"
                else:
                    fixed_version = fields["customfield_11002"]["name"]

            if fields["customfield_13702"] is None:
                nvd_version = "\nNot published on NVD/MITRE/SEARCH"
            else:
                nvd_version = "\nCVSS V3 URL:" + fields["customfield_13702"]
            summary = fields["summary"]
            defect_id = data["key"]
            if fields["resolution"] is None:
                resolution = "Unresolved"
                resolution_desc = "Unresolved"
            else:
                resolution = fields["resolution"]["name"]
                resolution_desc = fields["resolution"]["description"]
            print("- " + summary)
            print("Defect: " + defect_id)
            print("Status: " + status)
            print("Resolution: " + resolution)
            result = ("\nDefect: https://jira.wrs.com/browse/" + defect_id +
                      "\nStatus: " + status +
                      "\nResolution: " + resolution +
                      "\nFound Version: " + found_version +
                      "\nFixed Version: " + fixed_version +
                      "\nResolution Description: " + resolution_desc +
                      nvd_version)
    return result


def cve_list(number, config):
    result = []
    url = JIRA_URL + "search"
    # Request
    data = {"jql": "text~" + number, "startAt": 0, "maxResults": 20,
            "fields": ["summary", "status", "resolution", "project", "created"]}
    # Sending get request and saving the response as response object
    USER, PASSWORD = credentials.check(config)
    try:  # Refactor all this code in a single function
        r = requests.get(url=url, auth=HTTPBasicAuth(
            USER, PASSWORD), params=data)
    except:
        tools.print_failure(
            "Please, check that your internet and VPN are alive")
        return result
    if r.status_code != 200:
        tools.print_failure("CVE List could not establish the Jira connection.\
              Please check session")
        return result

    # Extracting data in json format
    data = r.json()
    status = ""
    resolution = ""
    updated = ""
    # First we search if there are issues with that code

    if data['issues']:
        for data in data['issues']:
            fields = data['fields']
            status = fields["status"]["name"]
            summary = fields["summary"]
            defect_id = data["key"]
            project = fields["project"]["key"]
            created = fields["created"]
            if fields["resolution"] is None:
                resolution = "Unresolved"
            else:
                resolution = fields["resolution"]["name"]
            result.append(
                {"cve": number, "defect": defect_id, "summary": summary, "status": status, "resolution": resolution,
                 "project": project, "created": created})
    # Sort tickets by creation
    result = sorted(result, key=lambda item: item.get('created'))
    return result


def associate(defect_id, case_id, config):
    url = JIRA_URL + "issue/" + defect_id
    # Request
    data = {"fields": ["customfield_12200"]}
    # Sending get request and saving the response as response object
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    # Extracting data in json format
    data = r.json()
    sf_link = data["fields"]["customfield_12200"]

    if sf_link:
        cases = sf_link.split(",")
        for case in cases:
            if case == case_id:
                return
        cases.append(case_id)
        value = ','.join([str(elem) for elem in cases])
    else:
        value = case_id
    headers = {"Accept": "application/json",
               "Content-Type": "application/json"}
    payload = json.dumps({"fields": {"customfield_12200": value}})
    USER, PASSWORD = credentials.check(config)
    requests.request("PUT", url=url, auth=HTTPBasicAuth(
        USER, PASSWORD), headers=headers, data=payload)


def jira_create_issue(sf_ins=None, data=None, case_id=None, config=None):
    logging.debug("Creating Issue in project " +
                  data['fields']['project']['key'])

    # Create issue
    url = JIRA_URL + "issue/"
    headers = {"Accept": "application/json",
               "Content-Type": "application/json"}
    payload = json.dumps(data)
    logging.debug(payload)
    USER, PASSWORD = credentials.check(config)
    r = requests.request("POST", url=url, auth=HTTPBasicAuth(
        USER, PASSWORD), data=payload, headers=headers)
    data = r.json()
    print("https://jira.wrs.com/browse/" + data['key'])

    if case_id is None:  # Ask for a casi ID if empty
        case_id = click.prompt('Please enter a valid case number: ')
    case.associate(sf_ins, case_id, data['key'], config)
    case.sf_set_resolution(
        sf_ins, case_id, "CCM is handling this CVE on " + data['key'])
    return data


def clone(sf_ins, defect_id, project, case_id=None, account="cisco", wrl_target_v=None, config=None):
    logging.debug("Cloning " + defect_id + " into " + project)
    print(defect_id)
    print(project)
    # Get issue info
    url = JIRA_URL + "issue/" + defect_id
    data = {}

    USER, PASSWORD = credentials.check(config)
    try:  # Refactor all this code in a single function
        r = requests.get(url=url, auth=HTTPBasicAuth(
            USER, PASSWORD), params=data)
    except:
        tools.print_failure(
            "Please, check that your internet and VPN are alive")
    if r.status_code != 200:
        tools.print_failure("CVE List could not establish the Jira connection.\
              Please check session")

    data = r.json()

    # Prepare new data
    if wrl_target_v is None:
        desired_prj = enquiries.choose(
            'Choose the project you want to clone for... ', LINCCM_TRANSLATION)
    else:
        desired_prj = WRL_V_TRANSLATE[wrl_target_v]

    if desired_prj == "LIN6":
        labels = ["CISCO", "PREMIUM",
                  "CIS-USA-SBG-WRL6"] if account == "cisco" else []
        found_in = LINCCM_TRANSLATION[desired_prj]
    elif desired_prj == "LIN8":
        labels = ["CISCO", "PREMIUM",
                  "CIS-USA-SBG-WRL8"] if account == "cisco" else []
        found_in = LINCCM_TRANSLATION[desired_prj]
    elif desired_prj == "LIN1018":
        labels = ["CISCO", "PREMIUM",
                  "CIS-USA-SBG-LTS18"] if account == "cisco" else []
        found_in = LINCCM_TRANSLATION[desired_prj]
    else:
        labels = ["CISCO", "PREMIUM"] if account == "cisco" else []
        linux_project = re.findall('(LIN\d+)', defect_id)[0]
        found_in = LINCCM_TRANSLATION[linux_project]

    new_data = {
        "update": {},
        "fields": {
            "project": {
                "key": "LINCCM",
            },
            "issuetype": {
                "name": "Bug"
            },
            "labels": labels
        }
    }
    new_data['fields']['summary'] = data['fields']['summary']
    new_data['fields']['description'] = data['fields']['description']
    new_data['fields']['customfield_11000'] = [{"name": found_in}]
    new_data['fields']['components'] = [{"name": "General"}]
    new_data['fields']['priority'] = {"id": data['fields']['priority']['id']}
    # Severity
    new_data['fields']['customfield_10605'] = {
        "value": data['fields']['customfield_10605']['value']}
    # Where found
    # new_data['fields']['customfield_13304'] = { "value" : data['fields']['customfield_13304']['value']}
    # TODO: Fix hardcoded value when None
    new_data['fields']['customfield_13304'] = {"value": "Review"}

    res = jira_create_issue(sf_ins=sf_ins, data=new_data,
                            case_id=case_id, config=config)

    logging.debug(res)
    return res['key']


def jira_inspect_keys(defect_list, config):
    url = JIRA_URL + "search"
    # Request
    if type(defect_list) is list:
        # print("your object is a list")
        STRING = "key = " + defect_list[0]
        for key in defect_list[1:]:
            STRING += " or key = " + key
    else:
        # print("your object is not a list")
        STRING = "key = " + defect_list

    data = {"jql": STRING, "startAt": 0, "maxResults": len(defect_list),
            "fields": ["summary", "status", "resolution", "project", "customfield_12200", "labels"]}

    # Sending get request and saving the response as response object
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    # Extracting data in json format
    data = r.json()
    # First we search if there are issues with that code
    result = []
    if (data['issues'] != []):
        result = []
        for data in data['issues']:
            fields = data['fields']
            status = fields["status"]["name"]
            summary = fields["summary"]
            labels = fields["labels"]
            labels = " ".join(labels)
            res = summary.find('CVE')
            cve_number = summary[res:].split(' ')[0]
            defect_id = data["key"]
            project = fields["project"]["key"]
            if fields["resolution"] is None:
                resolution = "Unresolved"
            else:
                resolution = fields["resolution"]["name"]
            result.append(
                {"cve": cve_number, "defect": defect_id, "summary": summary, "status": status, "resolution": resolution,
                 "project": project, "labels": labels})
    return result


def get_jira_commit(defect_id, verbose, config):
    # Get issue info
    url = JIRA_URL + "issue/" + defect_id
    data = {}
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    data = r.json()
    fields = data['fields']
    commit_id = jira_search_commit(
        fields['comment']['comments'], verbose, config)
    return fields['customfield_12200'], commit_id


def print_field(object, info, inner):
    if object[info]:
        if inner is None:
            print(info, ':', object[info])
        else:
            print(info, ':', object[info][inner])
    else:
        print(info, ':', "not found")


def print_custom_field(object, info, inner, name):
    if object[info]:
        if inner is None:
            print(name, ':', object[info])
        else:
            print(name, ':', object[info][inner])
    else:
        print(name, ':', "not found")


def inspect(defect_id, config):
    # Get issue info
    url = JIRA_URL + "issue/" + defect_id
    data = {}
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    data = r.json()
    fields = data['fields']
    print("Defect : https://jira.wrs.com/browse/" + defect_id)
    print_field(fields, "status", "description")
    print_field(fields, "status", "name")
    print_field(fields, "created", None)
    print_field(fields, "updated", None)
    print_field(fields, "summary", None)
    print_field(fields, "labels", None)
    print_custom_field(fields, "customfield_12200", None, "Salesforce Id")
    print_custom_field(fields, "customfield_13704", None, "CVE Id")
    print_field(fields, "reporter", "displayName")
    print_field(fields, "resolution", "description")
    print_field(fields, "resolutiondate", None)

    f = open("reports/"+defect_id+".json", "w")
    f.write(json.dumps(fields, indent=4, sort_keys=True))
    f.close()
    print('You can also check content of file: '+"reports/"+defect_id+".json")

    return fields


def jira_search_commit(field, verbose, config):
    commit_id = 'not_found'
    commit_url = None
    for comment in field:
        if comment['author']['name'] == 'jira-git':
            data = comment['body'].split('Commit: ', 1)[1].strip('[]')
            commit_id, commit_url = data.split('|', 1)

    if verbose and commit_url != None:
        session = HTMLSession()
        response = session.get(commit_url)
        subject = response.html.find('.commit-subject')[0].text
        message = response.html.find('.commit-msg')[0].text
        diffstat = response.html.find('.diffstat')[0].text
        tools.print_ok('Commit info:')
        print('URL: ' + commit_url)
        print(subject)
        print(message)
        print(diffstat)

    return commit_id


def comment(defect_id, text, config):
    logging.debug("Commenting in defect" + defect_id)
    data = {"body": text}
    # Create issue
    url = JIRA_URL + "issue/" + defect_id + "/comment"
    headers = {"Accept": "application/json",
               "Content-Type": "application/json"}
    payload = json.dumps(data)
    logging.debug(payload)
    USER, PASSWORD = credentials.check(config)
    r = requests.request("POST", url=url, auth=HTTPBasicAuth(
        USER, PASSWORD), data=payload, headers=headers)
    data = r.json()
    return data


def jira_get_status(defect_id, config):
    url = JIRA_URL + "issue/" + defect_id
    data = {}
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    data = r.json()
    fields = data['fields']
    return fields["status"]["name"]


def jira_get_last_mod_date(defect_id, config):
    # Get issue info
    # print(defect_id)
    url = JIRA_URL + "issue/" + defect_id
    data = {}
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    if r.status_code == 200:
        data = r.json()
        fields = data['fields']
        return fields['updated'].split('T')[0]
    else:
        print("Error code: ", r.status_code)
        exit()


def jira_get_created_date(defect_id, config):
    # Get issue info
    # print(defect_id)
    url = JIRA_URL + "issue/" + defect_id
    data = {}
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    data = r.json()
    fields = data['fields']
    return fields['created'].split('T')[0]


def jira_get_defect_status(defect_id, config):
    # Get issue info
    # print(defect_id)
    url = JIRA_URL + "issue/" + defect_id
    data = {}
    USER, PASSWORD = credentials.check(config)
    r = requests.get(url=url, auth=HTTPBasicAuth(USER, PASSWORD), params=data)
    data = r.json()
    fields = data['fields']
    return fields['Status']
