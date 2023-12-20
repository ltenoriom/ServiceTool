''' Helper module to interact as Manager
'''
import re
from itertools import cycle
import click
import enquiries

from JIRA import defects
from Misc import tools
from Salesforce import case, case_comment, users

# FIXME Move all of this to a single configuration file
URL_BASE = 'https://windriver.my.salesforce.com/'
PROJECT_TRANSLATION = {"Linux 6 - Legacy": "LIN6", "Linux 8 - Legacy": "LIN8",
                       "Linux LTS 18": "LIN1018", "Linux LTS 19": "LIN1019"}


def cis_cve_assign(sf_ins, manager_alias, config):
    """ This function will take all the unnasigned CVE Cisco cases team
    members in NA.COSTARICA

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    manager_alias(str): Manager alias

    Returns
    -------
    str: String without spaces
    """
    # query will contain only cases with the user Linux_Platform
    query_string = "SELECT CaseNumber, Product_Level_Three__c, Subject " + \
                   "FROM Case WHERE Account_Name__c LIKE '%CISCO%' " \
                   "AND OwnerId = '00G16000004GPUPEA4' "

    # Retrieve all of the results in a single local method call use
    dict_data = sf_ins.query_all(query_string)

    # translation to generate ID
    manager_id = users.sf_user_translate(sf_ins, 'Alias', 'Id', manager_alias)

    # Get the dicts for aliases and ids
    a_dict, _ = users.sf_user_get_employees(sf_ins, manager_id)

    count = 0
    for con in dict_data['records']:
        count = count + 1
        tools.print_warning("Defect : " + str(count) +
                            "-- Case Number: " + con['CaseNumber'])
        case_id = case.sf_case_get_id(sf_ins, con['CaseNumber'])

        res = con['Subject'].find('CVE')
        cve_id = con['Subject'][res:].split(' ')[0]

        lin_ver = tools.map_linux_version(con['Product_Level_Three__c'])
        data = defects.cve_project(cve_id, lin_ver, config)
        if not data:
            if lin_ver == "LIN6":  # check in linux 8 when LIN6 does not exist
                lin_ver = "LIN8"
                data = defects.cve_project(cve_id, lin_ver, config)
                if not data:
                    string = "NOT FOUND"
                else:
                    string = "NOT FOUND ON LIN6"
            else:
                string = "NOT FOUND"
        else:
            string = str(data)

        buffer = """
            Case Number: %s
            Case Link: %s/%s
            Linux Version: %s
            CVE Number: %s
            %s
        """ % (con['CaseNumber'], URL_BASE, case_id, lin_ver, cve_id, string)

        print(buffer)
        sf_case = sf_ins.Case.get(case_id)

        print("Review Current Values:")
        tools.print_list_no_spaces("Resolution_Summary__c", sf_case)
        tools.print_list_no_spaces("Resolution_Plan__c", sf_case)
        tools.print_list_no_spaces("CSE_Comments__c", sf_case)
        tools.print_list_no_spaces("Status", sf_case)

        if tools.yes_or_no("Do you want to update the case? "):
            alias = enquiries.choose('Choose one of these options: ', a_dict)
            owner_id = a_dict[alias]
            case_comment.post_comment(
                sf_ins, con['CaseNumber'], buffer, "internal")
            case_comment.post_comment(sf_ins, con['CaseNumber'],
                                      "Linux Group will take care of the " +
                                      "case and provide further " +
                                      "information/questions if needed.",
                                      "all")
            sf_ins.Case.update(case_id,
                               {"Case_Complexity__c": "Standard",
                                "Complexity_Detail1__c": "See Resolution Summary",
                                "Product_Level_Four__c": "Security",
                                "CSE_Comments__c": "Case Updated by CveTool CSE.",
                                "Status": 'Defect Filed', "Root_Cause__c": 'CCM',
                                "Resolution_Plan__c": "Case Will be processed by CCM"})
            sf_ins.Case.update(case_id, {'OwnerId': owner_id})

            sf_case = sf_ins.Case.get(case_id)

            print("Review New Values:")
            tools.print_list_no_spaces("Resolution_Summary__c", sf_case)
            tools.print_list_no_spaces("Resolution_Plan__c", sf_case)
            tools.print_list_no_spaces("CSE_Comments__c", sf_case)
            tools.print_list_no_spaces("Status", sf_case)
            tools.print_list_no_spaces("Status", sf_case)
            tools.print_list_no_spaces("OwnerId", sf_case)

        if tools.yes_or_no("Do you want to process the case? "):
            case.jiras(sf_ins, con['CaseNumber'], config)


def cis_cve_process(sf_ins, config):
    """ Use this function when new CVEs are created and you want full
    processing.

    The cve_owners define to which user to assign CVEs

    Attributes
    ----------
    sf_ins(SalesForce): SalesForce instance
    config(Configuration): Application configuration.

    Returns
    -------
    bool: True if success
    """
    # query will contain only cases with the user LinuxPlatform_CXG
    query_string = "SELECT Id,CaseNumber,Product_Level_Three__c,Subject,\
                    Description,Owner.Name,Status,JIRA_ID__c,Priority \
                    FROM Case WHERE Account_Name__c \
                    LIKE '%CISCO%' AND OwnerId = '00G16000004GPUPEA4' \
                    ORDER BY CaseNumber"

    # As a convenience, to retrieve all of the results in a single local method call use
    dict_data = sf_ins.query_all(query_string)

    # Iterate between theese users
    cve_owners = [
        '0051M000007p2BFQAY',  # MCaamano
        '0051M000008OkhRQAS',  # aariasch
    ]
    owner_id = cve_owners[0]  # Init with first user

    users_pool = cycle(cve_owners)
    prev_cve_id = 0  # Used to assign the same type of CVE to same user
    for rec in dict_data['records']:
        tools.print_warning("Case Number: " + rec['CaseNumber'])
        print("Review Case Values:")
        print(rec['Subject'])
        print(rec['Priority'])

        linux_version = rec['Product_Level_Three__c']
        cve_number = re.findall("(CVE-20\d\d-\d*)", rec['Subject'])[0]

        jira_defects = []
        if rec['JIRA_ID__c'] is not None:
            print("JIRA(s) associated:")
            jira_defects = rec['JIRA_ID__c'].split()
            # For every defect in this list of defects
            for defect in jira_defects:
                print(defect)

        if prev_cve_id != cve_number:
            owner_id = next(users_pool)
        prev_cve_id = cve_number
        jiras = defects.cve_list(cve_number, config)

        filt_jiras = []
        options = {}
        i = 0
        tools.print_cyan('Found the following defects:')
        for jira in jiras:
            if 'LIN1019' == jira['project'] or \
                'LIN1018' == jira['project'] or \
                'LIN8' == jira['project'] or \
                    'LIN6' == jira['project']:
                filt_jiras += [jira]
                print(jira['defect'] + ' - ' + jira['summary'] +
                      ' - ' + jira['resolution'])
                options[jira['project']] = i
                i += 1
        options['None'] = i  # To skip clonning a defect

        response = enquiries.choose(
            'Pick WRL defect version to clone', options)

        if(options.get(response) == i):  # User chose not to clone any defect
            print('Posting only generic first response')
        else:
            jira = filt_jiras[options.get(response)]
            tools.print_cyan("Cloning: " + jira["defect"])
            print("CVE: " + jira["cve"])
            print("Summary: " + jira["summary"])
            print("Status: " + jira["status"])
            print("Resolution: " + jira["resolution"])
            print("URL: https://jira.wrs.com/browse/" + jira["defect"])

            for defect in jira_defects:
                if jira["defect"] == defect:
                    print("Already associated")
                    associated = True

            new_defect = defects.clone(
                sf_ins, jira["defect"], "LINCCM", "", "cisco", linux_version, config)
            if new_defect:
                defects.comment(
                    new_defect, rec['Description'], config)
                case.associate(
                    sf_ins, rec["CaseNumber"], new_defect, config)
                case.sf_set_resolution(
                    sf_ins, rec["CaseNumber"], "Waiting for backporting by CCM")
                print(
                    "Don't forget to modify: https://jira.wrs.com/browse/" + new_defect)
            else:
                tools.print_failure(
                    "Failed to clone and associate this defect")

        sf_ins.Case.update(rec['Id'],
                           {"Case_Complexity__c": "Standard", "Complexity_Detail1__c": "See Resolution Summary",
                            "Product_Level_Four__c": "Security", "CSE_Comments__c": "Case Updated by CveTool CSE.",
                            "Status": 'Defect Filed', "Root_Cause__c": 'CCM',
                            "Resolution_Plan__c": "Case Will be processed by CCM"})
        sf_ins.Case.update(rec['Id'], {'OwnerId': owner_id})
        case_comment.post_comment(sf_ins, rec['CaseNumber'],
                                  "Linux Group will take care of the " +
                                  "case and provide further " +
                                  "information/questions if needed.",
                                  "all")

        sf_case = sf_ins.Case.get(rec['Id'])
        tools.print_cyan("Review Updated Values:")
        print('OwnerId: ' + owner_id)
        tools.print_list_no_spaces("Resolution_Summary__c", sf_case)
        tools.print_list_no_spaces("Resolution_Plan__c", sf_case)
        tools.print_list_no_spaces("CSE_Comments__c", sf_case)
        tools.print_list_no_spaces("Status", sf_case)

    msg = 'Close defects with commit?'
    if click.confirm(msg, default=False):
        print('Searching for commits...')
        process_defects_ready(sf_ins, config)

    return True


def process_defects_ready(sf_ins, config):
    """ Update SF case if defect is done.

    The Jira defects are done if they have a commit.

    Attributes
    ----------
    sf_ins(SalesForce): SalesForce instance
    config(Configuration): Application configuration.

    Returns
    -------
    bool: True if success
    """
    fields_query = ["CaseNumber", "Status", "OwnerId", "Product_Level_Three__c", "Subject",
                    "Resolution_Plan__c", "CreatedDate", "LastModifiedDate", "Id", "JIRA_ID__c"]
    query_data = "SELECT " + \
        ','.join(fields_query) + " FROM Case WHERE Subject " + \
        "LIKE '%CVE-%' AND Account_Name__c LIKE '%Cisco Systems%' " + \
        "AND Status != 'Closed' ORDER BY Product_Level_Three__c  " + \
        "ASC NULLS FIRST"
    data_iterator = sf_ins.query_all_iter(query_data)  # returns an iterator

    for row in data_iterator:
        # Get all the CCM defects
        jiras = row['JIRA_ID__c']
        tools.print_cyan(
            'Case: ' + row['CaseNumber'] + ' Defect: ' + jiras + ' Details: ' + row['Subject'][0:30])
        if jiras is None:
            continue

        ccm_defects = [item for item in jiras.split()
                       if item.startswith('LINCCM')]
        defects_with_commit = False
        final_commit = ''
        for defect_id in ccm_defects:
            res = defects.jira_inspect_keys(defect_id, config)
            if res[0]['status'] != 'Resolved' and res[0]['status'] != 'Checked In':
                continue  # Do not check WIP defect

            _, commit_id = defects.get_jira_commit(defect_id, True, config)
            if commit_id != 'not_found':
                final_commit += commit_id
                defects_with_commit = True

        if defects_with_commit:
            case_number = row['CaseNumber']
            case.sf_close_cve_case_with_commit(
                sf_ins, case_number, final_commit, config)

    return True
