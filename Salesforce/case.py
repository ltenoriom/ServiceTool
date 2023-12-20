''' Module to interact with Salesforce

Additional information:
Possible situations for cisco closure
1. the cve does not affect the version (Linux 8) RCPL33, (Linux LTS18) RCPL16,
    (Linux 6) RCPL38.
2. the cve does have a commit in place and we are going to close the case
    because it has been pushed into ccm layer.
3. The cve patch has been included on a previous version.
'''

import csv
import datetime
from itertools import filterfalse
import re
import logging
from pathlib import Path
from typing import Counter
import pandas as pd
import collections
import click
import enquiries
from langdetect import detect
from getpass import getpass
from JIRA import defects
from Misc import tools
from Salesforce import users,case_comment
import smtplib
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText





PROJECT_TRANSLATION = {"Linux 6 - Legacy": "LIN6",
                       "Linux 8 - Legacy": "LIN8",
                       "Linux LTS 18": "LIN1018",
                       "Linux LTS 19": "LIN1019"}
URL_BASE = 'https://windriver.lightning.force.com/'




def sf_case_get_id(sf_ins, number,verbose=True):
    if number == '':
        tools.print_failure('Empty case number to translate to ID')
        return False
    else:
        if len(number) == 6:
            number = '00' + number
        elif len(number) == 7:
            number = '0' + number
        else:
            pass

    if verbose:
        print("Retrieving case ID for " + number)

    case_list = sf_ins.query_all("SELECT Id FROM Case WHERE CaseNumber LIKE '%s'" % number)
    return case_list['records'][0]['Id']


def call_all_active_accounts(sf):
    query_account_name = sf.query_all("SELECT Id,Name FROM Account")
    _acc_od = []
    for account in query_account_name['records']:
        _acc_od.append({'Id': account['Id'], 'Name': account['Name']})

    return _acc_od

def sf_case_get_report(sf_ins, report_id):
    """ This function could retrieve the data from a direct report without grouping

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    report_id(str) :  report id requested

    Returns
    -------
    boolean: True on success. False otherwise
    """
    query_all = "/services/data/v49.0/analytics/reports/" + report_id
    dict_data = sf_ins.query_more(query_all, True)
    print('Extracted from:' + URL_BASE + '/r/Report/' + report_id + '/view\n\n')

    headers = []
    for con in dict_data['reportExtendedMetadata']['detailColumnInfo']:
        headers.append(con)

    print(headers)

    count = 0
    results = [headers]
    for con in dict_data['factMap']['T!T']['rows']:
        items = []
        for don in con['dataCells']:
            items.append(don['label'])
        count = count + 1
        results.append(items)

    print(results)
    print(str(count) + " new items have downloaded")
    tools.dict2html(results, "reports/file.html", "test")
    return True


def sf_topbox_costa_rica_team(sf):
    today = datetime.date.today()
    first = today.replace(day=1)
    lastMonth = first - datetime.timedelta(days=1)
    __last_month = (lastMonth.strftime("%B %Y"))

    '''Calculation of last month NPS'''
    fields = "Recommend_Raiting__c,Satisfaction_Raiting__c,Promoter__c,Detractor__c,Passive__c,Customer_Effort_Score__c"
    SR_LAST_MONTH = sf.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = LAST_MONTH".format(fields))
    SR_THIS_YEAR = sf.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = THIS_YEAR".format(fields))
    Last_month_nps = calculate_nps_per_bundle(SR_LAST_MONTH['records'],'THIS_YEAR') 
    this_year = calculate_nps_per_bundle(SR_THIS_YEAR['records'],'THIS_YEAR') 

    html_code = "<p>We are happy to announce our last month NPS =  <b>{}</b><br>".format(Last_month_nps['NPS'])
    html_code += "Our Year to date NPS = <b>{}</b></p>".format(this_year['NPS'])      

    __users_dict__ = users.get_list_of_users(sf)
    ''' Get id,OwnerId name and case number for all the cases '''
    query = "SELECT Id,OwnerId,CaseNumber FROM Case WHERE Status = 'Closed' AND CreatedDate = THIS_YEAR"
    case_list = sf.query_all(query)
    __list_of_cases__ = []
    for case in case_list['records']:
        __list_of_cases__.append({'Id': case['Id'], 'OwnerId': case['OwnerId'], 'CaseNumber': case['CaseNumber']})

    '''Returns rows of the top surveys cases'''
    query_temp = "SELECT Id, Case__c,OwnerId,Chat_Agent__c,Customer_Effort_Score__c,"
    query_temp += "CreatedDate,Communication_Feedback__c, Customer_Support_Engineer_Feedback__c,"
    query_temp += "Other_Feedback__c,Quality_Of_Resolution_Feedback__c, Recommend_Raiting__c,"
    query_temp += "Satisfaction_Raiting__c "
    query_temp += "FROM Survey_Result__c "
    query_temp += "WHERE Satisfaction_Raiting__c = 10 "
    query_temp += "AND CreatedDate = LAST_MONTH "
    query_temp += "ORDER BY CreatedDate ASC"
    query = sf.query_all(query_temp)
    __topbox__ = []
    __cases__ = []
    __receivers__ = []
    __feedback__ = []
    for row in query['records']:
        for case in __list_of_cases__:
            if case['Id'] == row['Case__c']:
                rr = list(filter(lambda person: person['Id'] == case['OwnerId'], __users_dict__))
                agent_name  = rr[0]['Name'] if rr else 'None'
                __topbox__.append({'Id': row['Id'], 'OwnerId': case['OwnerId'], 'CaseNumber': case['CaseNumber'], 'Agent': agent_name})
                __cases__.append(case['CaseNumber'])
                __cases__.append(case['CaseNumber'])
                __receivers__.append(agent_name)
                if row['Other_Feedback__c'] is not None:
                    __feedback__.append(row['Other_Feedback__c'])
                break

    __top_performers__ = [] 

    topbox_amount = len(query['records'])

    for i in __receivers__:
        __top_performers__.append({"CSE":i,"Count":__receivers__.count(i)})


    __top_performers__ = sorted(__top_performers__, key=lambda k: k['Count'], reverse=True)
    new_list = []
    for i in __top_performers__:
        if i not in new_list:
            new_list.append(i)
    __top_performers__ = new_list
    
    with open('src/topbox.html', 'r') as f:
        email_body = f.read() # Read whole file in the file_content string

    df_new = pd.DataFrame(__top_performers__)
    df_new = df_new.sort_values(by=['Count'], ascending=False)
    max_sur = df_new['Count'].max()
    result = df_new.loc[df_new['Count'] == max_sur]['CSE']
    result = ", ".join(result.to_list())
    html_comment = get_comments_blockquote(__feedback__)
    html = df_new.to_html(index=False)
    html = html.replace('<table border="1" class="dataframe">', '<table border="0" class="dataframe" style="width:100%">')
    '''get today date'''
    today = datetime.datetime.now()
    today = today.strftime("%d/%m/%Y")
    email_body = email_body.replace('{date}', today)
    email_body = email_body.replace('{topbox_amount}', str(topbox_amount))
    email_body = email_body.replace("{top_cse}", result)
    email_body = email_body.replace("{num_top_cse}", str(max_sur))
    email_body = email_body.replace("{nps_information}",html_code)
    email_body = email_body.replace("{month}", __last_month)
    email_body = email_body.replace(
            "{top_surveys}", get_ranking_table(__top_performers__))
    email_body = email_body.replace(
            "{comments}", html_comment)

    __action__ = tools.yes_or_no('Do you want to send the email?')
    if __action__: 
        subject = "Perfect Score list for CSO for {}".format(__last_month)
        me = "Esteban.ZunigaMora@windriver.com"
        you = "Esteban.ZunigaMora@windriver.com"
        cc  = "esteban.zuniga@protonmail.com"
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = me
        msg['To'] = you
        msg['Cc']=cc
        msg.attach(MIMEText(email_body, 'html'))
        mailserver = smtplib.SMTP('smtp.office365.com', 587)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(me, getpass("User {} , please insert your Password: ".format(me)))
        mailserver.sendmail(me, you, msg.as_string())
        mailserver.quit()
        print("Topbox report sent to {}".format(you))

    with open('reports/topbox.html', 'w') as f:
        f.write(email_body)
    print("Topbox report saved in reports/topbox.html")
  

def predominant_sign(data,__key__):
    signs = Counter(k[__key__] for k in data if k.get(__key__))
    for sign, count in signs.most_common():
        print(sign, count)

def get_ranking_table(__dict__):
    temp_ranking = ""
    last_count = 0
    rank = 0



    for row in __dict__:
        if last_count != row['Count']:
            rank += 1
        temp_ranking = temp_ranking + "<tr><td>" + str(rank) + "</td><td>" + row['CSE'] + "</td><td>" + str(row['Count']) + "</td></tr>"
        last_count = row['Count']

    return temp_ranking

def get_comments_blockquote(__feedback__):



    temp_comments = ""
    count = 0

    for comment in __feedback__:
        if count >= 10:
            break
        if comment is not None:
            ''' check if the comment is in english '''
            if detect(comment) == 'en':
                temp_comments += "<blockquote>{}</blockquote>".format(comment)
                count += 1
        
    return temp_comments


def calculate_nps_per_bundle(data,timeframe):
    '''calculate the nps for each period'''
    Promoter__c = 0 
    Detractor__c = 0
    Passive__c = 0
    csat__ = []
    ces__ = []
    for value in data:
        if value['Recommend_Raiting__c'] is not None:
            Promoter__c += value['Promoter__c']
            Detractor__c +=value['Detractor__c']
            Passive__c += value['Passive__c']
        if value['Satisfaction_Raiting__c'] is not None:
            csat__.append(value['Satisfaction_Raiting__c'])
        if value["Customer_Effort_Score__c"] is not None:
            ces__.append(value["Customer_Effort_Score__c"])
        
    csat = round(pd.Series(csat__).mean(),2)*10
    nps  = round((Promoter__c - Detractor__c) /(Detractor__c + Promoter__c+Passive__c),2)*100
    ces  = round(pd.Series(ces__).mean(),2)
    return {'NPS':nps,'CSAT':csat,'CES':ces}

def sf_topbox(sf,config):

    today = datetime.date.today()
    first = today.replace(day=1)
    lastMonth = first - datetime.timedelta(days=1)
    __last_month = (lastMonth.strftime("%B %Y"))

    '''Calculation of last month NPS'''
    fields = "Recommend_Raiting__c,Satisfaction_Raiting__c,Promoter__c,Detractor__c,Passive__c,Customer_Effort_Score__c"
    SR_LAST_MONTH = sf.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = LAST_MONTH".format(fields))
    SR_THIS_YEAR = sf.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = THIS_YEAR".format(fields))
    Last_month_nps = calculate_nps_per_bundle(SR_LAST_MONTH['records'],'THIS_YEAR') 
    this_year = calculate_nps_per_bundle(SR_THIS_YEAR['records'],'THIS_YEAR') 

    html_code = "<p>We are happy to announce our last month NPS =  <b>{}</b><br>".format(Last_month_nps['NPS'])
    html_code += "Our Year to date NPS = <b>{}</b></p>".format(this_year['NPS'])      

    __users_dict__ = users.get_list_of_users(sf)
    ''' Get id,OwnerId name and case number for all the cases '''
    query = "SELECT Id,OwnerId,CaseNumber FROM Case WHERE Status = 'Closed' AND CreatedDate = THIS_YEAR"
    case_list = sf.query_all(query)
    __list_of_cases__ = []
    for case in case_list['records']:
        __list_of_cases__.append({'Id': case['Id'], 'OwnerId': case['OwnerId'], 'CaseNumber': case['CaseNumber']})

    '''Returns rows of the top surveys cases'''
    query_temp = "SELECT Id, Case__c,OwnerId,Chat_Agent__c,Customer_Effort_Score__c,"
    query_temp += "CreatedDate,Communication_Feedback__c, Customer_Support_Engineer_Feedback__c,"
    query_temp += "Other_Feedback__c,Quality_Of_Resolution_Feedback__c, Recommend_Raiting__c,"
    query_temp += "Satisfaction_Raiting__c "
    query_temp += "FROM Survey_Result__c "
    query_temp += "WHERE Satisfaction_Raiting__c = 10 "
    query_temp += "AND CreatedDate = LAST_MONTH "
    query_temp += "ORDER BY CreatedDate ASC"
    query = sf.query_all(query_temp)
    __topbox__ = []
    __cases__ = []
    __receivers__ = []
    __feedback__ = []
    for row in query['records']:
        for case in __list_of_cases__:
            if case['Id'] == row['Case__c']:
                rr = list(filter(lambda person: person['Id'] == case['OwnerId'], __users_dict__))
                agent_name  = rr[0]['Name'] if rr else 'None'
                __topbox__.append({'Id': row['Id'], 'OwnerId': case['OwnerId'], 'CaseNumber': case['CaseNumber'], 'Agent': agent_name})
                __cases__.append(case['CaseNumber'])
                __cases__.append(case['CaseNumber'])
                __receivers__.append(agent_name)
                if row['Other_Feedback__c'] is not None:
                    __feedback__.append(row['Other_Feedback__c'])
                break

    __top_performers__ = [] 

    topbox_amount = len(query['records'])

    for i in __receivers__:
        __top_performers__.append({"CSE":i,"Count":__receivers__.count(i)})


    __top_performers__ = sorted(__top_performers__, key=lambda k: k['Count'], reverse=True)
    new_list = []
    for i in __top_performers__:
        if i not in new_list:
            new_list.append(i)
    __top_performers__ = new_list
    
    with open('src/topbox.html', 'r') as f:
        email_body = f.read() # Read whole file in the file_content string

    df_new = pd.DataFrame(__top_performers__)
    df_new = df_new.sort_values(by=['Count'], ascending=False)
    max_sur = df_new['Count'].max()
    result = df_new.loc[df_new['Count'] == max_sur]['CSE']
    result = ", ".join(result.to_list())
    html_comment = get_comments_blockquote(__feedback__)
    html = df_new.to_html(index=False)
    html = html.replace('<table border="1" class="dataframe">', '<table border="0" class="dataframe" style="width:100%">')
    '''get today date'''
    today = datetime.datetime.now()
    today = today.strftime("%d/%m/%Y")
    email_body = email_body.replace('{date}', today)
    email_body = email_body.replace('{topbox_amount}', str(topbox_amount))
    email_body = email_body.replace("{top_cse}", result)
    email_body = email_body.replace("{num_top_cse}", str(max_sur))
    email_body = email_body.replace("{nps_information}",html_code)
    email_body = email_body.replace("{month}", __last_month)
    email_body = email_body.replace(
            "{top_surveys}", get_ranking_table(__top_performers__))
    email_body = email_body.replace(
            "{comments}", html_comment)

    __action__ = tools.yes_or_no('Do you want to send the email?')
    if __action__: 
        subject = "Perfect Score list for CSO for {}".format(__last_month)
        me = "Esteban.ZunigaMora@windriver.com"
        you = "Esteban.ZunigaMora@windriver.com"
        cc  = "esteban.zuniga@protonmail.com"
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = me
        msg['To'] = you
        msg['Cc']=cc
        msg.attach(MIMEText(email_body, 'html'))
        mailserver = smtplib.SMTP('smtp.office365.com', 587)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(me, getpass("User {} , please insert your Password: ".format(me)))
        mailserver.sendmail(me, you, msg.as_string())
        mailserver.quit()
        print("Topbox report sent to {}".format(you))

    with open('reports/topbox.html', 'w') as f:
        f.write(email_body)
    print("Topbox report saved in reports/topbox.html")

    
def unique(list1):
  
    # initialize a null list
    unique_list = []
  
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

def sf_case_get_info(sf_ins, number, config):
    """ Get the information from a single case

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str):  number of the case
    config(Config): Configuration object

    Returns
    -------
    boolean: True on success. False otherwise
    """
    logging.debug("Retrieving data of case number: " + number)
    tools.print_ok("\n\nRetrieving data of case number: " + number)
    case_id = sf_case_get_id(sf_ins, number)
    query_list = ["Id", "Account_Name__c", "CaseNumber", "OwnerId",
                  "LastModifiedDate", "LastModifiedById", "Subject",
                  "Status", "JIRA_ID__c", "Resolution_Plan__c"]
    case_list_query = "SELECT " + ",".join(query_list)
    case_list_query += " FROM Case WHERE Id = '%s'" % case_id
    case_list = sf_ins.query_all(case_list_query)
    for data in case_list['records']:
        for header in query_list:
            if header == "Id":
                info = URL_BASE + data[header]
                tools.print_item_value(header, info)
            elif header == "Resolution_Plan__c":
                info = data['Resolution_Plan__c']
                if not info:
                    info = "empty"
                info = (info[:75] + '..') if len(info) > 75 else info
                tools.print_item_value(header, info)
            elif header == "Subject":
                info = data['Subject']
                info = (info[:75] + '..') if len(info) > 75 else info
                tools.print_item_value(header, info)
            elif header == "LastModifiedById":
                tools.print_item_value(
                    header, users.sf_user_id2name(sf_ins, data[header]))
            elif header == "OwnerId":
                tools.print_item_value(
                    header, users.sf_user_id2name(sf_ins, data[header]))
            elif header == "JIRA_ID__c":
                if data['JIRA_ID__c']:
                    jira_defects = data['JIRA_ID__c'].split()
                    for defect in jira_defects:
                        lastmod_jira = defects.jira_get_last_mod_date(
                            defect, config)
                        created_jira = defects.jira_get_created_date(
                            defect, config)
                        item = "Jira Defect " + "https://jira.wrs.com/browse/" + \
                               defect + " [" + lastmod_jira + \
                               ';' + created_jira + ']'
                        tools.print_item_value(header, item)
                else:
                    tools.print_item_value(header, "No Jiras Found")
            else:
                tools.print_item_value(header, data[header])

    return True


def sf_set_status_case(sf_ins, number, new_status):
    """ Set the new case status

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str):  number of the case.
    new_status(str): new status requested.

    Reference: https://workbench.developerforce.com/query.php
    """
    logging.debug("Retrieving data of case number: " + number)
    list_of_status = {
        "Open", 
        "Closed", 
        "In Progress", 
        "Customer Action",
        "Assigned", 
        "Enhancement Request Filed",
        "Solution Proposed", 
        "Defect Filed",
        "Defect Relief Provided"}

    # we need to ge the case Id before obtaining the dictionary
    case_id = sf_case_get_id(sf_ins, number)

    # To get a dictionary with all the information regarding that record
    f_b = sf_ins.Case.get(case_id)
    current_status = f_b["Status"]
    if new_status in list_of_status:
            print("New Status is :", new_status)
            new_status_in = new_status
    else:
        return

    #if enquiries.confirm("Do you want to modify the status?"):
    #    if new_status in list_of_status:
    #        print("New Status is :", new_status)
    #        new_status_in = new_status
    #    else:
    #        new_status_in = enquiries.choose(
    #            'Choose one of these options: ', list_of_status)
    #else:
    #    print("Case Status Not Changed")
    #    return

    if current_status == new_status_in:
        print("Case Status Not Changed")
        return

    if new_status_in == "Closed":
        print('We will close the case now!!')
        summ_n_resol = "Case Closed per previous agreement with the customer- GDMS"
        data = {"Case_Complexity__c": "Standard", "Complexity_Detail1__c": "See Resolution Summary",
                "Product_Level_Four__c": "Security","Root_Cause__c":'Vulnerability','Status':new_status_in,
                "Resolution_Summary__c": summ_n_resol, "Resolution_Plan__c": summ_n_resol,
                "CSE_Comments__c": "GDMS Case Resolved per Agreemenet on the sync up meetings with the customer"}
    else: 
        data = {"Status": new_status_in}
    sf_ins.Case.update(case_id, data)

    f_b = sf_ins.Case.get(case_id)

    tools.print_cyan("Review New Values:")
    tools.print_list_no_spaces("Status", f_b)
    tools.print_list_no_spaces("CSE_Comments__c", f_b)
    tools.print_list_no_spaces("Resolution_Summary__c", f_b)
    tools.print_list_no_spaces("Resolution_Plan__c", f_b)
    tools.print_list_no_spaces("CSE_Comments__c", f_b)


def sf_case_update(sf_ins, case_number, text_argument):
    """ Update case information

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    case_number(str): Case ID
    text_argument(str): Comment for resolution and summary
    """
    case_id = sf_case_get_id(sf_ins, case_number)
    tools.print_cyan("Review Case URL: " + URL_BASE + case_id)
    # we need to ge the case Id before obtaining the dictionary
    case_id = sf_case_get_id(sf_ins, case_number)

    # To get a dictionary with all the information regarding that record
    f_b = sf_ins.Case.get(case_id)

    tools.print_cyan("Review Current Values:")
    tools.print_list_no_spaces("Resolution_Summary__c", f_b)
    tools.print_list_no_spaces("Resolution_Plan__c", f_b)
    tools.print_list_no_spaces("CSE_Comments__c", f_b)
    tools.print_list_no_spaces("Status", f_b)
    tools.print_list_no_spaces("Product_Level_Three__c", f_b)

    if f_b["Product_Level_Three__c"] == "Linux 6 - Legacy":
        target_layer = "WRL6 RCPL29 & RCPL38 layers."
    elif f_b["Product_Level_Three__c"] == "Linux 8 - Legacy":
        target_layer = "WRL8 RCPL33  layer."
    elif f_b["Product_Level_Three__c"] == "Linux LTS 18":
        target_layer = "WRL LTS18 RCPL16  layer."
    else:
        target_layer = "TO MODIFY"

    options = ['Resolution', 'Status', "None"]

    response = enquiries.choose(
        'Pick the fields you want to change', options, multi=True)

    if "None" in response:
        tools.print_failure("You selected None, exiting....")
        return

    if tools.yes_or_no("Is the text argument only the commit id ?"):
        summ_n_resol = "CCM pushed out commit " + \
                       text_argument + " to the " + target_layer
    else:
        summ_n_resol = text_argument

    if "Resolution" in response:
        data = {"Case_Complexity__c": "Standard", "Complexity_Detail1__c": "See Resolution Summary",
                "Product_Level_Four__c": "Security",
                "Resolution_Summary__c": summ_n_resol, "Resolution_Plan__c": summ_n_resol,
                "CSE_Comments__c": "Case Updated by CSTool"}
        sf_ins.Case.update(case_id, data)

    if "Status" in response:
        # the case will be updated by the user
        sf_set_status_case(sf_ins, case_number, "None")

    # To get a dictionary with all the information regarding that record
    f_b = sf_ins.Case.get(case_id)

    tools.print_cyan("Review New Values:")
    tools.print_list_no_spaces("Resolution_Summary__c", f_b)
    tools.print_list_no_spaces("Resolution_Plan__c", f_b)
    tools.print_list_no_spaces("CSE_Comments__c", f_b)
    tools.print_list_no_spaces("JIRA_ID__c", f_b)
    tools.print_list_no_spaces("Status", f_b)


def sf_close_cve_case_with_commit(sf_ins, case_number, commit_id, config):
    """ Close a SF CVE case with a commit ID

    The commit ID will be extender with a default message like:
    'CCM pushed the <commit_id> commit to the repository'.

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    case_number(str): Case ID
    commit_id(str): Commit ID
    config(Configuration): Application configuration
    """
    case_id = sf_case_get_id(sf_ins, case_number)

    # To get a dictionary with all the information regarding that record
    f_b = sf_ins.Case.get(case_id)

    tools.print_ok('Ready to close with commit: ' + commit_id)
    if not tools.yes_or_no("Proceed?"):
        return

    if f_b["Product_Level_Three__c"] == "Linux 6 - Legacy":
        target_layer = "WRL6 RCPL38 layer."
    elif f_b["Product_Level_Three__c"] == "Linux 8 - Legacy":
        target_layer = "WRL8 RCPL33  layer."
    elif f_b["Product_Level_Three__c"] == "Linux LTS 18":
        target_layer = "WRL LTS18 RCPL16 layer."
    else:
        target_layer = "TO MODIFY"

    summ_n_resol = "CCM pushed out commit " + \
        commit_id + " to the " + target_layer

    data = {"Case_Complexity__c": "Standard", "Complexity_Detail1__c": "See Resolution Summary",
            "Product_Level_Four__c": "Security",
            "Resolution_Summary__c": summ_n_resol, "Resolution_Plan__c": summ_n_resol,
            "CSE_Comments__c": "Case Updated by CSTool"}
    sf_ins.Case.update(case_id, data)

    # the case will be updated by the user
    sf_set_status_case(sf_ins, case_number, "Closed")


def sf_get_open_cases_num(sf_ins, alias, userid):
    """ Get open cases from a user

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    alias(str): User alias
    userid(str): User ID
    """
    logging.debug("Retrieving number of open cases for " + alias)
    logging.debug("Retrieving Open cases for User " + alias)
    query_string = "SELECT Case_Number__c FROM Case WHERE OwnerId = '%s' AND  CreatedDate > %s" % (userid, time_t)
    query = sf_ins.query_all(query_string)
    return query['totalSize']


def sf_get_closed_cases_num(sf_ins, alias, userid, time_t):
    """ Get closed cases for a given user

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    alias(str): User alias
    userid(str): User ID
    """
    logging.debug("Retrieving number of closed cases for " + alias)
    query_string = "SELECT Case_Number__c FROM Case WHERE OwnerId = '%s' AND " \
                   "ClosedDate > %s" % (userid, time_t)
    query = sf_ins.query_all(query_string)
    return query['totalSize']


def list_case(sf_ins, userid):
    """ List Salesforce cases for a given user

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    userid(str): User ID
    """
    request_list = "Id, Account_Name__c, CaseNumber, Subject, OwnerId, Status, JIRA_ID__c, " \
                   "Resolution_Plan__c, Product_Level_Three__c"
    list_rq = request_list.split(',')
    case_list_query = "SELECT "
    case_list_query += request_list
    case_list_query += " FROM Case WHERE OwnerId = '%s' AND Subject LIKE " \
                       "'%%CVE%%' AND Status != 'Closed'" % userid
    case_list = sf_ins.query_all(case_list_query)

    results = [list_rq.copy()]
    for case in case_list['records']:
        items = []
        for header in list_rq:
            strip_header = header.strip()
            if strip_header == "JIRA_ID__c":
                if case[strip_header] is None:
                    items.append("No Jiras Associated")
                else:
                    jira_defects = case[strip_header].split()
                    list_of_defects = ""
                    for defect in jira_defects:
                        list_of_defects += "https://jira.wrs.com/browse/" + defect + "\n"
            elif strip_header == "Id":
                items.append(
                    "https://windriver.lightning.force.com/lightning/r/Case/"
                    + case[strip_header] + "/view")
            elif strip_header == "Resolution_Plan__c":
                if case[strip_header] is None:
                    items.append("None")
                else:
                    items.append(case[strip_header])
            else:
                items.append(case[strip_header])
        results.append(items)

    tools.dict2html(results, 'reports/sf_cases_results.html',
                    "Salesforce_Results")
    return results


def fetch(sf, number,verbose=True):

    """ Fetch a Salesforce case from ID

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str): Salesforce case ID
    """
    id = sf_case_get_id(sf, number)
    case = sf.Case.get(id)
    for key in case:
        print(key,"=", case[key])

    return 0

def sf_get_user_id(sf, alias,verbose=True):
    """ Get user ID from alias

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    alias(str): User alias
    """
    if verbose: 
        print("Retrieving User ID for " + alias)
    query_string = "SELECT Id FROM User WHERE Alias = '%s'" % alias
    query = sf.query_all(query_string)
    if query['totalSize'] == 0:
        print("User not found")
        return None
    return query['records'][0]['Id']

def sf_re_assign_case(sf,number,alias,option='auto',verbose=True):
    """ Re-assign a Salesforce case to a user

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str): Salesforce case ID
    alias(str): User alias
    """
    id = sf_case_get_id(sf, number)
    case = sf.Case.get(id)
    print("Re-assigning case " + number + " to " + alias)
    print("Old owner: " + users.sf_Contact_id2name(sf,case['OwnerId']))
    if case['CSE_Comments__c'] is None:
        case['CSE_Comments__c'] = ""
    else:
        print("Old CSE Comments: " + case['CSE_Comments__c'])
        
    OwnerId= sf_get_user_id(sf,alias)
    CSE_Comments__c = "Case has been re-assigned to " + alias + "\n" + case['CSE_Comments__c']
    if option == "accept":
        if click.confirm("Do you want to update the case?"):
            sf.Case.update(id,
                            {"CSE_Comments__c": CSE_Comments__c,
                            "Status": "On Hold",
                            "Resolution_Plan__c": "This case has been put on hold and be handled by the CSE Team and the defects will be shared on a monthly basis"})
            sf.Case.update(id,{"OwnerId": OwnerId})
            case_comment.post_comment(sf, number,
                                "The case will be handled by the team and we will  " +
                                "share all the information on a monthly basis " +
                                "please contact esteban.zunigamora@windriver.com for more information.",
                                "all")
            print("Case updated")
        else:
            print("Case not updated")
    elif option == 'auto':
        sf.Case.update(id,
                            {"CSE_Comments__c": CSE_Comments__c,
                            "Status": "On Hold",
                            "Resolution_Plan__c": "This case has been put on hold and be handled by the CSE Team and the defects will be shared on a monthly basis"})
        sf.Case.update(id,{"OwnerId": OwnerId})
        case_comment.post_comment(sf, number,
                            "The case will be handled by the team and we will  " +
                            "share all the information on a monthly basis " +
                            "please contact esteban.zunigamora@windriver.com for more information.",
                            "all")
        print("Case updated"+"\n"+"Case re-assigned to " + alias)
    return 0

def sf_set_resolution(sf_ins, number, text):
    """ Set resolution to a Salesforce case

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str): Salesforce case ID
    text(str): Resolution comment
    """
    logging.debug("Set Resolution for case number " + number)
    date_object = datetime.date.today()
    text = str(date_object) + ": " + text
    case_id = sf_case_get_id(sf_ins, number)
    if not case_id:
        tools.print_failure(
            'Could not retieve case ID for case num: ' + str(number))
        return

    sf_ins.Case.update(case_id, {
        "Resolution_Plan__c": text, "Resolution_Summary__c": text})


def associate(sf_ins, number, defect, config):
    """ Associate a case ID with a Jira ID

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str): Case ID
    defect(str): Jira ID
    config(Config): Configuration object
    """
    print("Associate the defect " + defect +
          " to case number " + number)
    case_list_query = "SELECT Id,JIRA_ID__c FROM Case WHERE CaseNumber = '%s'" % number
    case_list = sf_ins.query_all(case_list_query)

    try:
        jira_defects = [] if not case_list['records'][0]['JIRA_ID__c'] else case_list['records'][0]['JIRA_ID__c'].split()
        defects.associate(defect, case_list['records'][0]["Id"], config)
    except Exception:
        tools.print_failure('ERROR: Could not associate case: ' + str(number) +
                            ' with defect: ' + str(defect))
        return

    if defect in jira_defects:
        return
    jira_defects.append(defect)
    update_string = ' '.join([str(elem) for elem in jira_defects])
    sf_ins.Case.update(case_list['records'][0]["Id"],
                       {'JIRA_ID__c': update_string})
    print(defect + " associated with case " + number + " !")


def jiras(sf_ins, number, config):
    """ Process a new CVE

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str): Salesforce case ID
    config(Config): Configuration object
    """
    case_list_query = "SELECT Id, Account_Name__c, Subject, Description,\
                        Owner.Name, Status, JIRA_ID__c, \
                        Product_Level_Three__c, CaseNumber FROM Case WHERE \
                        CaseNumber = '%s'" % number
    case_list = sf_ins.query_all(case_list_query)
    for case in case_list['records']:
        print("---------Case----------")
        print("Case Number: " + number)
        print("Subject: " + case['Subject'])
        print("Description: " + case['Description'])
        print("Owner: " + case['Owner']['Name'])
        print("Account: " + case['Account_Name__c'])
        print("Status: " + case['Status'])
        jira_defects = []
        if case['JIRA_ID__c'] is None:
            print("No JIRAS associated!")
        else:
            print("JIRA associated:")
            jira_defects = case['JIRA_ID__c'].split()
            # For every defect in this list of defects
            for defect in jira_defects:
                print(defect)

        print("-----------------------")
        print("Possible Defects")
        print("-----------------------")
        # TODO: check exists
        linux_version = case['Product_Level_Three__c']
        # TODO: manage errors
        cve_number = re.findall("(CVE-20\d\d-\d*)", case['Subject'])[0]

        jiras_cves = defects.cve_list(cve_number, config)
        cloned_ticket = False
        for jira in jiras_cves:
            if jira["project"] == 'LIN6' or \
               jira["project"] == 'LIN8' or \
               jira["project"] == 'LIN1018' or \
               jira["project"] == 'LIN1019':

                print("- " + jira["defect"])
                print("CVE: " + jira["cve"])
                print("Summary: " + jira["summary"])
                print("Status: " + jira["status"])
                print("Resolution: " + jira["resolution"])
                print("URL: https://jira.wrs.com/browse/" + jira["defect"])
                associated = False
                for defect in jira_defects:
                    if jira["defect"] == defect:
                        print("Already associated")
                        associated = True

                if not associated and click.confirm(
                        'Do you want to associate it to the case?', default=False):
                    associate(sf_ins, case["CaseNumber"],
                              jira["defect"], config)
                    msg = '->Do you want to clone and associate this defect?'
                    if click.confirm(msg, default=False):
                        cloned_ticket = True
                        new_defect = defects.clone(sf_ins=sf_ins,
                                                   defect_id=jira["defect"],
                                                   project="LINCCM",
                                                   case_id=number,
                                                   account="cisco",
                                                   wrl_target_v=None,
                                                   config=config)
                        if not new_defect:
                            tools.print_failure(
                                "Failed to clone and associate this defect")
                            continue
                        defects.comment(
                            new_defect, case['Description'], config)
                        associate(
                            sf_ins, case["CaseNumber"], new_defect, config)
                        sf_set_resolution(
                            sf_ins, case["CaseNumber"], "Waiting for backporting by CCM")
                        print(
                            "Don't forget to modify: https://jira.wrs.com/browse/" + new_defect)
                    else:
                        msg = 'Do you want to change resolution of this case?'
                        if click.confirm(msg, default=False):
                            sf_set_resolution(sf_ins, case["CaseNumber"],
                                              "Sustaining is handling this CVE\
                                                on" + jira["defect"])
            if cloned_ticket:
                break

def GetLicenseNumber(sf,account_id):
    query = sf.query("SELECT License_Number__c FROM Case WHERE AccountId = '{}'".format(account_id))
    return query['records'][0]['License_Number__c']

def cases_per_cse(sf_ins, ialias, itype, config):
    """ List the CVEs for a specific user

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    userid(str): User alias
    itype(str):  User id type

    Returns
    -------
    bool
        True on sucess
    """
    option = 'eng:'+ialias
    a_dict = users.get_users_with_option(sf_ins,option,verbose=False)
    filename = 'cases_per_cse_'+ialias+'.html'

    if not a_dict:
        tools.print_failure('ERROR: User not found: ' + ialias)
        return False
    user_id = a_dict[0]['Id']
    user_name = a_dict[0]['Name']
    accounts_table = call_all_active_accounts(sf_ins)

    query='SELECT '
    ''' put all the fields you want here'''
    query+='AccountId,CaseNumber,Case_Age__c,Current_Status__c,Description,Green_Status__c,JIRA_ID__c,Product_Level_Three__c,Product_Level_Two__c,Subject,Type,Workload__c'
    if itype == 'all':
        query+=" FROM Case WHERE OwnerId = '{}' AND CreatedDate = THIS_YEAR".format(user_id)
    elif itype == 'open':
        query+=" FROM Case WHERE OwnerId = '{}' AND CreatedDate = THIS_YEAR AND Status !='Closed' ".format(user_id)
    elif itype == 'cve':
        query+=" FROM Case WHERE OwnerId = '{}' AND CreatedDate = THIS_YEAR AND Status !='Closed' AND Subject LIKE '%CVE-%'".format(user_id)
    elif itype == 'closed':
        query+=" FROM Case WHERE OwnerId = '{}' AND CreatedDate = THIS_YEAR AND Status ='Closed' ".format(user_id)
    else:
        tools.print_failure('ERROR: Invalid type: ' + itype)
        return False
    try : 
        case_list = sf_ins.query_all(query)
    except:
        tools.print_failure('ERROR: Invalid query: ' + query)
        print( case_list)
        return False
    if not case_list:
        tools.print_failure('ERROR: No cases found for user: ' + ialias)
        return False

    __ret_dict__ = []
    Workload__c = 0
    for case in case_list['records']:
        case['Description'] = (case['Description'][:75] + '..') if len(case['Description']) > 75 else case['Description']
        case['Subject'] = (case['Subject'][:75] + '..') if len(case['Subject']) > 75 else case['Subject']
        rr = list(filter(lambda person: person['Id'] == case['AccountId'], accounts_table))
        case['AccountId'] = rr[0]['Name'] if rr else 'None'
        Workload__c += case['Workload__c']
        __ret_dict__.append({
            'AccountName':case['AccountId'],
            'CaseNumber':case['CaseNumber'],
            'Case_Age__c':case['Case_Age__c'],
            'Current_Status__c':case['Current_Status__c'],
            'Description':case['Description'],
            'Green_Status__c':case['Green_Status__c'],
            'JIRA_ID__c':case['JIRA_ID__c'],
            'Product_Level_Three__c':case['Product_Level_Three__c'],
            'Product_Level_Two__c':case['Product_Level_Two__c'],
            'Subject':case['Subject'],
            'Type':case['Type'],
            'Workload__c':case['Workload__c']})
        
    '''dict to html'''
    if case_list['records'] :
        wklod = Workload__c/len(case_list['records'])
        wklod = round(wklod,2)
    else:
        wklod = 0
    header = '<h1> shown below the information for '+user_name+'</h1>'
    header += '<p> Current Workoad is '+str(wklod)+'</p>'
    header += '<p> Total number of cases is '+str(len(case_list['records']))+'</p>'
    header += '<br>'
    html = pd.DataFrame(__ret_dict__)
    body = html.to_html(index=False)
    with open(filename, 'w') as f:
        f.write(header)
        f.write(body)
    print('File saved: ' + filename)
    return True
       
   