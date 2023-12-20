#
# This script is intended to pull a list of CVE cases from salesforce
# Before running this script please run create_sf_session.py and follow the link
# This will generate a file called CVE_SF.csv
#
# Usage: python3 -m Salesforce.fetch_cve_list
import pickle
import csv
from cve import fetch_csv

from cve import fetch_csv
from simple_salesforce import Salesforce

SESSION_FILE = "./salesforce_session"


def main():
    infile = open(SESSION_FILE, 'rb')
    response = pickle.load(infile)
    infile.close()
    sf = Salesforce(
        instance_url=response['instance_url'], session_id=response['access_token'])
    fetch_csv(sf, "./files/CVE_JIRA.csv")


if __name__ == '__main__':
    main()
