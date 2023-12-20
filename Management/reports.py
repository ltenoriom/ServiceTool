''' Module to interact as Manager
'''

import datetime
import enquiries

from JIRA import defects
from Misc import tools
from Salesforce import users

JIRA_URL = 'http://jira.wrs.com:8080/rest/api/2/'
URL_BASE = 'https://windriver.my.salesforce.com/'  # + CASE_ID
JIRA_ISSUE_URL = 'https://jira.wrs.com/browse/'  # + DEFECT_ID


def html_color_tags(tag):
    """ HTML Color Tags

    Attributes
    ----------
    tag(str): Switch tag value {Unresolved, Resolved, Default}

    Returns
    -------
    str: String without spaces
    """
    string = ""
    if tag == "Unresolved":
        string = "<a style=color:blue>%s</a>" % tag
    elif tag == "Resolved":
        string = "<a style=color:green>%s</a>" % tag
    else:
        string = "<a style=color:black>%s</a>" % tag

    return string


def sf_cve_closed_cases(sf_ins, manager_id, account, days):
    """ Close a case

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    manager_id(str): Manager ID
    account(str): Account name
    days(str): Days

    Returns
    -------
    list: List with results
    """
    delta_t = datetime.datetime.now() - datetime.timedelta(days=days)
    time_closed = str(delta_t).split()[0]+'T00:00:00.000Z'
    print(time_closed)
    _, b_dictionary = users.sf_user_get_employees(sf_ins, manager_id)
    fields_query = ["CaseNumber", "Status", "OwnerId",
                    "Product_Level_Three__c", "Subject", "Resolution_Plan__c",
                    "CreatedDate", "LastModifiedDate", "Id", "JIRA_ID__c"]
    query_data = "SELECT " + ','.join(fields_query) + " FROM Case WHERE " + \
        "Subject LIKE '%CVE-%' AND Account_Name__c LIKE '%" + account + \
        "%' AND ClosedDate > " + time_closed + \
        " ORDER BY Product_Level_Three__c  ASC NULLS FIRST"
    data = sf_ins.query_all_iter(query_data)
    results = []
    feils_q_copy = fields_query.copy()
    results.append(feils_q_copy)
    count = 0
    for row in data:
        count += 1
        items = []
        for header in feils_q_copy:
            if row[header]:
                if header == "OwnerId":
                    items.append(b_dictionary[row[header]])
                elif header == "Subject":
                    info = (row[header][:75] +
                            ' ... ') if len(row[header]) > 75 else row[header]
                    items.append(info)
                elif header == "CreatedDate":
                    items.append(row[header].split('T')[0])
                elif header == "LastModifiedDate":
                    items.append(row[header].split('T')[0])
                elif header == "Id":
                    item_id = '<a href='+URL_BASE + \
                        row[header]+'>'+row['CaseNumber']+'</a>'
                    items.append(item_id)
                elif header == "JIRA_ID__c":
                    defects1 = row[header].split()
                    ccm_defects = [
                        item for item in defects1 if item.startswith('LINCCM')]
                    string = ""
                    if ccm_defects:  # extract only ccm defects is they exist
                        for defcts in ccm_defects:
                            string += str(tools.add_html_tags2defect(defcts) + "<br>")
                    else:
                        for defcts in defects1:
                            string += str(tools.add_html_tags2defect(defcts) + "<br>")
                    items.append(string)
                else:
                    items.append(row[header])
        results.append(items)

    tools.dict2html(results, 'reports/sf_cve_closed.html',
                    "Salesforce CVE Results")
    print(str(count) + " case has been extracted and closed since "+str(days)+" ago")
    return results


def sf_cve_update(sf_ins, case_type, manager_id, account, config):
    """ Update the given CVE

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    case_type(str): Object list to iterate
    manager_id(str): Manager ID
    account(str): Account name
    config(Configuration): Configuration object

    Returns
    -------
    str: String without spaces
    """
    results = []
    # this is the list of fields that will be evaluated
    fields_query = ["CaseNumber", "Status", "OwnerId", "Product_Level_Three__c", "Subject",
                    "Resolution_Plan__c", "CreatedDate", "LastModifiedDate", "Id", "JIRA_ID__c"]

    # Create the relationship dict between ids and alias and the
    # reverse version to avoid multiple requests.
    a_dict, b_dictionary = users.sf_user_get_employees(sf_ins, manager_id)

    # the user will be able to select cse or all the cases under an specific mananger
    if case_type == "cse":
        alias = enquiries.choose('Choose one of these options: ', a_dict)
        query_data = "SELECT "+','.join(fields_query) + " FROM Case " + \
            "WHERE Subject LIKE '%CVE-%' AND OwnerId = '" + \
            a_dict[alias] + "' AND Account_Name__c LIKE '%" + account + \
            "%' AND Status != 'Closed' ORDER BY Product_Level_Three__c " + \
            "ASC NULLS FIRST"
    elif case_type == "all":
        query_data = "SELECT " + \
            ','.join(fields_query) + " FROM Case WHERE Subject " + \
            "LIKE '%CVE-%' AND Account_Name__c LIKE '%Cisco Systems%' " + \
            "AND Status != 'Closed' ORDER BY Product_Level_Three__c  " + \
            "ASC NULLS FIRST"
    else:
        print("Select the option cse/all ... ")
        return results

    data = sf_ins.query_all_iter(query_data)
    # adding the headers into returning results
    jira_status = "empty"
    jira_resolution = "empty"
    commit_id = "empty"

    feils_q_copy = fields_query.copy()
    feils_q_copy.append('Jira_Status')
    feils_q_copy.append("Jira_Resolution")
    feils_q_copy.append("Commit_id")
    results.append(feils_q_copy)
    for row in data:
        items = []
        for header in feils_q_copy:
            try:
                if row[header]:
                    if header == "OwnerId":
                        items.append(b_dictionary[row[header]])
                    elif header == "Subject":
                        info = (
                            row[header][:75] + ' ... ') if len(row[header]) > 75 else row[header]
                        items.append(info)
                    elif header == "CreatedDate":
                        items.append(row[header].split('T')[0])
                    elif header == "LastModifiedDate":
                        items.append(row[header].split('T')[0])
                    elif header == "Id":
                        item_id = '<a href='+URL_BASE + \
                            row[header]+'>'+row['CaseNumber']+'</a>'
                        items.append(item_id)
                    elif header == "JIRA_ID__c":
                        defects1 = row[header].split()
                        ccm_defects = [
                            item for item in defects1 if item.startswith('LINCCM')]
                        string = ""
                        jira_status = ""
                        jira_resolution = ""
                        commit_id = ""
                        if ccm_defects:  # extract only ccm defects is they exist
                            for defcts in ccm_defects:
                                print("Processing " + defcts)
                                res = defects.jira_inspect_keys(defcts, config)
                                string += str(tools.add_html_tags2defect(defcts) + "<br>")
                                jira_status += html_color_tags(
                                    res[0]['status'])+"<br>"
                                jira_resolution += html_color_tags(
                                    res[0]['resolution'])+"<br>"
                                if (res[0]['status'] == 'Resolved') or (res[0]['status'] == 'Checked In'):
                                    _, commit_id = defects.get_jira_commit(
                                        defcts, False, config)
                                else:
                                    commit_id += 'no commit id<br>'
                        else:
                            for defcts in defects1:
                                print("Processing " + defcts)
                                res = defects.jira_inspect_keys(defcts, config)
                                string += str(tools.add_html_tags2defect(defcts) + "<br>")
                                jira_status += html_color_tags(
                                    res[0]['status'])+"<br>"
                                jira_resolution += html_color_tags(
                                    res[0]['resolution'])+"<br>"
                                if (res[0]['status'] == 'Resolved') or (res[0]['status'] == 'Checked In'):
                                    _, commit_id = defects.get_jira_commit(
                                        defcts, False, config)
                                else:
                                    commit_id += 'no commit id<br>'

                        items.append(string)
                    else:
                        items.append(row[header])
                else:  # this will happens if the feild is empty
                    items.append('empty')
            except KeyError:
                if header == "Jira_Status":
                    items.append(jira_status)
                elif header == "Jira_Resolution":
                    items.append(jira_resolution)
                elif header == "Commit_id":
                    items.append(commit_id)

                else:
                    items.append("N/A")
        results.append(items)

    tools.dict2html(results, 'reports/sf_cve_results.html',
                    "Salesforce CVE Results")
    return results
