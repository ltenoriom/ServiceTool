create_sf_session.py:
    This script creates a salesforce session.

fetch_cvs_list.py
    This script pulls a list of CVEs from Salesforce.

fetch_jira_status.py
    This script pulls a list of the status, resolution and last modificatoin date from jira.

request_CVE_JIRA.py
    This script pulls a list of CVEs from JIRA based on a list of CVE names.


# Bugs & old notes:
- sf ls: Add JIRA Status
- sf ls: Detect inconsistency in resolution plan and JIRA Status
- sf jiras: clone after associate sustaning JIRA
Do you want to associate it to the case or clone the case to CCM? [y/c/N]:
- sf associate: Defect Filed after associate
- jira clone: sf associate after clone
- jira clone: Add SF summary to description

Bugs

- Case Owner is changed after modifying the case with 'cveTool sf resolution'
