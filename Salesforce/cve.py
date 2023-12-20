#
# This script is intended to pull a list of CVE cases from salesforce
# Before running this script please run create_sf_session.py and follow the link
# This will generate a file called CVE_SF.csv
#

import csv
import logging
import os


# This functions obtains the list using a request
def fetch(sf):
    # This is the query
    cve_list_query = "SELECT Account_Name__c, CaseNumber, OwnerId, JIRA_ID__c, Subject FROM Case WHERE " \
                     "Account_Name__c LIKE '%cisco%' AND Status != 'closed' AND Subject LIKE '% CVE-%' "
    cve_list = sf.query_all(cve_list_query)

    ## fieldnames = ['Account','Owner','Case Number', 'JIRA ID','Subject']
    for cve in cve_list['records']:

        # for every CVE case obtained from Salesforce
        if cve['JIRA_ID__c'] is not None:
            # Check if the Defect is None(in case the case is a new case)
            continue
        # If it is not a new case it will obtain the individual defects that are assigned to the case
        jira_defects = cve['JIRA_ID__c'].split()
        # For every defect in this list of defects
        for defect in jira_defects:
            # Obtain the one with CCM in the name, this is because probaly the CCM is the last step of the process.
            if "CCM" in defect or len(jira_defects) <= 1:
                print("-----------------CVE------------------")
                print(cve)


# This functions obtaines the list using a request
def fetch_csv(sf, filename):
    # This is the query
    cve_list_query = "SELECT Account_Name__c, CaseNumber, OwnerId, JIRA_ID__c, Subject FROM Case WHERE " \
                     "Account_Name__c LIKE '%cisco%' AND Status != 'closed' AND Subject LIKE '% CVE-%' "
    cve_list = sf.query_all(cve_list_query)

    # Create directory
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # I open the file where I will be saving the information obtained from Salesforce
    with open(filename, 'w', newline='') as file:
        fieldnames = ['Account', 'Owner', 'Case Number', 'JIRA ID', 'Subject']
        logging.debug("Saving CSV to: " + filename)
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for cve in cve_list['records']:

            # for every CVE case obtained from Salesforce
            if cve['JIRA_ID__c'] is not None:
                # Check if the Defect is None(in case the case is a new case)
                continue

            # If it is not a new case it will obtain the individual defects that are assigned to the case
            jira_defects = cve['JIRA_ID__c'].split()
            # For every defect in this list of defects
            for defect in jira_defects:
                # Obtain the one with CCM in the name, this is because probaly the CCM is the last step of the process.
                if "CCM" in defect or len(jira_defects) <= 1:
                    # Finally write to file.
                    writer.writerow(
                        {"Account": cve['Account_Name__c'], 'Owner': cve['OwnerId'], 'Case Number': cve['CaseNumber'],
                         'JIRA ID': defect, 'Subject': cve['Subject']})
