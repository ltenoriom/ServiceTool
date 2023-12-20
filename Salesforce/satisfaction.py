from audioop import add
from calendar import c
import csv
import logging
from operator import is_
import os
import re
import datetime
from pickle import FALSE
import sys
from collections import Counter
import numpy as np
import pandas as pd
import smtplib
import pandas as pd
from youtube_dl import list_extractors
from Salesforce import users as sf_users
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import webbrowser
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
import requests
import csv
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go # or plotly.express as px
from getpass import getpass
from weasyprint import HTML, CSS
import json
import time
from math import nan, isnan
#from pythonreveal import *
import dataframe_image as dfi
from bs4 import BeautifulSoup
from AuthManagement.okta import OktaAuth

### dcoumentation to review just in case
### https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_dateformats.htm


from prettytable import PrettyTable

def LINE():
    return " *** line of code :{}\n".format(sys._getframe(1).f_lineno)

tbl_fmt = '''
<table border="1" bordercolor="white" class="dataframe"> {}
</table>'''

row_fmt = '''
  <tr>
    <td>{}</td>
    <td>{}</td>
  </tr>'''


def dict_to_html_table(in_dict):
    return tbl_fmt.format(''.join(row_fmt.format(k, v) for k, v in in_dict.items()))

MILESTONES_VIOLATION = {'FIRST_RESPONSE': "557G0000000XZAgIAO", "RESOLUTION_COMPLIANCE": "557G0000000XZAqIAO"}
MILESTONE_ID_TYPE_FR = '557G0000000XZAgIAO'
MILESTONE_ID_TYPE_RC = '557G0000000XZAqIAO'

REFLEKTIVE_URL = "https://www.reflektive.com"
WIND_REFLEKTIVE_URL = "http://reflektive.windriver.com"
THIRD_PARTY_TOKEN = "MvAyGxLAgdPeKEtJ7AV6" 


month = {	1:'Janauary',
		2:'February',
		3:'March',
		4:'April',
		5:'May',
		6:'June',
		7:'July',
		8:'August',
		9:'September',
		10:'October',
		11:'November',
		12:'December'		}

# Get quarter number
def get_current_quarter_number():
  today = int(datetime.datetime.now().strftime('%m'))
  if today == 1 or today == 2 or today == 3:
      quarter_number = 1
  elif today == 4 or today == 5 or today == 6:
      quarter_number = 2
  elif today == 7 or today == 8 or today == 9:
      quarter_number = 3
  elif today == 10 or today == 11 or today == 12:
      quarter_number = 4
  return quarter_number

# Python program to illustrate the intersection
# of two lists in most simple way
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


# function to return key for any value
def get_key(val):
    for key, value in MILESTONES_VIOLATION.items():
        if val == value:
            return key
    return "key doesn't exist"


def customer_information(sf_ins,account_name):
    Case_fields  = "AccountId,Case_Number__c,JIRA_ID__c,CreatedDate,Id,OwnerId,Priority,Resolution_Plan__c,Resolution_Summary__c,Status,Subject,Survey_Sent_Date__c,License_Number__c,"
    Case_fields += "Account.Name,Owner.Name,Owner.Email,Owner.Title,Owner.Alias"
    if account_name.isnumeric():
        query_string = "SELECT {} FROM Case WHERE License_Number__c  = {} AND CreatedDate = THIS_YEAR".format(Case_fields,account_name)
    else:
        query_string = "SELECT {} FROM Case WHERE Account.Name LIKE '%{}%' AND CreatedDate = THIS_YEAR".format(Case_fields,account_name)
    print(query_string)
    query = sf_ins.query_all(query_string)
    
    ## get all the cases into a pandas table 
    pd_1 = cleanup_entry(query,Case_fields)
    df_1 = pd.DataFrame.from_dict(pd_1)
    print('this is the amount of cases for account ',df_1.shape[0])
    df_survey_cases = df_1[['Case_Number__c','Id','Survey_Sent_Date__c']]
    df_survey_cases = df_survey_cases.dropna()
    #print(df_survey_cases['Id'].to_list())
    id_list = '(\'{}\')'.format('\',\''.join(df_survey_cases['Id'].to_list()))
    Case_fields = "Customer_Effort_Score__c,Customer_Satisfaction__c,Detractor__c,Id,Name,Other_Feedback__c,OwnerId,Passive__c,Promoter__c,Recommend_Raiting__c,Satisfaction_Raiting__c"
    query_string = "SELECT {} FROM Survey_Result__c WHERE Case__c  IN {}".format(Case_fields,id_list)
    query = sf_ins.query_all(query_string)
    pd_2 = cleanup_entry(query,Case_fields)
    df_2 = pd.DataFrame.from_dict(pd_2)
    print(df_2)
    nps = (df_2['Promoter__c'].sum()-df_2['Detractor__c'].sum())/(df_2['Promoter__c'].sum()+df_2['Detractor__c'].sum()+df_2['Passive__c'].sum())*100
    csat = df_2['Satisfaction_Raiting__c'].mean()*10
    ces = df_2['Customer_Effort_Score__c'].mean()

    license = df_1['License_Number__c'].unique()[0]
    print('License Number : http://ebusiness.wrs.com:8000/OA_HTML/imcSOSrchRsltsWR_old.jsp?PTYPE=License&param0={}'.format(license))
    print('Number of cases this year : {}'.format(df_1.shape[0]))
    print('nps = {}'.format(nps))
    print('csat = {}'.format(csat))
    print('ces = {}'.format(ces))

def customer_report(sf_ins,lic_number):
    """
    Returns the number of surveys sent by the user 
    sf: Salesforce connection object
    OwnerId: User ID
    time_t: Time threshold (THIS_YEAR, LAST_YEAR, THIS_YEAR,THIS_MONTH, LAST_MONTH)
    """
    #print('query the cases for the license number', account)
    try:
        Case_fields = "AccountId,Case_Number__c,JIRA_ID__c,CreatedDate,Id,OwnerId,Priority,Resolution_Plan__c,Resolution_Summary__c,Status,Subject"
        query_string = "SELECT {} FROM Case WHERE License_Number__c = '{}' AND Status != 'closed'".format(Case_fields,lic_number)
        query = sf_ins.query_all(query_string)
    except: 
        print('Error in query_string')
        return
    
    if query['totalSize'] == 0:
        print('No cases found! LINE', LINE())
        print('license number ', lic_number, ' does not exist!')
        exit()

    AccountId = query['records'][0]['AccountId']

    ''' create email body for the message'''
    today = datetime.today()
    d2 = today.strftime("%B %d, %Y")
    query_account_name = sf_ins.query_all("SELECT Name FROM Account WHERE Id = '{}'".format(AccountId))
    acc_name = query_account_name['records'][0]['Name']
    #print('acc_name', acc_name)
    email_body = '<html><body><h2>[SUBJECT] Premium Support Report Summary for Account {} in {} </h2>'.format(acc_name,d2)
    email_body = email_body.replace(query_account_name['records'][0]['Name'], '<font color="green">{}</font>'.format(query_account_name['records'][0]['Name']))
    email_body +='Hello Team, <br><br>\
        <p>Attached is the report for this week.</p>\
        <h2>Agenda</h2>\
            <p>1. Review the Open Cases</p>\
            <p>2. Review the Closed Cases</p>\
            <p>3. Review Action Items</p>\
            <p>4. Opens</p>\
        <h2>Action Items: (outside of the scope of this report)</h2>\
        <h2>Summary of the cases </h2>' 

    dict_ret = []
    for row in query['records']:
        id2name = sf_users.sf_Contact_id2name(sf_ins,row['OwnerId'])
        case_url = 'https://windriver.lightning.force.com/lightning/r/Case/{}/view'.format(row['Id'])
        html_url = '<a href="{}">{}</a>'.format(case_url, row['Case_Number__c'])
        '''truncate date string'''
        date_str = row['CreatedDate'].split('T')[0]
        if row['Status'] == 'Defect Filed':
            status = '<font color="red">{}</font>'.format('WINDRIVER ACTION')
        elif row['Status'] == 'Customer Action' or row['Status'] == 'Solution Proposed':
            status = '<font color="blue">{}</font>'.format('CUSTOMER ACTION')
        elif row['Status'] == 'Closed':
            status = '<font color="green">{}</font>'.format(row['Status'])
        else:
            status = row['Status']
        dict_ret.append({'Status': status,'Case Number': html_url,'Subject': row['Subject'],'Defects':row['JIRA_ID__c'], 'CreatedDate': date_str,'Owner': id2name,'Priority': row['Priority'],'Resolution Plan': row['Resolution_Plan__c'],'Resolution Summary': row['Resolution_Summary__c']})
    df = pd.DataFrame.from_dict(dict_ret)


    email_body += df.to_html( index=False, classes='stocktable', table_id='table1',escape=False)
    email_body = email_body.replace('class="dataframe ','class="')  # It always adds a dataframe class so this removes i
    email_body = email_body.replace('\r\n', '<br>')
    '''add background color to the table'''
    email_body = email_body.replace('<table border="1" class="dataframe">', '<table border="1" class="dataframe" style="background-color: #f2f2f2;">')
    '''add background color to string Not Affected'''
    

    email_body += '<h2>Other Topics</h2>'
    email_body += '<h2>Notes</h2>'
    email_body += '</body></html>'
    '''breaking lines on the email body'''
    
    email_body = email_body.replace('\\r\\n', '<br>')
    email_body = email_body.replace('Not Affected', '<a style="background-color:#90ee90">Not Affected</a>')
    email_body = email_body.replace('Not affected', '<a style="background-color:#90ee90">Not Affected</a>')
    email_body = email_body.replace('On Hold', '<a style="background-color:#FFFFE0">On Hold</a>')
    email_body = email_body.replace('In progress', '<a style="background-color:yellow">In progress</a>')
    email_body = email_body.replace('Fixed', '<a style="background-color:#ADD8E6">Fixed</a>')
    filename = 'reports/{}_report.html'.format(acc_name).replace(' ', '_')
    with open(filename, 'w') as f:
        f.write(email_body)
    ''' dict to html table'''
    
    print('open the file {} and send the email'.format(filename))
    return query['totalSize']

def sf_org_chart(sf,verbose=False):
    flist = "Alias,Department,Country,Email,Id,Name,Title,Manager.name,Manager.title,Manager.email,Manager.Id,Manager.Department,Manager.Country"
    #qstring = "SELECT {} FROM User WHERE Country = 'Costa Rica' AND IsActive = True AND Email LIKE '%windriver%' AND Title NOT IN ('Non-employee','Intern') ORDER BY Department ASC NULLS FIRST".format(flist)
    qstring = "SELECT {} FROM User WHERE Country = 'Costa Rica' AND IsActive = True AND Email LIKE '%windriver%' ORDER BY Department ASC NULLS FIRST".format(flist)
    
    print(qstring)
    query = sf.query_all(qstring)
    pd_users = pd.DataFrame.from_dict(query['records'])
    clean_query = cleanup_entry(query,flist)
    df_clean_query = pd.DataFrame.from_dict(clean_query)


    print('amount of employees in costa rica = ',pd_users.shape[0])
    df_clean_query.to_html('users_org.html',index=False)

    val = pd_users['Department'].value_counts()

    eng_list = ["Studio Eng Aptiv",
    "Studio Developer",
    "Studio Core",
    "Studio Testing",
    "Studio AI",
    "R&D V&V",
    "Studio Gallery",
    "Program Management Office",
    "Studio TAF",
    "Design Engineering",
    "Studio Operations"]


    finance_list = ["General Finance",
    "Sales Finance",
    "FP&A",
    "Facilities",
    "Chief Financial Officer",
    "Treasury",
    "Purchasing Cost"]


    marketing_list = ['Marketing Communications']


    people_list = ["People Team","Global Communications"]

    cso_list = ["Customer Support - Value",
    "Professional Services Cost",
    "IT Client Services",
    "Customer Support-Developer",
    "CSO Licensing",
    "Prof Services",
    "Customer Success Management Office",
    "IT Network & Ops",
    "Studio Linux Services"]
    



    eng = 0 
    cso = 0 
    mark = 0 
    finance = 0 
    people = 0 
    other = 0
    for it in val.keys():
        if it in eng_list: 
            eng +=val[it]
        elif it in cso_list:
            cso +=val[it]
        elif it in marketing_list:
            mark +=val[it]
        elif it in finance_list:
            finance +=val[it]
        elif it in people_list:
            people +=val[it]
        else:
            print(it)
            other +=val[it]
    
    print('amount of R&D ',eng)
    print('Amount of finance ',finance)
    print('Amount of people ',people)
    print('Amount of CSO ',cso)
    print('Amount of Marketing ',mark)
    print('Amount of other ',other)

    return 0 

    #### code is currently working 
    '''
    if query['totalSize'] == 0:
        print('No users found! LINE', LINE()) s
        return 0
    else:
        outdict = []
        buffer = "```mermaid\ngraph RL\n" 

        for item in query['records']:
            rr = list(filter(lambda person: person['Id'] == item['ManagerId'], users_dict))
            manager_name = rr[0]['Name'] if rr else 'None'
            rr = list(filter(lambda person: person['Id'] == item['ManagerId'], users_dict))
            manager_title = rr[0]['Title'] if rr else 'None'
            rr = list(filter(lambda person: person['Id'] == item['ManagerId'], users_dict))
            manager_email = rr[0]['Email'] if rr else 'None'
            outdict.append({'Alias': item['Alias'], 'Email': item['Email'], 'Id': item['Id'], 'ManagerId': manager_name, 'Name': item['Name'], 'Title': item['Title']})
            employee_name = "{}".format(item['Name']) ###item['Name']
            employee_title = "{}".format(item['Title'])
            employee_title = item['Title']
            buffer += '\n\t{}[{} {}] --> {}[{} {} ]'.format(item['Id'], employee_name,employee_title, item['ManagerId'], manager_name,manager_title)
            buffer.replace('Program Mgr.- ', 'PM')
        buffer += "\n```"
        with open('org_chart.md', 'w') as f:
            f.write(buffer)
    '''
def unique(list1):
 
    # insert the list to the set
    list_set = set(list1)
    # convert the set to the list
    unique_list = (list(list_set))
    return unique_list

def get_list_of_profiles(sf):
    query = "SELECT Id,Name FROM Profile"
    query = sf.query_all(query)
    dict_ = []
    for row in query['records']:
        dict_.append({'Id': row['Id'], 'Name': row['Name']})

    print('success on retrieving list of profiles')
    return dict_



def users(sf_ins, filename):
    ''' read filename line by line '''
    dict_array__ = []
    dict_profiles = get_list_of_profiles(sf_ins);
    users_dict = sf_users.get_list_of_users(sf_ins);
    list_of_emails = []
    with open(filename, 'r') as f:
        for line in f:
            # remove newline character from line
            line = line.rstrip()
            # split the line into words
            words = line.split(';')
            list_of_emails.append(words[0])
    list_of_emails = unique(list_of_emails)
    listready = '(\'{}\')'.format('\',\''.join(list_of_emails))
    dict_array__ = []
    __query__ = sf_ins.query_all("SELECT Id,Title,Name,Email,ManagerId,Department,ProfileId FROM User WHERE Email IN {} ORDER BY Department ASC NULLS FIRST ".format(listready) )
    if __query__ ['totalSize'] == 0:
        print('no users found')
        return
    else:
        for row in __query__ ['records']:
            rr = list(filter(lambda person: person['Id'] == row['ManagerId'], users_dict))
            manager_name = rr[0]['Name'] if rr else 'None'
            rr = list(filter(lambda person: person['Id'] == row['ProfileId'], dict_profiles))
            profile_name = rr[0]['Name'] if rr else 'None'   
            
            dict_array__.append({'Id': row['Id'], 'Title': row['Title'], 'Name': row['Name'], 'Email': row['Email'],'manager_name': manager_name, 'Department': row['Department'], 'profile_name': profile_name})
    ''' generate html file from dict'''
    html = pd.DataFrame.from_dict(dict_array__)
    html = html.to_html(index=False)
    html = html.replace('<table border="1" class="dataframe">', '<table class="styled-table border="1"')

    with open('users.html', 'w') as f:
        f.write(html)
    
    print('success on generating users.html')
    return True
   

def sf_get_premium_list(sf, option,verbose=False):
    '''sf_get_premium_list(sf, option,verbose=True):
    This function returns a list of premium users.
    option: 'all' or 'active'
    '''
    users_dict = sf_users.get_list_of_users(sf);

    '''query all premium cases'''
    query = "SELECT  Account.OwnerId,Account.Id,Account.Status__c,Account.Geo_Location__c,Account.Name,"\
        "Id,License_Number__c,Case_Number__c,AccountId,Product_Level_Two__c,Product_Level_Three__c"\
    " FROM Case WHERE (CreatedDate = THIS_YEAR OR Resolved_Date__c = THIS_YEAR) AND Coverage_Type__c = 'Premium' AND Account.Status__c = 'Active' ORDER BY License_Number__c ASC NULLS FIRST " 
    ret = sf.query_all(query)

    orddict = []
    for row in ret['records']:
        orddict.append({'AccountId': row['AccountId'], 'CaseId': row['Id'],'CaseNumber':row['Case_Number__c'], 'License_Number__c': row['License_Number__c'], 'Product_Level_Two__c': row['Product_Level_Two__c'], 'Product_Level_Three__c': row['Product_Level_Three__c'],'Geo_Location__c': row['Account']['Geo_Location__c'],'Name': row['Account']['Name'],'OwnerId': row['Account']['OwnerId']})

    ''' print the length of the premium case list'''
    if verbose:
        print('length of premium case list: {}'.format(len(orddict)))

    '''get unique list of License_Number__c'''
    list_of_licenses = []
    for row in orddict:
        dict___ = row['License_Number__c']
        if dict___ in list_of_licenses:
            continue
        else:
            list_of_licenses.append(dict___)

    list_of_licenses.sort()
    
    '''get the number of cases per license'''
    cases_per_lic = {}
    for row in orddict:
      for lic in list_of_licenses:
        if lic == row['License_Number__c']:
            if lic in cases_per_lic:
                cases_per_lic[lic] += 1
            else:
                cases_per_lic[lic] = 1

    ''' get unique name per licenses'''
    unique_name_per_lic = {}
    for row in orddict:
        for lic in list_of_licenses:
            if lic == row['License_Number__c']:
                unique_name_per_lic[lic] = row['Name']
            else:
                continue
    
    unique_product_per_lic = {}
    for row in orddict:
        for lic in list_of_licenses:
            if lic == row['License_Number__c']:
                unique_product_per_lic[lic] = row['Product_Level_Two__c']
            else:
                continue
    
    unique_id_per_lic = {}
    for row in orddict:
        for lic in list_of_licenses:
            if lic == row['License_Number__c']:
                unique_id_per_lic[lic] = row['AccountId']
            else:
                continue

    unique_version_per_lic = {}
    for row in orddict:
        for lic in list_of_licenses:
            if lic == row['License_Number__c']:
                unique_version_per_lic[lic] = row['Product_Level_Three__c']
            else:
                continue

    unique_geo_per_lic = {}
    for row in orddict:
        for lic in list_of_licenses:
            if lic == row['License_Number__c']:
                unique_geo_per_lic[lic] = row['Geo_Location__c']
            else:
                continue

    unique_owner_per_lic = {}
    for row in orddict:
        for lic in list_of_licenses:
            if lic == row['License_Number__c']:
                rr = list(filter(lambda person: person['Id'] == row['OwnerId'], users_dict))
                owner_name = rr[0]['Name'] if rr else 'None'
                unique_owner_per_lic[lic] = owner_name  ##row['OwnerId']
            else:
                continue

    ''' ordered dict of licenses and number of cases'''
    ordered_licenses = []
    
    for lic in list_of_licenses:
        url_account = "https://windriver.lightning.force.com/lightning/r/Account/{}/view".format(unique_id_per_lic[lic])
        oracle_lic_url = url = "http://ebusiness.wrs.com:8000/OA_HTML/imcSOSrchRsltsWR_old.jsp?PTYPE=License&param0={}".format(lic) 
        html_url = '<a href="{}">{}</a>'.format(url_account, unique_name_per_lic[lic])
        oracle_lic = '<a href="{}">{}</a>'.format(oracle_lic_url, lic)
        ordered_licenses.append({'License_Number__c': oracle_lic, 'Number_of_Cases': cases_per_lic[lic], 'Name': html_url, 'Product_Level_Two__c': unique_product_per_lic[lic], 'Product_Level_Three__c': unique_version_per_lic[lic], 'Geo_Location__c': unique_geo_per_lic[lic], 'OwnerName': unique_owner_per_lic[lic]})
    
    '''clean html'''
    buf = "<h1>Premium Users</h1>"
    buf = buf + "<p> Shown below is the information for the premium users. That have open or resolved cased during 2022</p>"
    html = pd.DataFrame.from_dict(ordered_licenses)
    html = html.to_html(index=False, classes='stocktable', table_id='table1',escape=False)
    with open('reports/ordered_licenses.html', 'w') as f:
        f.write(buf+html)
            
    if verbose:
        print("length of unique list of licenses: {}".format(len(list_of_licenses)))
        print('unique name per license: {}'.format(len(unique_name_per_lic)))
    


    html = pd.DataFrame.from_dict(orddict)
    html = html.to_html(index=False)
    with open('super_directory.html', 'w') as f:
        f.write(html)

    return True

def process_users_(sf,option,verbose=False):
    """ this function is used to get the performance of the reviews
    :param sf: sf connection
    :param option: option can be all, linux_na, eng:<ALIAS>
    :param time_t: time_t is the time in the format of (THIS_YEAR,THIS_QUARTER,THIS_MONTH,LAST_MONTH,LAST_QUARTER,LAST_YEAR,LAST_N_DAYS:<N>)'
    :return:
    """
    dict_user__ = sf_users.get_list_of_users(sf)
    __ord_dict_user__ = []
    if "eng" in option:
        if verbose:
            print('select only for one user: {}'.format(option))
        for user in dict_user__:
            if user['Alias'] == option.split(":")[1]:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
    elif "liclx" in option:
        rr = list(filter(lambda person: person['Alias'] == "ezunigam", dict_user__))
        manager_id = rr[0]['Id']
        for user in dict_user__:
            if user['ManagerId'] == manager_id:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
                if verbose:
                    print('{}'.format(user['Name']))
            elif "aelmahra" == user['Alias'] or "rpadmana" == user['Alias']:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
                if verbose:
                    print('{}'.format(user['Name']))
            else:
                pass
    elif "nalinux" in option:
        list_of_engineers = ["aelmahra","dmorales","erivera","mmontero","csolano","jortegac"]
        #list_of_engineers = ['mcaamano',"dmorales","erivera","mmontero","csolano","jortegac","ltenorio","erojasag","mwilliam","jlopez","rpadmana"]
        for user in dict_user__:
            if user['Alias'] in list_of_engineers:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
                if verbose:
                    print('{}'.format(user['Name']))
            else:
                pass
    elif "man" in option:
        if verbose:
            print('select for multiple users and one manager')

        ''' get the id from the the manager'''
        rr = list(filter(lambda person: person['Alias'] == option.split(":")[1], dict_user__))
        manager_id = rr[0]['Id']
        for user in dict_user__:
            if user['ManagerId'] == manager_id:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
    elif "cso" == option:
        ### Department LIKE '%Support%' OR Department LIKE '%Licensing%' OR Department LIKE '%CSO%'
        for user in dict_user__:
            if user['Department'] is not None and ("Support" in user['Department'] or "Licensing" in user['Department'] or "CSO" in user['Department']) and "CSP" not in user['Department']:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['ALias']})
    elif "costarica" in option:
        ### Department LIKE '%Costa Rica%'
        for user in dict_user__:
            if (user['Department'] is not None and user['Country'] is not None) and "Costa Rica" in user['Country']:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
    elif "nacoreip" in option:
        ### Department LIKE '%Licensing%'
        for user in dict_user__:
            eng_list = ["DOrdonez","ncutaia","ELo","amorse","jcruz","mzhang","nkecske","dchang","jli9","pmertens","dgarbanz"]
            if user['Alias'] in eng_list:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
    
    elif "lic" in option:
        ### Department LIKE '%Licensing%'
        for user in dict_user__:
            eng_list = ["RPadmana","ltenorio","erojasag","mwilliam","jlopez"]
            if user['Alias'] in eng_list:
                __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
    elif "na" in option:
        ### Department LIKE '%Costa Rica%'
        for user in dict_user__:
            if user['Department'] is not None and ("Support" in user['Department'] or "Licensing" in user['Department'] or "Customer" in user['Department'] or "CSO" in user['Department']) and "CSP" not in user['Department']:
                if (user['Department'] is not None and user['Country'] is not None) and ("Costa Rica" == user['Country'] or "United States" == user['Country'] or "Canada" == user['Country']):
                    __ord_dict_user__.append({'Id': user['Id'], 'Name': user['Name'],"Title":user['Title'],"Alias":user['Alias']})
    else: 
        __ord_dict_user__ = dict_user__
    
    return __ord_dict_user__

def sf_review_performance(sf, option, time_t,verbose=False):

    __ord_dict_user__  = option
    #print(__ord_dict_user__)
    list_of_users_to_process = pd.DataFrame.from_dict(__ord_dict_user__)['Id'].tolist()
    #print(list_of_users_to_process)
    pd_ordlist = pd.DataFrame.from_dict(__ord_dict_user__)
    ownerid_list = '(\'{}\')'.format('\',\''.join(row['Id'] for row in __ord_dict_user__))
    
    ''' get open cases '''
    cases_fields  = "Id,AccountId,OwnerId,Subject,Case_Complexity__c,Complexity_Detail1__c,Product_Level_Three__c,Root_Cause__c,Case_Number__c,SLA_Overrun__c,CreatedDate,Survey_Sent_Date__c,Resolved_Date__c,Account.Name,Owner.Name,Owner.Email,Owner.Title,Owner.Alias"
    survey_fields = "Id,OwnerId,Other_Feedback__c,Satisfaction_Raiting__c,Recommend_Raiting__c,Customer_Effort_Score__c,Promoter__c,Detractor__c,Passive__c,CreatedDate"
    chat_fields   = "WaitTime,Status,ChatDuration,OwnerId,CreatedDate"
    violation_fields = "CaseId,CreatedDate"

    qOpen = sf.query_all("SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}".format(cases_fields,ownerid_list, time_t))
    qResolved = sf.query_all("SELECT {} FROM Case WHERE OwnerId IN {} AND Resolved_Date__c = {}".format(cases_fields,ownerid_list, time_t))
    qSurv = sf.query_all("SELECT {} FROM Survey_Result__c WHERE  OwnerId IN {} AND CreatedDate = {}".format(survey_fields,ownerid_list,time_t))
    qViol = sf.query_all("SELECT {} FROM CaseMilestone WHERE CreatedDate = {} AND MilestoneTypeId = '557G0000000XZAgIAO' AND IsViolated = true".format(violation_fields,time_t,))
    qChatR = sf.query_all("SELECT {} FROM LiveChatTranscript WHERE (Status = 'Missed' OR Status = 'Completed') AND CreatedDate = {}".format(chat_fields,time_t))


    qOpen_cl = cleanup_entry(qOpen,cases_fields)
    qResolved = cleanup_entry(qResolved,cases_fields)
    qChatR = cleanup_entry(qChatR,chat_fields)
    qSurv = cleanup_entry(qSurv,survey_fields)
    qViol = cleanup_entry(qViol,violation_fields)
    
    df_qOpen_cl = pd.DataFrame.from_dict(qOpen_cl)
    df_qResolved = pd.DataFrame.from_dict(qResolved)
    df_qChatR = pd.DataFrame.from_dict(qChatR)
    df_qSurv = pd.DataFrame.from_dict(qSurv)
    df_qViol = pd.DataFrame.from_dict(qViol)
   
    op_cases_cve     = extract_vulnerability_dict(df_qOpen_cl,list_of_users_to_process)
    op_cases_not_cve = extract_cases(df_qOpen_cl,list_of_users_to_process)
    cl_cases_cve     = extract_vulnerability_dict(df_qResolved,list_of_users_to_process)
    cl_cases_not_cve = extract_cases(df_qResolved,list_of_users_to_process)
   
    chat_values = get_chat_value(df_qChatR,list_of_users_to_process) 
    violations  = SLA_Overrun_Analysis_Resolution_Compliance(df_qResolved,list_of_users_to_process,option,time_t)
    pd_kpis     = Get_KPIs_From_dict(sf,df_qSurv,list_of_users_to_process)

    fr_violation = get_first_response_compliance(df_qOpen_cl,df_qViol,list_of_users_to_process)
    
    
    # Opening JSON file
    with open('docs/na_additional_actitivities.json', 'r') as openfile:
        additional_activities = json.load(openfile)
    
    with open('docs/na_capacity.json', 'r') as openfile:
        capacity_dict_by_name = json.load(openfile)

    out_frame = []
    for user in list_of_users_to_process:
        __row__ = {}
        df = pd_kpis[pd_kpis['Id']==user]
        df_chat = chat_values[chat_values['OwnerId']==user]
        df_data = df_qOpen_cl[df_qOpen_cl['OwnerId']==user]
        surveys_sent = df_data['Survey_Sent_Date__c']
        surveys_sent = surveys_sent.mask(surveys_sent.eq('None')).dropna()   
        user_list001 = pd_ordlist[pd_ordlist['Id']==user]
        __row__["Name"] = user_list001['Name'].item()
        __row__["Title"] = user_list001['Title'].item()
        __row__['Capacity'] =  capacity_dict_by_name[__row__["Name"]] if __row__["Name"] in capacity_dict_by_name else capacity_dict_by_name['Other']
        __row__["Open Cases"] = op_cases_not_cve[user]+op_cases_cve[user]
        __row__["Closed Cases"] = cl_cases_not_cve[user]
        __row__["Resolved Cases %"] = int(__row__["Closed Cases"]/(__row__["Open Cases"])*100) if __row__["Open Cases"] else 0 
        __row__["Open CVE"] = op_cases_cve[user]
        __row__["Closed CVE"] = cl_cases_cve[user]
        __row__["Resolved CVE %"] = int(__row__["Closed CVE"]/(__row__["Open CVE"])*100) if __row__["Open CVE"] > 0 else 0
        __row__["First Compliance Resolution %"] = int((100 - fr_violation[user] / (op_cases_not_cve[user])*100)) if op_cases_not_cve[user] > 0 else 0
        __row__["Resolution Compliance"] = violations[user]
        __row__["Survey Sent"] = len(surveys_sent)
        __row__["Survey Received"] = df['Survey_received'].item()
        __row__["Survey Rate"] = int(__row__["Survey Received"]/(__row__["Survey Sent"])*100) if __row__["Survey Sent"] > 0 else 0
        __row__["NPS"] = df['NPS'].item()
        __row__["CSAT"] = df['CSAT'].item()
        __row__["CES"] = df['CES'].item()
        __row__["TopBox"] = df['Topbox'].item()
        __row__["WaitTime"] = df_chat['WaitTime'].item()
        __row__["ChatDuration"] = df_chat['ChatDuration'].item()
        __row__["ChatRate"] = df_chat['ChatRate'].item()
        __row__['Additional Activities'] = additional_activities[__row__["Name"]][0] if __row__["Name"] in additional_activities else additional_activities['Other']
        __row__['% Additional Activities'] = additional_activities[__row__["Name"]][1] if __row__["Name"] in additional_activities else additional_activities['Other']


        out_frame.append(__row__)

    pd0 = pd.DataFrame.from_dict(out_frame)

    ''' get totals from each row in the pd frame '''
    __sum_row__ = {}
    __sum_row__["Name"] = "Total"
    __sum_row__["Title"] = "Total"
    __sum_row__['Capacity'] =pd0['Capacity'].sum()
    __sum_row__["Open Cases"] = pd0['Open Cases'].sum()
    __sum_row__["Closed Cases"] = pd0['Closed Cases'].sum()
    __sum_row__["Resolved Cases %"] = pd0["Resolved Cases %"].replace(0, np.NaN).mean()
    __sum_row__["Open CVE"] = pd0['Open CVE'].sum()
    __sum_row__["Closed CVE"] = pd0['Closed CVE'].sum()
    __sum_row__["Resolved CVE %"] = pd0['Resolved CVE %'].replace(0, np.NaN).mean()
    __sum_row__["First Compliance Resolution %"] =pd0['First Compliance Resolution %'].replace(0, np.NaN).mean()
    __sum_row__["Resolution Compliance"] = pd0['Resolution Compliance'].replace(0, np.NaN).mean()
    __sum_row__["Survey Sent"] = pd0["Survey Sent"].sum()
    __sum_row__["Survey Received"] = pd0["Survey Received"].sum()
    __sum_row__["Survey Rate"] = pd0["Survey Rate"].replace(0, np.NaN).mean()
    __sum_row__["NPS"] = pd0['NPS'].replace(0, np.NaN).mean()
    __sum_row__["CSAT"] = pd0["CSAT"].replace(0, np.NaN).mean()
    __sum_row__["CES"] = pd0['CES'].replace(0, np.NaN).mean()
    __sum_row__["TopBox"] = pd0['TopBox'].sum()
    __sum_row__["WaitTime"] = pd0['WaitTime'].replace(0, np.NaN).mean()
    __sum_row__["ChatDuration"] = pd0['ChatDuration'].replace(0, np.NaN).mean()
    __sum_row__["ChatRate"] = pd0['ChatRate'].replace(0, np.NaN).mean()
    __sum_row__['Additional Activities'] = "Total"

    df_totals = pd.DataFrame(__sum_row__, index=[0]).round(0)
    pd0 = pd0.append(df_totals)
 
    page_title_text = 'Team Report for {}'.format(time_t)
    title_text = 'Team Performance Review for {}'.format(time_t)
    text = 'The information has been extracted from salesforse database on day <b>{}</b><br><br>'.format(datetime.datetime.now())
    html = f'''
        <html>
            <head>
                <title>{page_title_text}</title>
                <link rel="stylesheet" href="css/style.css">
            </head>
            <body>
                <h1>{title_text}</h1>
                <p>{text}</p>
                {pd0.to_html(index=False)}
            </body>
        </html>
        '''
    
    html = html.replace('<table border="1" class="dataframe">', '<table class="styled-table border="1"')
    filename__ = "reports/perf_report_{}.html".format(time_t).lower().replace(':','_')
    with open(filename__, 'w') as f:
        f.write(html)
    print('Review the report file :',filename__ )

    return pd0
    
def Get_Complexity_analysis(stream,verbose=False):
    Case_Complexity__c = pd.DataFrame(stream['Case_Complexity__c'].value_counts(dropna = False)).sort_index().to_dict()['Case_Complexity__c']
    Root_Cause__c = pd.DataFrame(stream['Root_Cause__c'].value_counts(dropna = False)).sort_index().to_dict()['Root_Cause__c']
    Prod_Info__c = pd.DataFrame(stream['Product_Level_Two__c'].value_counts(dropna = False)).sort_index().to_dict()['Product_Level_Two__c']
    Product_type = pd.DataFrame(stream['Product_Level_Three__c'].value_counts(dropna = False)).sort_index().to_dict()['Product_Level_Three__c']

    if verbose:
        print(Case_Complexity__c)
        print(Root_Cause__c)
        print(Product_type)
    
    return Case_Complexity__c,Root_Cause__c,Product_type,Prod_Info__c
    

def Get_KPIs_From_dict(sf,stream,list_of_users,verbose=False):
    """
    Returns a list of KPIs from a stream
    :param stream:
    :param list_of_users:
    :param verbose:
    :return:
    """
    df_cp = stream.copy()
    list_of_owners_count = df_cp['OwnerId'].value_counts()
    out_stream = []
    TopBox__c = calculate_topbox_per_user(sf,list_of_users)


    for user in list_of_users:
        _o_dict_ = {}
        if user in list_of_owners_count.index.to_list():
            df_cp = stream.copy()
            df_cp = df_cp[df_cp['OwnerId'] == user]
            df_cp_nps = df_cp[df_cp['Recommend_Raiting__c'].notna()]
            Survey_received = len(df_cp['OwnerId'].index)
            Promoter__c = df_cp_nps['Promoter__c'].sum()
            Detractor__c = df_cp_nps['Detractor__c'].sum()
            Passive__c = df_cp_nps['Passive__c'].sum()
            Satisfaction_Raiting__c = df_cp['Satisfaction_Raiting__c'].mean()
            Customer_Effort_Score__c = df_cp['Customer_Effort_Score__c'].mean()
            denom = Promoter__c + Detractor__c +Passive__c if (Promoter__c + Detractor__c +Passive__c)>0 else 1 
            NPS = int((Promoter__c - Detractor__c)/(denom)*100)
            CSAT = int(Satisfaction_Raiting__c *10) if Satisfaction_Raiting__c > 0 else 0 
            CES = round(Customer_Effort_Score__c,1)
            if user in TopBox__c:
                _o_dict_ = {'Id':user,'Survey_received':Survey_received,'NPS':NPS,'CSAT':CSAT,'CES':CES,'Topbox':TopBox__c[user]}
            else: 
                _o_dict_ = {'Id':user,'Survey_received':Survey_received,'NPS':NPS,'CSAT':CSAT,'CES':CES,'Topbox':0}
        else:
            _o_dict_ = {'Id':user,'Survey_received':0,'NPS':0,'CSAT':0,'CES':0,'Topbox':0}
        
        out_stream.append(_o_dict_)

    if verbose:
        print("kpis: ")
        print(json.dumps(out_stream, sort_keys=False, indent=4))
    return (pd.DataFrame.from_dict(out_stream))  
    
def get_first_response_compliance(cOpen,cViolation,list_of_users,verbose=False):
    df_cp = cOpen.copy()
    df2_cp = cViolation.copy()
    list_of_owners_count = df_cp['OwnerId'].value_counts()
    return_array = {}
    for user in list_of_users:
        if user in list_of_owners_count.index.to_list():
            df_cp = df_cp[df_cp['OwnerId']== user]
            list_of_cases = df_cp['Id'].to_list()
            list_of_viol = df2_cp['CaseId'].to_list()
            list_of_violated_cases = intersection(list_of_cases,list_of_viol)
            return_array[user]  = len(list_of_violated_cases)
        else:
            return_array[user] = 0
    if verbose:
        print("first_response_compliance: ")
        print(json.dumps(return_array, sort_keys=False, indent=4))
    return return_array

def SLA_Overrun_Analysis_Resolution_Compliance(stream,list_of_users,option,time_t,verbose=False):
    """
    Get the number of violations in the stream
    :param stream:
    :param list_of_users:
    :return:
    """
    ''' get only cases not cve '''

    _o_dict_ = {}
    for user in list_of_users:
        df_non_violation = stream.copy()
        df_all = stream.copy()
        
        df_non_violation = df_non_violation[df_non_violation['OwnerId']==user]
        df_non_violation = df_non_violation[df_non_violation['SLA_Overrun__c']<=0]
        df_all = df_all[df_all['OwnerId']==user]
        violation_per = round(df_non_violation.shape[0]/df_all.shape[0]*100,1) if df_all.shape[0]>0 else 0 
        if verbose:
            print('[{}] Non Violation {} , all resolved cases {} violation percentage {} %'.format(user,df_non_violation.shape[0],df_all.shape[0],violation_per))
        _o_dict_[user] = violation_per

    if verbose:
        df_all = stream.copy()
        df_all = df_all[df_all['SLA_Overrun__c']>0]
        filen = 'reports/violations_{}_{}.txt'.format(option,time_t)
        with open(filen, 'w') as f:
            index = 0 
            for ind in df_all.index:
                index = index + 1
                buffer = "{} [{}] Case Link https://windriver.lightning.force.com/lightning/r/Case/{}/view\n".format(index, df_all['OwnerId'][ind],df_all['Id'][ind])
                f.write(buffer)


    return _o_dict_
   

def get_chat_value(stream,list_of_users):
    """
    Get the value of a chat
    :param list_of_users:
    :return:
    """
    df_cp = stream.copy()
    Vulnerability_count = df_cp['OwnerId'].value_counts()
    output = pd.DataFrame(columns=['OwnerId', 'ChatDuration','WaitTime','Missed','Completed','ChatRate'])
    __ordict__ = []
    for user in list_of_users:
        df_out = {}
        if user in Vulnerability_count.index.to_list():
            df_cp = stream.copy()
            df_cp = df_cp[df_cp['OwnerId'] == user] 
            df_out['OwnerId'] = user
            df_cd =df_cp['ChatDuration'].fillna(0).mean()
            #print('this is the value for :df_cd ',int(df_cd))
            df_out['ChatDuration'] = int(df_cd/60)
            df_out['WaitTime'] = int(df_cp['WaitTime'].fillna(0).mean())
            df_out['Missed'] = df_cp[df_cp['Status'] == 'Missed'].shape[0]
            df_out['Completed'] = df_cp[df_cp['Status'] == 'Completed'].shape[0]
            df_out['ChatRate'] = int(df_out['Completed'] / (df_out['Completed'] + df_out['Missed'])*100)
        else:
            df_out['OwnerId'] = user
            df_out['ChatDuration'] = 0
            df_out['WaitTime'] = 0
            df_out['Missed'] = 0
            df_out['Completed'] = 0
            df_out['ChatRate'] = 0
        __ordict__.append(df_out)
    
    output = pd.DataFrame.from_dict(__ordict__)
    
    return (output)



def extract_cases(entry,list_of_users,verbose=False):
    ''' get only cases not cve '''
    df_cp = entry.copy()
    df_cp = df_cp[~(df_cp['Root_Cause__c'] == 'Vulnerability')]
   
    Vulnerability_count = df_cp['OwnerId'].value_counts()
    '''get access to values '''
    dict_vulnerability_count = {}
    for user in list_of_users:
        if user in Vulnerability_count.index.to_list():
            dict_vulnerability_count[user] = Vulnerability_count[user]
        else:
            dict_vulnerability_count[user] = 0
    
    if verbose:
        print("Cases: ",dict_vulnerability_count)
    return (dict_vulnerability_count)


def extract_vulnerability_dict(entry,list_of_users,verbose=False):
    ''' get only cases not cve '''
    df_cp = entry.copy()
    df_cp = df_cp[(df_cp['Root_Cause__c'] == 'Vulnerability')]
    Vulnerability_count = df_cp['OwnerId'].value_counts()
    '''get access to values '''
    dict_vulnerability_count = {}
    for user in list_of_users:
        if user in Vulnerability_count.index.to_list():
            dict_vulnerability_count[user] = Vulnerability_count[user]
        else:
            dict_vulnerability_count[user] = 0
    
    if verbose:
        print("CVE: ",dict_vulnerability_count)
    return (dict_vulnerability_count)

def cleanup_entry(entry,cases_fields):
    
    clean_entry = []
    for record in entry['records']:
        row = {}
        for item in cases_fields.split(','):
            if '.' in item:
                expr = item.replace('.', '')
                fields = item.split('.')
                
                if record[fields[0]]:
                    print(fields[0],fields[1])
                    print(record[fields[0]])
                    f1 =  fields[1][0].upper() + fields[1][1:]
                    row[expr] = record[fields[0]][f1]
                else:
                    row[expr] = None
            else:
                row[item] = record[item]
        clean_entry.append(row)
               
    return clean_entry

def question(string_i):
    i = 0
    while i < 2:
        answer = input("{} (yes or no)".format(string_i))
        if any(answer.lower() == f for f in ["yes", 'y', '1', 'ye']):
            print("Continue...")
            return True
        elif any(answer.lower() == f for f in ['no', 'n', '0']):
            print("Skip")
            return False
        else:
            i += 1
            if i < 2:
                print('Please enter yes or no')
            else:
                print("Nothing done")
                exit()

def calculate_kpis_per_bundle(data,timeframe,verbose=False):
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
    
    if verbose:
        print('NPS on period {} = {} '.format(timeframe,nps))
        print('CSAT on period {} = {} '.format(timeframe,csat))
        print('CES on period {} = {} '.format(timeframe,ces))

    return {'NPS':nps,'CSAT':csat,'CES':ces}


def NPS_gauge_comp(text,curr_data,comp_data):
    fig = go.Figure(go.Indicator(
    domain = {'x': [0, 1], 'y': [0, 1]},
    value = curr_data,
    mode = "gauge+number+delta",
    title = {'text':text},
    delta = {'reference': comp_data},
    gauge = {'axis': {'range': [-100, 100]},
             'steps' : [
                 {'range': [0, 47], 'color': "#A3DAD6"},
                 {'range': [47, 100], 'color': "#00ADA4"}],
             'threshold' : {'line': {'color': "#8473AD", 'width': 4}, 'thickness': 1, 'value': 60}}))
    return fig

def CSAT_gauge_comp(text,curr_data,comp_data):
    fig = go.Figure(go.Indicator(
    domain = {'x': [0, 1], 'y': [0, 1]},
    value = curr_data,
    mode = "gauge+number+delta",
    title = {'text':text},
    delta = {'reference': comp_data},
    gauge = {'axis': {'range': [0, 100]},
             'steps' : [
                 {'range': [0, 80], 'color': "#A3DAD6"},
                 {'range': [80, 100], 'color': "#00ADA4"}],
             'threshold' : {'line': {'color': "#8473AD", 'width': 4}, 'thickness': 1, 'value': 92}}))
    return fig

def CES_gauge_comp(text,curr_data,comp_data):
    curr_data = -curr_data
    comp_data = -comp_data
    fig = go.Figure(go.Indicator(
    domain = {'x': [0, 1], 'y': [0, 1]},
    value = curr_data,
    mode = "gauge+number+delta",
    title = {'text':text},
    delta = {'reference': comp_data},
    gauge = {'axis': {'range': [-7, 0]},
             'steps' : [
                 {'range': [-7, 0], 'color': "#A3DAD6"},
                 {'range': [0, -1.8], 'color': "#00ADA4"}],
             'threshold' : {'line': {'color': "#8473AD", 'width': 4}, 'thickness': 1, 'value': -2}}))
    return fig

def sf_nps(sf_ins):
    ''' get all the data from survey_result_c '''
    fields = "Recommend_Raiting__c,Satisfaction_Raiting__c,Promoter__c,Detractor__c,Passive__c,Customer_Effort_Score__c"
    SR_LAST_3_YEARS = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = LAST_N_YEARS:3".format(fields))
    SR_LAST_2_YEARS = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = LAST_N_YEARS:2".format(fields))
    SR_THIS_YEAR = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = THIS_YEAR".format(fields))
    SR_LAST_YEAR = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = LAST_YEAR".format(fields))
    SR_LAST_QUARTER = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = LAST_QUARTER".format(fields))
    SR_THIS_QUARTER = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = THIS_QUARTER".format(fields))
    SR_LAST_2_QUARTERS = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = N_QUARTERS_AGO:2".format(fields))
    SR_LAST_3_QUARTERS = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = N_QUARTERS_AGO:3".format(fields))

    this_year = calculate_kpis_per_bundle(SR_THIS_YEAR['records'],'THIS_YEAR')     
    last_year = calculate_kpis_per_bundle(SR_LAST_YEAR['records'],'LAST_YEAR')   
    last_2_year = calculate_kpis_per_bundle(SR_LAST_2_YEARS['records'],'LAST_2_YEAR')
    last_3_year = calculate_kpis_per_bundle(SR_LAST_3_YEARS['records'],'LAST_3_YEAR')
    this_quarter = calculate_kpis_per_bundle(SR_THIS_QUARTER['records'],'THIS_QUARTER') 
    last_quarter = calculate_kpis_per_bundle(SR_LAST_QUARTER['records'],'LAST_QUARTER')   
    last_2_quarters = calculate_kpis_per_bundle(SR_LAST_2_QUARTERS['records'],'N_QUARTERS_AGO:2')   
    last_3_quarters = calculate_kpis_per_bundle(SR_LAST_3_QUARTERS['records'],'N_QUARTERS_AGO:3')   

    CSAT_YEAR_TABLE = go.Figure(data=[go.Table(header=dict(values=['TimeFrame', 'CSAT Score']),
                 cells=dict(values=[['THIS YEAR', 'LAST YEAR', 'LAST 2 YEAR', 'LAST 3 YEARS'], 
                 [this_year['CSAT'], last_year['CSAT'], last_2_year['CSAT'],last_3_year['CSAT']]]))
                     ])

    CES_YEAR_TABLE = go.Figure(data=[go.Table(header=dict(values=['TimeFrame', 'CES Score']),
                    cells=dict(values=[['THIS YEAR', 'LAST YEAR', 'LAST 2 YEAR', 'LAST 3 YEARS'], 
                    [this_year['CES'], last_year['CES'], last_2_year['CES'],last_3_year['CES']]]))
                    ])
    
    NPS_YEAR_TABLE = go.Figure(data=[go.Table(header=dict(values=['TimeFrame', 'NPS Score']),
                 cells=dict(values=[['THIS YEAR', 'LAST YEAR', 'LAST 2 YEAR', 'LAST 3 YEARS'], 
                 [this_year['NPS'], last_year['NPS'], last_2_year['NPS'],last_3_year['NPS']]]))
                     ])
    
    CSAT_QUARTER_TABLE = go.Figure(data=[go.Table(header=dict(values=['TimeFrame', 'CSAT Score']),
                 cells=dict(values=[['THIS QUARTER', 'LAST QUARTER', 'LAST 2 QUARTERS','LAST 3 QUARTERS' ], 
                 [this_quarter['CSAT'], last_quarter['CSAT'], last_2_quarters['CSAT'],last_3_quarters['CSAT']]]))
                     ])

    NPS_QUARTER_TABLE = go.Figure(data=[go.Table(header=dict(values=['TimeFrame', 'NPS Score']),
                 cells=dict(values=[['THIS QUARTER', 'LAST QUARTER', 'LAST 2 QUARTERS','LAST 3 QUARTERS' ], 
                 [this_quarter['NPS'], last_quarter['NPS'], last_2_quarters['NPS'],last_3_quarters['NPS']]]))
                     ])
    
    CES_QUARTER_TABLE = go.Figure(data=[go.Table(header=dict(values=['TimeFrame', 'CES Score']),
                    cells=dict(values=[['THIS QUARTER', 'LAST QUARTER', 'LAST 2 QUARTERS','LAST 3 QUARTERS' ], 
                    [this_quarter['CES'], last_quarter['CES'], last_2_quarters['CES'],last_3_quarters['CES']]]))
                    ])

    
    
    _text_ =  "NPS value this year({}) , compared with last year ({})".format(this_year['NPS'],last_year['NPS'])
    fig0 = NPS_gauge_comp(_text_,this_year['NPS'],last_year['NPS'])
    _text_ =  "NPS value this Q({}) , compared with last Q ({})".format(this_quarter['NPS'],last_quarter['NPS'])
    fig1 = NPS_gauge_comp(_text_,this_quarter['NPS'],last_quarter['NPS'])

    _text_ =  "CSAT value this year({}) , compared with last year ({})".format(this_year['CSAT'],last_year['CSAT'])
    fig2 = CSAT_gauge_comp(_text_,this_year['CSAT'],last_year['CSAT'])
    _text_ =  "CSAT value this Q({}) , compared with last Q ({})".format(this_quarter['CSAT'],last_quarter['CSAT'])
    fig3 = CSAT_gauge_comp(_text_,this_quarter['CSAT'],last_quarter['CSAT'])

    _text_ =  "CES value this year({}) , compared with last year ({})".format(this_year['CES'],last_year['CES'])
    fig4 = CES_gauge_comp(_text_,this_year['CES'],last_year['CES'])
    _text_ =  "CES value this Q({}) , compared with last Q ({})".format(this_quarter['CES'],last_quarter['CES'])
    fig5 = CES_gauge_comp(_text_,this_quarter['CES'],last_quarter['CES'])

    

    app = dash.Dash()
    app.layout = html.Div([
        html.H1(children='NPS,CSAT,CES for the last 3 years'),
        html.H2(children='NPS Comparison Tables'),
        html.Div(children=[
            dcc.Graph(figure=NPS_YEAR_TABLE,id="graphNPS1", style={'display': 'inline-block'}),
            dcc.Graph(figure=NPS_QUARTER_TABLE,id="graphNPS2", style={'display': 'inline-block'}),
        ], style={'display': 'inline-block'}),
        html.H2(children='CSAT Comparison Tables'),
        html.Div(children=[
            dcc.Graph(figure=CSAT_YEAR_TABLE,id="graphCSAT1", style={'display': 'inline-block'}),
            dcc.Graph(figure=CSAT_QUARTER_TABLE,id="graphCSAT2", style={'display': 'inline-block'}),
        ], style={'display': 'inline-block'}),
        html.H2(children='CES Comparison Tables'),
        html.Div(children=[
            dcc.Graph(figure=CES_YEAR_TABLE,id="graphCES1", style={'display': 'inline-block'}),
            dcc.Graph(figure=CES_QUARTER_TABLE,id="graphCES2", style={'display': 'inline-block'}),
        ], style={'display': 'inline-block'}),
        html.Div(children=[
            dcc.Graph(figure=fig0,id="graphF1", style={'display': 'inline-block'}),
            dcc.Graph(figure=fig1,id="graphF2", style={'display': 'inline-block'}),
        ], style={'display': 'inline-block'}),
        html.Div(children=[
            dcc.Graph(figure=fig2,id="graphH1", style={'display': 'inline-block'}),
            dcc.Graph(figure=fig3,id="graphH2", style={'display': 'inline-block'}),
        ], style={'display': 'inline-block'}),
        html.Div(children=[
            dcc.Graph(figure=fig4,id="graphJ1", style={'display': 'inline-block'}),
            dcc.Graph(figure=fig5,id="graphJ2", style={'display': 'inline-block'}),
        ], style={'display': 'inline-block'}),
    ], style={'display': 'flex', 'flex-direction': 'column'})

    app.run_server(debug=True, use_reloader=False) 
   

def get_range_date(query,name_of_query='unknown',verbose=False):

    if not verbose:
        return False

    '''write all the records to the database'''
    with open('reports/range.txt', 'w') as f:
        for r in query['records']:
            f.write(r['CreatedDate'])
            f.write("\n")

    ''' create a new list with all the records in the database'''
    time_list = []
    for r in query['records']:
        time_list.append(r['CreatedDate'])

    ''' get first item and last item '''
    first_item = time_list[0].split('T')[0]
    last_item  = time_list[-1].split('T')[0]

    ret_value = ('[{}] date range = {} - {} - Amount of records to retrieve: {}'.format(name_of_query,first_item,last_item,len(query['records'])))
    print(ret_value)
    return True


def sf_perf(sf_ins,option,timeframe_t,verbose=False):

    name_of_file = 'reports/perf_{}_{}.html'.format(option, timeframe_t).lower()
    name_of_file =name_of_file.replace(r'[^\w]', '_')
    if name_of_file in os.listdir('.'):
        if verbose:
            print('file already exists')
        return True

    fields = "Recommend_Raiting__c,CreatedDate,Satisfaction_Raiting__c,Promoter__c,Detractor__c,Passive__c,Customer_Effort_Score__c"
    results_all = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = {}".format(fields,timeframe_t))
    ''' review the amount of records'''
    
    get_range_date(results_all,"sf_perf_Survey_Result__c")
    
    result__all__ = calculate_kpis_per_bundle(results_all['records'],timeframe_t) 
    option_list = process_users_(sf_ins,option)
    df = sf_review_performance(sf_ins, option_list, timeframe_t)
   
    '''extracting the data from the dataframe'''
    df_nps = df.tail(1)['NPS'].values[0]
    df_csat = df.tail(1)['CSAT'].values[0]
    df_ces = df.tail(1)['CES'].values[0]

    _nps_text_ =  "NPS = ({}) compared with all org nps = ({})".format(df_nps,result__all__['NPS'],timeframe_t)
    fig0 = NPS_gauge_comp("NPS Comparison",df_nps,result__all__['NPS'])
    fig0.write_image("reports/NPS_gauge_comp.png")
    _csat_text_ = "CSAT = ({}) compared with all org csat = ({})".format(df_csat,result__all__['CSAT'],timeframe_t)
    fig1 = CSAT_gauge_comp("CSAT Comparison",df_csat,result__all__['CSAT'])
    fig1.write_image("reports/CSAT_gauge_comp.png")
    _ces_text_ = "CES = ({}) compared with all org ces = ({})".format(df_ces,result__all__['CES'],timeframe_t)
    fig2 = CES_gauge_comp("CES Comparison",df_ces,result__all__['CES'])
    fig2.write_image("reports/CES_gauge_comp.png")


    # 1. Set up multiple variables to store the titles, text within the report
    page_title_text='My Salesforce Performance Report - {} option : {}'.format(timeframe_t,option)
    title_text = 'Metrics '
    text = 'Shown below we have the metrics for the {} option for the {} timeframe'.format(option,timeframe_t)
    prices_text = 'Summary of the results'
    stats_text = 'All Stats'
    violations = ""

    

    # 2. Combine them together using a long f-string
    html = f'''
        <html>
            <head>
                <title>{page_title_text}</title>
                <link rel="stylesheet" href="css/style.css">
            </head>
            <body>
                <h1>{title_text}</h1>
                <p>{text}</p>
                <section class='line'>
                    <figure class="line__figure figure">
                        <img class="figure__image top" src="CSAT_gauge_comp.png" />
                        <figcaption>{_csat_text_}</figcaption>
                    </figure>
                    <figure class="line__figure figure">
                        <img class="figure__image average" src="NPS_gauge_comp.png" />
                        <figcaption>{_nps_text_}</figcaption>
                    </figure>
                    <figure class="line__figure figure">
                        <img class="figure__image average" src="CES_gauge_comp.png" />
                        <figcaption>{_ces_text_}</figcaption>
                    </figure>
                </section>
                <section class='line'>
                <hr>
                </section>
                <h2>{prices_text}</h2>
                <div style="overflow-x:auto;">
                {df.tail(1).to_html(index=False)}
                </div>
                <h2>{stats_text}</h2>
                <div style="overflow-x:auto;">
                {df.to_html(index=False)}
                </div>
            </body>
        </html>
        '''
    html = html.replace('<table border="1" class="dataframe">', '<table class="styled-table border="1"')
    html = html.replace('NaN', '0')

    # 3. Write the html string as an HTML file
    print('please review the file : {}'.format(name_of_file))
    with open(name_of_file, 'w') as f:
        f.write(html)

    #print('review the file ' + name_of_file)
    css = CSS(string='''
    @page {size: A4; margin: 1cm;} 
    th, td {border: 1px solid black;}
    ''')
    HTML(name_of_file).write_pdf('weasyprint_pdf_report.pdf', stylesheets=[css])


def sf_misc_information(sf,option,verbose=False):
    __ord_dict_user__ = process_users_(sf,option)
    ownerid_list = '(\'{}\')'.format('\',\''.join(row['Id'] for row in __ord_dict_user__))

    cases_fields  = "Case_Complexity__c,Complexity_Detail1__c,Product_Level_Three__c,Product_Level_Two__c,Root_Cause__c,Account.Name"
 
    last_month_val = int(time.strftime('%m'))-1
    current_year = int(time.strftime('%Y'))
    if last_month_val == 0:
        last_month_val = 1 ## workaround to handle the change of the year : no time to resolve this now.
    LAST_MONTH   = month[last_month_val]
    THIS_QUARTER = "{}-Q{}".format(current_year,get_current_quarter_number()) 
    LAST_QUARTER = "{}-Q{}".format(current_year,get_current_quarter_number()-1) 

    timer_used = {'THIS_QUARTER':THIS_QUARTER,'LAST_QUARTER':LAST_QUARTER,'LAST_MONTH':LAST_MONTH}
    
    print(ownerid_list)
    qOpen_0 = cleanup_entry(sf.query_all('SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}'.format(cases_fields,ownerid_list, list(timer_used)[0])),cases_fields)
    qOpen_1 = cleanup_entry(sf.query_all('SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}'.format(cases_fields,ownerid_list, list(timer_used)[1])),cases_fields)
    qOpen_2 = cleanup_entry(sf.query_all('SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}'.format(cases_fields,ownerid_list, list(timer_used)[2])),cases_fields)
    

    df_qOpen_cl_0 = pd.DataFrame.from_dict(qOpen_0)
    df_qOpen_cl_1 = pd.DataFrame.from_dict(qOpen_1)
    df_qOpen_cl_2 = pd.DataFrame.from_dict(qOpen_2)

    Case_Complexity__c_0_tfq,Root_Cause__c_0_tfq,Product_Type_0_tfq,Prod_Info__c_0_tfq = Get_Complexity_analysis(df_qOpen_cl_0)
    Case_Complexity__c_1_lfq,Root_Cause__c_1_lfq,Product_Type_1_lfq,Prod_Info__c_1_lfq = Get_Complexity_analysis(df_qOpen_cl_1)
    Case_Complexity__c_2_lfq,Root_Cause__c_2_lfq,Product_Type_2_lfq,Prod_Info__c_2_lfq = Get_Complexity_analysis(df_qOpen_cl_2)


    ##############
    rc1 = unique(list(Case_Complexity__c_0_tfq) + list(Case_Complexity__c_1_lfq) + list(Case_Complexity__c_2_lfq))
    value_0 = []
    value_1 = []
    value_2 = []
    for  index in list(rc1):
        value_0.append( Case_Complexity__c_0_tfq[index] if index in Case_Complexity__c_0_tfq else 0 )
        value_1.append( Case_Complexity__c_1_lfq[index] if index in Case_Complexity__c_1_lfq else 0 )
        value_2.append( Case_Complexity__c_2_lfq[index] if index in Case_Complexity__c_2_lfq else 0 )

    Case_Complexity__c_ = {'Name':list(rc1),timer_used['LAST_QUARTER']:value_0,timer_used['THIS_QUARTER']:value_1,timer_used['LAST_MONTH']:value_2}
    Case_Complexity__c_type = pd.DataFrame(Case_Complexity__c_)
    Case_Complexity__c_type.loc[len(Case_Complexity__c_type.index)] = ['Total', Case_Complexity__c_type[timer_used['LAST_QUARTER']].sum(),Case_Complexity__c_type[timer_used['THIS_QUARTER']].sum(),Case_Complexity__c_type[timer_used['LAST_MONTH']].sum()] 

    str_lfq = timer_used['LAST_QUARTER']+' %'
    Case_Complexity__c_type[str_lfq] = Case_Complexity__c_type.apply(lambda row: round(row[timer_used['LAST_QUARTER']] / Case_Complexity__c_type[timer_used['LAST_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['THIS_QUARTER']+' %'
    Case_Complexity__c_type[str_tfq] = Case_Complexity__c_type.apply(lambda row: round(row[timer_used['THIS_QUARTER']] / Case_Complexity__c_type[timer_used['THIS_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['LAST_MONTH']+' %'
    Case_Complexity__c_type[str_tfq] = Case_Complexity__c_type.apply(lambda row: round(row[timer_used['LAST_MONTH']] / Case_Complexity__c_type[timer_used['LAST_MONTH']].iloc[-1]*100,1), axis=1)

    
    Case_Complexity__c_type.to_html('cc.html',index = False)


    ###############
    rc1 = unique(list(Prod_Info__c_0_tfq) + list(Prod_Info__c_1_lfq) + list(Prod_Info__c_2_lfq))
    value_0 = []
    value_1 = []
    value_2 = []
    for  index in list(rc1):
        value_0.append( Prod_Info__c_0_tfq[index] if index in Prod_Info__c_0_tfq else 0 )
        value_1.append( Prod_Info__c_1_lfq[index] if index in Prod_Info__c_1_lfq else 0 )
        value_2.append( Prod_Info__c_2_lfq[index] if index in Prod_Info__c_2_lfq else 0 )

    Prod_Info__c = {'Name':list(rc1),timer_used['LAST_QUARTER']:value_0,timer_used['THIS_QUARTER']:value_1,timer_used['LAST_MONTH']:value_2}
    Prod_Info__c_type = pd.DataFrame(Prod_Info__c)
    Prod_Info__c_type.loc[len(Prod_Info__c_type.index)] = ['Total', Prod_Info__c_type[timer_used['LAST_QUARTER']].sum(),Prod_Info__c_type[timer_used['THIS_QUARTER']].sum(),Prod_Info__c_type[timer_used['LAST_MONTH']].sum()] 

    str_lfq = timer_used['LAST_QUARTER']+' %'
    Prod_Info__c_type[str_lfq] = Prod_Info__c_type.apply(lambda row: round(row[timer_used['LAST_QUARTER']] / Prod_Info__c_type[timer_used['LAST_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['THIS_QUARTER']+' %'
    Prod_Info__c_type[str_tfq] = Prod_Info__c_type.apply(lambda row: round(row[timer_used['THIS_QUARTER']] / Prod_Info__c_type[timer_used['THIS_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['LAST_MONTH']+' %'
    Prod_Info__c_type[str_tfq] = Prod_Info__c_type.apply(lambda row: round(row[timer_used['LAST_MONTH']] / Prod_Info__c_type[timer_used['LAST_MONTH']].iloc[-1]*100,1), axis=1)


    Prod_Info__c_type.to_html('pi.html',index = False)

    ###############
    rc1 = unique(list(Root_Cause__c_0_tfq) + list(Root_Cause__c_1_lfq)  + list(Root_Cause__c_2_lfq))
    value_0 = []
    value_1 = []
    value_2 = []
    for  index in list(rc1):
        value_0.append( Root_Cause__c_0_tfq[index] if index in Root_Cause__c_0_tfq else 0 )
        value_1.append( Root_Cause__c_1_lfq[index] if index in Root_Cause__c_1_lfq else 0 )
        value_2.append( Root_Cause__c_2_lfq[index] if index in Root_Cause__c_2_lfq else 0 )

    Root_Cause_ = {'Name':list(rc1),timer_used['LAST_QUARTER']:value_0,timer_used['THIS_QUARTER']:value_1,timer_used['LAST_MONTH']:value_2}
    Root_Cause__Type = pd.DataFrame(Root_Cause_)
    Root_Cause__Type.loc[len(Root_Cause__Type.index)] = ['Total', Root_Cause__Type[timer_used['LAST_QUARTER']].sum(),Root_Cause__Type[timer_used['THIS_QUARTER']].sum(),Root_Cause__Type[timer_used['LAST_MONTH']].sum()] 
    
    str_lfq = timer_used['LAST_QUARTER']+' %'
    Root_Cause__Type[str_lfq] = Root_Cause__Type.apply(lambda row: round(row[timer_used['LAST_QUARTER']] / Root_Cause__Type[timer_used['LAST_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['THIS_QUARTER']+' %'
    Root_Cause__Type[str_tfq] = Root_Cause__Type.apply(lambda row: round(row[timer_used['THIS_QUARTER']] / Root_Cause__Type[timer_used['THIS_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['LAST_MONTH']+' %'
    Root_Cause__Type[str_tfq] = Root_Cause__Type.apply(lambda row: round(row[timer_used['LAST_MONTH']] / Root_Cause__Type[timer_used['LAST_MONTH']].iloc[-1]*100,1), axis=1)
    
    Root_Cause__Type.to_html('rc.html',index = False)

    #####################
    rc1 = unique(list(Product_Type_0_tfq) + list(Product_Type_1_lfq)+ list(Product_Type_2_lfq))
    value_0 = []
    value_1 = []
    value_2 = []
    for  index in list(rc1):
        value_0.append( Product_Type_0_tfq[index] if index in Product_Type_0_tfq else 0 )
        value_1.append( Product_Type_1_lfq[index] if index in Product_Type_1_lfq else 0 )
        value_2.append( Product_Type_2_lfq[index] if index in Product_Type_2_lfq else 0 )

    Product_type_ = {'Name':list(rc1),timer_used['LAST_QUARTER']:value_0,timer_used['THIS_QUARTER']:value_1,timer_used['LAST_MONTH']:value_2}
    df_Product_Type = pd.DataFrame(Product_type_)
    df_Product_Type.loc[len(df_Product_Type.index)] = ['Total', df_Product_Type[timer_used['LAST_QUARTER']].sum(),df_Product_Type[timer_used['THIS_QUARTER']].sum(),df_Product_Type[timer_used['LAST_MONTH']].sum()] 
    
    str_lfq = timer_used['LAST_QUARTER']+' %'
    df_Product_Type[str_lfq] = df_Product_Type.apply(lambda row: round(row[timer_used['LAST_QUARTER']] / df_Product_Type[timer_used['LAST_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['THIS_QUARTER']+' %'
    df_Product_Type[str_tfq] = df_Product_Type.apply(lambda row: round(row[timer_used['THIS_QUARTER']] / df_Product_Type[timer_used['THIS_QUARTER']].iloc[-1]*100,1), axis=1)
    str_tfq = timer_used['LAST_MONTH']+' %'
    df_Product_Type[str_tfq] = df_Product_Type.apply(lambda row: round(row[timer_used['THIS_QUARTER']] / df_Product_Type[timer_used['THIS_QUARTER']].iloc[-1]*100,1), axis=1)

    df_Product_Type.to_html('pt.html',index = False)

    ####################
    excel_name = 'reports/complexity_analysis_{}.xlsx'.format(option)
    sheet_name1  = '{}'.format(option).lower().replace(':','_')
    writer = pd.ExcelWriter(excel_name,engine='xlsxwriter')
    workbook=writer.book
    worksheet=workbook.add_worksheet(sheet_name1)
    writer.sheets[sheet_name1] = worksheet

    Case_Complexity__c_type.name = 'Complexity Analysis'
    cell_format = workbook.add_format({'bold': True, 'font_color': '00ADA4','size':16})
    worksheet.write_string(0, 0, Case_Complexity__c_type.name,cell_format)
    row_pos = 1 
    Case_Complexity__c_type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += Case_Complexity__c_type.shape[0] + 2 
    
    Root_Cause__Type.name = ' Root Cause Analysis'
    worksheet.write_string(row_pos, 0, Root_Cause__Type.name,cell_format)
    row_pos += 2 
    Root_Cause__Type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += Root_Cause__Type.shape[0] + 2 
    
    Prod_Info__c_type.name = 'Prod Info - Level Two'
    worksheet.write_string(row_pos, 0, Prod_Info__c_type.name,cell_format)
    row_pos += 2 
    Prod_Info__c_type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += Prod_Info__c_type.shape[0] + 2 
    
    df_Product_Type.name = ' Product type Analysis'
    worksheet.write_string(row_pos, 0, df_Product_Type.name,cell_format)
    row_pos += 2 
    df_Product_Type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += df_Product_Type.shape[0] + 2 
    
    writer.save()
    print('file created successfully : ',excel_name)
    return Case_Complexity__c_type,Root_Cause__Type,Prod_Info__c_type,df_Product_Type


def Get_Top_Customers(sf,ownerid_list):
    __ord_dict_user__  = ownerid_list
    ownerid_list = '(\'{}\')'.format('\',\''.join(row['Id'] for row in __ord_dict_user__))

    cases_fields  = "Id,AccountId,OwnerId,Subject,Account.Name,Owner.Name,Owner.Email,Owner.Title,Owner.Alias"
    open_cus = sf.query_all("SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}".format(cases_fields,ownerid_list, 'THIS_FISCAL_YEAR'))
    open_cus_clean = cleanup_entry(open_cus,cases_fields)
    df_ = pd.DataFrame.from_dict(open_cus_clean)
    df_1 = df_['AccountName'].value_counts(dropna = False, ascending=False).reset_index()
    df_1.columns = ['Accounts', 'cases']
    #print(df_1.head(10))

    return df_1.head(10)

def Compare_this_last_month(sf,ownerid_list):
    __ord_dict_user__  = ownerid_list
    ownerid_list = '(\'{}\')'.format('\',\''.join(row['Id'] for row in __ord_dict_user__))

    cases_fields  = "Id,AccountId,OwnerId,Subject,Case_Complexity__c,Complexity_Detail1__c,Product_Level_Three__c,Product_Level_Two__c,Root_Cause__c,Case_Number__c,SLA_Overrun__c,CreatedDate,Survey_Sent_Date__c,Resolved_Date__c,Account.Name,Owner.Name,Owner.Email,Owner.Title,Owner.Alias"
    qOpen_lm = sf.query_all("SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}".format(cases_fields,ownerid_list, 'LAST_MONTH'))
    qOpen_lm1y = sf.query_all("SELECT {} FROM Case WHERE OwnerId IN {} AND CreatedDate = {}".format(cases_fields,ownerid_list, 'N_MONTHS_AGO:13'))

    pd_lm = pd.DataFrame.from_dict(qOpen_lm['records'])
    pd_lm1y = pd.DataFrame.from_dict(qOpen_lm1y['records'])


    month_pd_lm = pd_lm['CreatedDate'].head(1).to_string().split('-')
    month_pd_lm = month_pd_lm[0]+'-'+month_pd_lm[1]+':'+str(pd_lm.shape[0])
    month_pd_lm1y = pd_lm1y['CreatedDate'].head(1).to_string().split('-')
    month_pd_lm1y = month_pd_lm1y[0]+'-'+month_pd_lm1y[1]+':'+str(pd_lm1y.shape[0])
    month_pd_lm
    month_pd_lm = month_pd_lm[1:].strip().split(':')
    month_pd_lm1y = month_pd_lm1y[1:].strip().split(':')

    print(month_pd_lm)
    print(month_pd_lm1y)
    
    return month_pd_lm,month_pd_lm1y

    

def sf_capacity(sf_ins,option,verbose=False):
    name_of_file = 'reports/capacity_{}.html'.format(option).lower()
    name_of_file =name_of_file.replace(r'[^\w]', '_')
    if name_of_file in os.listdir('.'):
        if verbose:
            print('file already exists')
        return True

    timeframes = {
        1: 'THIS_FISCAL_YEAR',
        2: 'LAST_MONTH',
        3: 'THIS_FISCAL_QUARTER',
        4: 'LAST_FISCAL_QUARTER',
        }

    this_year_str    = 'THIS_FISCAL_YEAR'
    last_month_str   = 'LAST_MONTH'
    this_quarter_str = 'THIS_FISCAL_QUARTER'
    last_quarter_str = 'LAST_FISCAL_QUARTER'

    option_list = process_users_(sf_ins,option)

    ty,ly = Compare_this_last_month(sf_ins,option_list)
    Case_Complexity__c_type,Root_Cause__Type,Prod_Info__c_type,df_Product_Type = sf_misc_information(sf_ins,option)
    top10cus = Get_Top_Customers(sf_ins,option_list)

    this_year    = sf_review_performance(sf_ins, option_list, this_year_str)
    last_month   = sf_review_performance(sf_ins, option_list, last_month_str)
    this_quarter = sf_review_performance(sf_ins, option_list, this_quarter_str)
    last_quarter = sf_review_performance(sf_ins, option_list, last_quarter_str)

    last_month_nps  = last_month.tail(1)['NPS'].values[0]
    last_month_csat = last_month.tail(1)['CSAT'].values[0]
    last_month_ces  = last_month.tail(1)['CES'].values[0]
    last_month_1res = last_month.tail(1)["First Compliance Resolution %"].values[0]
    last_month_cr   = last_month.tail(1)['Resolution Compliance'].values[0]

    this_quarter_nps  = this_quarter.tail(1)['NPS'].values[0]
    this_quarter_csat = this_quarter.tail(1)['CSAT'].values[0]
    this_quarter_ces  = this_quarter.tail(1)['CES'].values[0]
    this_quarter_1res = this_quarter.tail(1)["First Compliance Resolution %"].values[0]
    this_quarter_cr   = this_quarter.tail(1)['Resolution Compliance'].values[0]

    last_quarter_nps  = last_quarter.tail(1)['NPS'].values[0]
    last_quarter_csat = last_quarter.tail(1)['CSAT'].values[0]
    last_quarter_ces  = last_quarter.tail(1)['CES'].values[0]
    last_quarter_1res = last_quarter.tail(1)["First Compliance Resolution %"].values[0]
    last_quarter_cr   = last_quarter.tail(1)['Resolution Compliance'].values[0]

    last_month_val = int(time.strftime('%m'))-1
    current_year = int(time.strftime('%Y'))
    if last_month_val == 0: 
        last_month_val = 12 
        current_year = current_year - 1
    
    LAST_MONTH   = month[last_month_val]
    THIS_QUARTER = "{}-Q{}".format(current_year,get_current_quarter_number()) 
    LAST_QUARTER = "{}-Q{}".format(current_year,get_current_quarter_number()-1) 
  
    CASES_LAST_MONTH = "# of cases " + LAST_MONTH 
    CASES_THIS_QUARTER = "# of cases " + THIS_QUARTER 
    CASES_LAST_QUARTER = "# of cases " + LAST_QUARTER 
    last_month.rename(columns = {'Open Cases':CASES_LAST_MONTH},inplace=True)
    this_quarter.rename(columns = {'Open Cases':CASES_THIS_QUARTER},inplace=True)
    last_quarter.rename(columns = {'Open Cases':CASES_LAST_QUARTER},inplace=True)
  
    ### generate table for month capacity calculation
    df_month = last_month.filter(['Name',CASES_LAST_MONTH])
    df_month.name = "Utlization for " + LAST_MONTH
    month_capacity = '%Utilization '+LAST_MONTH
    df_month['Baseline Capacity'] = last_month.apply(lambda row: row['Capacity']/3 , axis=1) 
    df_month[month_capacity] = last_month.apply(lambda row: round((row[CASES_LAST_MONTH] / (row['Capacity']/3))*100,0) if row['Capacity'] > 0 else 0 , axis=1) 
    df_month['Additional Activities Hours'] = 0
    df_month['% Additional Activities'] = last_month.apply(lambda row: row['% Additional Activities'] , axis=1) 
    df_month['Total Utilization'] = 0 ## df_month.apply(lambda row: row[month_capacity]+row['% Additional Activities']  , axis=1) 
    df_month['additional activities Description'] = last_quarter.filter(['Additional Activities'])


    #### THIS QUARTER ########
    df_tfq_ = this_quarter.filter(['Name',CASES_THIS_QUARTER])
    df_tfq_.name = "Utlization for " + THIS_QUARTER 
    df_month['Baseline Capacity'] = this_quarter.filter(['Capacity'])
    tfq_capacity = '%Utilization '+THIS_QUARTER
    df_tfq_[tfq_capacity] = this_quarter.apply(lambda row: round((row[CASES_THIS_QUARTER] / (row['Capacity']))*100,0) if row['Capacity'] > 0 else 0 , axis=1) 
    df_tfq_['% Additional Activities'] = this_quarter.apply(lambda row: row['% Additional Activities'] , axis=1) 
    df_tfq_['Total Utilization '+THIS_QUARTER] = 0 # df_tfq_.apply(lambda row: row[tfq_capacity]+row['% Additional Activities']  , axis=1) 

    #### LAST QUARTER ########
    df_lfq_ = this_quarter.filter(['Name',CASES_LAST_QUARTER])
    df_lfq_.name = "Utlization for " + LAST_QUARTER 
    df_month['Baseline Capacity'] = last_quarter.filter(['Capacity'])
    lfq_capacity = '%Utilization '+LAST_QUARTER
    df_lfq_[lfq_capacity] = last_quarter.apply(lambda row: round((row[CASES_LAST_QUARTER] / (row['Capacity']))*100,0) if row['Capacity'] > 0 else 0 , axis=1) 
    df_lfq_['% Additional Activities'] = last_quarter.apply(lambda row: row['% Additional Activities'] , axis=1) 
    df_lfq_['Total Utilization '+LAST_QUARTER] = 0 # df_lfq_.apply(lambda row: row[lfq_capacity]+row['% Additional Activities']  , axis=1) 

    df2 = pd.DataFrame()
    csat_row ={}
    csat_row['Name'] = 'CSAT'
    csat_row[LAST_MONTH] = last_month_csat
    csat_row[THIS_QUARTER] = this_quarter_csat
    csat_row[LAST_QUARTER] = last_quarter_csat
    df2 = df2.append(csat_row, ignore_index = True)

    ces_row = {}
    ces_row['Name'] = 'CES'
    ces_row[LAST_MONTH] = last_month_ces
    ces_row[THIS_QUARTER] = this_quarter_ces
    ces_row[LAST_QUARTER] = last_quarter_ces
    df2 = df2.append(ces_row, ignore_index = True)
    
    nps_row = {}
    nps_row['Name'] = 'NPS' 
    nps_row[LAST_MONTH] = last_month_nps
    nps_row[THIS_QUARTER] = this_quarter_nps
    nps_row[LAST_QUARTER] = last_quarter_nps
    df2 = df2.append(nps_row, ignore_index = True)
 
    resp1_row = {}
    resp1_row['Name'] = 'First Response Compliance'
    resp1_row[LAST_MONTH] = last_month_1res
    resp1_row[THIS_QUARTER] = this_quarter_1res
    resp1_row[LAST_QUARTER] = last_quarter_1res
    df2 = df2.append(resp1_row, ignore_index = True)

    respcr_row = {}
    respcr_row['Name']        = 'Response Compliance'
    respcr_row[LAST_MONTH]    = last_month_cr
    respcr_row[THIS_QUARTER]  = this_quarter_cr
    respcr_row[LAST_QUARTER]  = last_quarter_cr
    df2 = df2.append(respcr_row, ignore_index = True)

    ##'Resolution Compliance'


    sheet_name1 = name_of_file.split('/')[1].split('.')[0].replace(':','_')
    
    ##### 
    df2.name = "Kpis analysis fro the current and last quarter of the group " + option
    this_year.name  = "Year to date analysis for the group "+ option
    excel_name = name_of_file.split('.')[0]+".xlsx"

    
    writer = pd.ExcelWriter(excel_name,engine='xlsxwriter')
    workbook=writer.book
    worksheet=workbook.add_worksheet(sheet_name1)
    writer.sheets[sheet_name1] = worksheet

    cell_format = workbook.add_format({'bold': True, 'font_color': '00ADA4','size':16})

    ##### last month information
    colp = 0 
    rowp = 0 
    worksheet.write_string(rowp,colp, df_month.name,cell_format)
    rowp +=2
    df_month.to_excel(writer,sheet_name=sheet_name1,startrow=rowp , startcol=colp,index=False)
    rowp = rowp + df_month.shape[0]
    ##### quarters information
    rowp = 0  
    colp = df_month.shape[1] + 2 
    worksheet.write_string(rowp,colp, df_tfq_.name,cell_format)
    rowp +=2
    df_tfq_.to_excel(writer,sheet_name=sheet_name1,startrow=rowp , startcol=colp,index=False)
    rowp = rowp + df_tfq_.shape[0]

    rowp = 0 
    colp += df_tfq_.shape[1] + 2 
    worksheet.write_string(rowp,colp, df_lfq_.name,cell_format)
    rowp +=2
    df_lfq_.to_excel(writer,sheet_name=sheet_name1,startrow=rowp , startcol=colp,index=False)
    rowp = rowp + df_lfq_.shape[0]

    ##### kpis information 
    rowp +=2
    colp = 0 
    worksheet.write_string(rowp, colp, df2.name,cell_format)
    rowp +=2
    df2.to_excel(writer,sheet_name=sheet_name1,startrow=rowp, startcol=colp,index=False)
    rowp = rowp + df2.shape[0]


    ### information about last month and 1y ago last month
    colp = 0 
    rowp +=2
    worksheet.write_string(rowp, colp, "# of cases opened",cell_format)
    rowp+=1
    colp+=0
    worksheet.write_string(rowp, colp, ly[0])
    colp+=1
    worksheet.write_string(rowp, colp, ty[0])
    colp+=1
    worksheet.write_string(rowp, colp, "%change")
    rowp+=1
    colp=0
    worksheet.write_string(rowp, colp, ly[1])
    colp+=1
    worksheet.write_string(rowp, colp, ty[1])
    colp+=1
    #print(ly[1],ty[1])
    ll = int(ly[1])
    yy = int(ty[1])
    change__ = round(abs(yy - ll)/ll*100,1)
    worksheet.write_string(rowp, colp,str(change__))
    rowp+=1


    ### Year to date information
    rowp +=2
    colp = 0 
    worksheet.write_string(rowp, colp, this_year.name,cell_format)
    rowp +=2
    this_year.to_excel(writer,sheet_name=sheet_name1,startrow=rowp, startcol=colp,index=False)
    rowp += this_year.shape[0] + 2 
    
    top10cus.name = 'Top 10 Customers for the group ' + option
    rowp +=2
    colp = 0 
    worksheet.write_string(rowp, colp, top10cus.name,cell_format)
    rowp +=2
    top10cus.to_excel(writer,sheet_name=sheet_name1,startrow=rowp, startcol=colp,index=False)
    row_pos = rowp + top10cus.shape[0] + 2 
    


    Case_Complexity__c_type.name = 'Complexity Analysis'
    worksheet.write_string(0, 0, Case_Complexity__c_type.name,cell_format)
    row_pos += 1 
    Case_Complexity__c_type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += Case_Complexity__c_type.shape[0] + 2 
    
    Root_Cause__Type.name = ' Root Cause Analysis'
    worksheet.write_string(row_pos, 0, Root_Cause__Type.name,cell_format)
    row_pos += 2 
    Root_Cause__Type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += Root_Cause__Type.shape[0] + 2 
    
    Prod_Info__c_type.name = 'Prod Info - Level Two'
    worksheet.write_string(row_pos, 0, Prod_Info__c_type.name,cell_format)
    row_pos += 2 
    Prod_Info__c_type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += Prod_Info__c_type.shape[0] + 2 
    
    df_Product_Type.name = ' Product type Analysis'
    worksheet.write_string(row_pos, 0, df_Product_Type.name,cell_format)
    row_pos += 2 
    df_Product_Type.to_excel(writer,sheet_name=sheet_name1,startrow=row_pos, startcol=0,index=False)
    row_pos += df_Product_Type.shape[0] + 2 

    writer.save()
  



def sf_capacity_old_and_working(sf_ins,option,verbose=False):

    name_of_file = 'reports/capacity_{}.html'.format(option).lower()
    name_of_file =name_of_file.replace(r'[^\w]', '_')
    if name_of_file in os.listdir('.'):
        if verbose:
            print('file already exists')
        return True

    this_year_str    = 'THIS_FISCAL_YEAR'
    last_month_str   = 'LAST_MONTH'
    this_quarter_str = 'THIS_FISCAL_QUARTER'
    last_quarter_str = 'LAST_FISCAL_QUARTER'
    n2quarter_ago    = 'N_QUARTERS_AGO:2'

    option_list = process_users_(sf_ins,option)
    this_year = sf_review_performance(sf_ins, option_list, this_year_str)
    last_month = sf_review_performance(sf_ins, option_list, last_month_str)
    this_quarter = sf_review_performance(sf_ins, option_list, this_quarter_str)
    last_quarter = sf_review_performance(sf_ins, option_list, last_quarter_str)
    n2quarter = sf_review_performance(sf_ins, option_list, n2quarter_ago)

    last_month_nps = last_month.tail(1)['NPS'].values[0]
    last_month_csat = last_month.tail(1)['CSAT'].values[0]
    last_month_ces = last_month.tail(1)['CES'].values[0]

    this_quarter_nps = this_quarter.tail(1)['NPS'].values[0]
    this_quarter_csat = this_quarter.tail(1)['CSAT'].values[0]
    this_quarter_ces = this_quarter.tail(1)['CES'].values[0]

    last_quarter_nps = last_quarter.tail(1)['NPS'].values[0]
    last_quarter_csat = last_quarter.tail(1)['CSAT'].values[0]
    last_quarter_ces = last_quarter.tail(1)['CES'].values[0]

    n2_quarter_nps = n2quarter.tail(1)['NPS'].values[0]
    n2_quarter_csat = n2quarter.tail(1)['CSAT'].values[0]
    n2_quarter_ces = n2quarter.tail(1)['CES'].values[0]

    last_month_val = int(time.strftime('%m'))-1
    current_year = int(time.strftime('%Y'))
    if last_month_val == 0 : 
        last_month_val = 12 
        current_year = current_year - 1

    LAST_MONTH   = month[last_month_val]
    THIS_QUARTER = "{}-Q{}".format(current_year,get_current_quarter_number()) 
    LAST_QUARTER = "{}-Q{}".format(current_year,get_current_quarter_number()-1) 
    N2_QUARTER   = "{}-Q{}".format(current_year,get_current_quarter_number()-2)

    
    last_month.rename(columns = {'Open Cases':LAST_MONTH},inplace=True)
    this_quarter.rename(columns = {'Open Cases':THIS_QUARTER},inplace=True)
    last_quarter.rename(columns = {'Open Cases':LAST_QUARTER},inplace=True)
    n2quarter.rename(columns = {'Open Cases':N2_QUARTER},inplace=True)
    
       
    THIS_QUARTER_str = this_quarter.filter(['Name',THIS_QUARTER])
    LAST_QUARTER_str = last_quarter.filter(['Name',LAST_QUARTER])
    N2_QUARTER_str = n2quarter.filter(['Name',N2_QUARTER])
 
    new = last_month.filter(['Name','Title','Capacity','Additional Activities',LAST_MONTH])
    df = pd.merge(new,THIS_QUARTER_str, on='Name',how='outer')
    df = pd.merge(df,LAST_QUARTER_str, on='Name',how='outer')
    df = pd.merge(df,N2_QUARTER_str, on='Name',how='outer')

    ''' Create labels for capacisty calculations based on the new data'''
    month_capacity = 'Capacity-'+LAST_MONTH
    this_quarter_capacity = 'Capacity-'+THIS_QUARTER
    last_quarter_capacity = 'Capacity-'+LAST_QUARTER
    n2quarter_capacity = 'Capacity-'+N2_QUARTER

    
    df[month_capacity] = df.apply(lambda row: round((row[LAST_MONTH] / (row['Capacity']/3))*100,0) if row['Capacity'] > 0 else 0 , axis=1) 
    df[this_quarter_capacity] = df.apply(lambda row: round((row[THIS_QUARTER] / (row['Capacity']))*100,0) if row['Capacity'] > 0 else 0 , axis=1)
    df[last_quarter_capacity] = df.apply(lambda row: round((row[LAST_QUARTER] / (row['Capacity']))*100,0) if row['Capacity'] > 0 else 0 , axis=1)
    df[n2quarter_capacity] = df.apply(lambda row: round((row[N2_QUARTER] / (row['Capacity']))*100,0)if row['Capacity'] > 0 else 0  , axis=1)


    new = df.to_html(index=False)
    '''print the file'''
    with open('reports/cap_.html', 'w') as f:
        f.write(new)

    df2 = pd.DataFrame()
    csat_row ={}
    csat_row['Name'] = 'CSAT'
    csat_row[LAST_MONTH] = last_month_csat
    csat_row[THIS_QUARTER] = this_quarter_csat
    csat_row[LAST_QUARTER] = last_quarter_csat
    csat_row[N2_QUARTER] = n2_quarter_csat
    df2 = df2.append(csat_row, ignore_index = True)

    ces_row = {}
    ces_row['Name'] = 'CES'
    ces_row[LAST_MONTH] = last_month_ces
    ces_row[THIS_QUARTER] = this_quarter_ces
    ces_row[LAST_QUARTER] = last_quarter_ces
    ces_row[N2_QUARTER] = n2_quarter_ces
    df2 = df2.append(ces_row, ignore_index = True)
    
    nps_row = {}
    nps_row['Name'] = 'NPS'
    nps_row[LAST_MONTH] = last_month_nps
    nps_row[THIS_QUARTER] = this_quarter_nps
    nps_row[LAST_QUARTER] = last_quarter_nps
    nps_row[N2_QUARTER] = n2_quarter_nps
    df2 = df2.append(nps_row, ignore_index = True)


    fields = "Recommend_Raiting__c,CreatedDate,Satisfaction_Raiting__c,Promoter__c,Detractor__c,Passive__c,Customer_Effort_Score__c"
    results_all = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = {}".format(fields,'THIS_FISCAL_YEAR'))
    ''' review the amount of records'''
    
    get_range_date(results_all,"sf_perf_Survey_Result__c")
    
    result__all__ = calculate_kpis_per_bundle(results_all['records'],'THIS_FISCAL_YEAR') 
    df_this_year = this_year
   
    '''extracting the data from the dataframe'''
    df_nps = this_year.tail(1)['NPS'].values[0]
    df_csat = this_year.tail(1)['CSAT'].values[0]
    df_ces = this_year.tail(1)['CES'].values[0]
    _nps_text_ =  "NPS = ({}) compared with all org nps = ({})".format(df_nps,result__all__['NPS'],'THIS_FISCAL_YEAR')
    fig0 = NPS_gauge_comp("NPS Comparison",df_nps,result__all__['NPS'])
    fig0.write_image("reports/NPS_gauge_comp.png")
    _csat_text_ = "CSAT = ({}) compared with all org csat = ({})".format(df_csat,result__all__['CSAT'],'THIS_FISCAL_YEAR')
    fig1 = CSAT_gauge_comp("CSAT Comparison",df_csat,result__all__['CSAT'])
    fig1.write_image("reports/CSAT_gauge_comp.png")
    _ces_text_ = "CES = ({}) compared with all org ces = ({})".format(df_ces,result__all__['CES'],'THIS_FISCAL_YEAR')
    fig2 = CES_gauge_comp("CES Comparison",df_ces,result__all__['CES'])
    fig2.write_image("reports/CES_gauge_comp.png")


    # 2. Combine them together using a long f-string
    page_title_text = 'Capacity Report'
    title_text = 'Capacity Report for {}'.format(option)
    text = 'This report shows the number of open cases per engineer for the last 3 quarters.'
    kpi_text = 'KPIs for the team'
    text2 = 'This report shows the number kpis per group for the last 3 quarters.'
    this_year.fillna(0,inplace=True)
    html = f'''
        <html>
            <head>
                <title>{page_title_text}</title>
                <link rel="stylesheet" href="css/style.css">
            </head>
            <body>
                <h1>{title_text}</h1>
                <p>{text}</p>
                {df.to_html(index=False)}
                <h1>{kpi_text}</h1>
                <p>{text2}</p>
                {df2.to_html(index=False)}
                <h1>This Year to Date information for all the team</h1>
                {this_year.to_html(index=False)}
                <section class='line'>
                    <figure class="line__figure figure">
                        <img class="figure__image top" src="CSAT_gauge_comp.png" />
                        <figcaption>{_csat_text_}</figcaption>
                    </figure>
                    <figure class="line__figure figure">
                        <img class="figure__image average" src="NPS_gauge_comp.png" />
                        <figcaption>{_nps_text_}</figcaption>
                    </figure>
                    <figure class="line__figure figure">
                        <img class="figure__image average" src="CES_gauge_comp.png" />
                        <figcaption>{_ces_text_}</figcaption>
                    </figure>
                </section>
                <section class='line'>
                <hr>
                </section>
            </body>
        </html>
        '''
    html = html.replace('<table border="1" class="dataframe">', '<table class="styled-table border="1"')
    
    # 3. Write the html string as an HTML file
    with open(name_of_file, 'w') as f:
        f.write(html)
    print('review the report file {}'.format(name_of_file))

    sheet_name1 = name_of_file.split('/')[1].split('.')[0].replace(':','_')
    
    ##### 
    df.name = "Capacity Report for the group "+ option
    df2.name = "Kpis analysis fro the current and last quarter of the group " + option
    this_year.name  = "Year to date analysis for the group "+ option
    excel_name = name_of_file.split('.')[0]+".xlsx"

    
    writer = pd.ExcelWriter(excel_name,engine='xlsxwriter')
    workbook=writer.book
    worksheet=workbook.add_worksheet(sheet_name1)
    writer.sheets[sheet_name1] = worksheet

    cell_format = workbook.add_format({'bold': True, 'font_color': '00ADA4','size':16})
    worksheet.write_string(0, 0, df.name,cell_format)
    df.to_excel(writer,sheet_name=sheet_name1,startrow=2 , startcol=0,index=False)
    worksheet.write_string(df.shape[0] + 4, 0, df2.name,cell_format)
    start_row_for_second_table = df.shape[0] + 6
    df2.to_excel(writer,sheet_name=sheet_name1,startrow=start_row_for_second_table, startcol=0,index=False)
    start_row_for_third_table = df.shape[0] + df2.shape[0] + 8
    worksheet.write_string(start_row_for_third_table, 0, this_year.name,cell_format)
    this_year.to_excel(writer,sheet_name=sheet_name1,startrow=start_row_for_third_table+2, startcol=0,index=False)
    writer.save()
    print('file created successfully : ',excel_name)


def calculate_topbox_per_user(sf,list_of_engineers):
    #eng_list_nalinux = ['aelmahra','dmorales','erivera','mmontero','csolano','jortegac']
    #eng_list_nalinux += ["RPadmana","ltenorio","erojasag"]

    ownerid_list = '(\'{}\')'.format('\',\''.join(row for row in list_of_engineers))

    case_fields = ["Id","OwnerId","CaseNumber",'Owner.Alias']
    case_fields_l = ','.join(case_fields)
    query = "SELECT {} FROM Case WHERE Status = 'Closed' AND OwnerId IN {} AND CreatedDate = {}".format(case_fields_l,ownerid_list,'THIS_FISCAL_YEAR')
    case_query = sf.query_all(query)
    __list_of_cases__ = []

    for case in case_query['records']:
        ord_tmp = {}
        for ff in case_fields:
            if ff == "Owner.Alias":
                ord_tmp["OwnerAlias"]  = case['Owner']['Alias']
            else:
                ord_tmp[ff]  = case[ff]
        __list_of_cases__.append(ord_tmp)

    
    pd_c = pd.DataFrame.from_dict(__list_of_cases__)
    survey_fields = ["CreatedDate","Communication_Feedback__c", "Customer_Support_Engineer_Feedback__c","Id","Case__c"]
    survey_fields += ["Other_Feedback__c","Quality_Of_Resolution_Feedback__c", "Recommend_Raiting__c","Satisfaction_Raiting__c"]
    survey_fields_l = ','.join( survey_fields)
    query = "SELECT {} FROM Survey_Result__c WHERE Satisfaction_Raiting__c = 10 AND CreatedDate = {} AND Case__c !=null ORDER BY CreatedDate ASC NULLS FIRST".format(survey_fields_l,'THIS_YEAR')
    survey_query = sf.query_all(query)
    __list_of_surveys  = []
    for survey in survey_query['records']:
        ord_tmp = {}
        for sf in survey_fields: 
            ord_tmp[sf] = survey[sf]
        __list_of_surveys.append(ord_tmp)
    
    pd_s = pd.DataFrame.from_dict(__list_of_surveys)

    inter = []
    for idx in pd_c['Id'].values.tolist(): 
        if idx in pd_s['Case__c'].values.tolist():
            inter.append(idx)

    cleaned = pd_c[pd_c['Id'].isin(inter)]
    return cleaned['OwnerId'].value_counts()



def create_presentation(sf_ins,option,verbose=False):
    p = Presentation(
        theme=ThemeDark(),
        width=1200,
        height=1024,
        margin='0.05',
        transition='none',
        data_dir='./reports/',
        )

    # Frontpage
    ################################################
    page = p.frontpage()
    #page.title('Customer Support Linux and Operations team')
    page.c(1).w('50%').im('https://www.windriver.com/themes/wr/global/images/svg/logo.svg').h('75px')
    page.c(2).w('50%').par('<b>Staff Group Presentation : {} </b> <br> Esteban Zuniga Mora<br>Sr. Manager CSO'.format(option))
    #author = page.author('Esteban Zuniga ')
    #author.institution('Wind River')

    # New Section 
    ################################################
    p.sectionpage('Agenda')

    # New Page 
    ################################################
    page = p.page('Agenda')

    # Paragraph
    page.par('Following agenda is expected to be the base for all the Staff meetings and group reviews')

    # Paragraph
    page.par('Topics:')

    # ulist
    l = page.ul()

    # ulist items
    l.item('Announcements Company/Organization/Team')
    l.item('Recognitions and appraisals ')
    l.item('Team Stats')
    l.item('Roundtable')
    l.item('Action Items')

    # New Page 
    ################################################
    page = p.page('Announcements Company/Organization/Team ')
    page.par('<a href="https://windriversystems.sharepoint.com/sites/People-Team/SitePages/Manager-Talk-Track.aspx">Link to Updates</a> ')
    page.par('Organization Updates')
    page.par('Team Updates')
    

    # New Page 
    ################################################
    page = p.page('Recognitions and appraisals ')
    page.par('<center><a href="https://analytics.reflektive.com/v2/app/reports/5d949740-f37e-4e16-bbd7-739f776a22ba">Link to reflektive Report</a></center>')
    page.im('https://www.reflektive.com/wp-content/uploads/2020/03/reflective-logo-full-color-01.svg').w('40%')

    # New Page 
    ################################################
    option_list = process_users_(sf_ins,option)
    dir_resultsn = dict()
    
    counter = 1 
    for f in option_list:
        string_f = "<b>{}</b>".format(counter)
        dir_resultsn[string_f] = f['Name']
        counter = counter + 1

    page = p.page('Team Stats')
    table = dict_to_html_table(dir_resultsn)
    page.par(table)
    
    this_year_str    = 'THIS_FISCAL_YEAR'
    this_year   = sf_review_performance(sf_ins, option_list, this_year_str)
   
    '''extracting the data from the dataframe'''

    ff = ['Open Cases','Closed Cases','Resolved Cases %','Open CVE','Closed CVE',
        'NPS','CSAT','CES','Survey Rate','First Compliance Resolution %','Resolution Compliance','TopBox']


    dir_results = dict()
    for f in ff:
        dir_results[f] = this_year.tail(1)[f].values[0]

    page = p.page('KPis Results YTD')
    table = dict_to_html_table(dir_results)
    page.par(table)


    fields = "Recommend_Raiting__c,CreatedDate,Satisfaction_Raiting__c,Promoter__c,Detractor__c,Passive__c,Customer_Effort_Score__c"
    results_all = sf_ins.query_all("SELECT {} FROM Survey_Result__c WHERE CreatedDate = {}".format(fields,'THIS_FISCAL_YEAR'))
    
    get_range_date(results_all,"sf_perf_Survey_Result__c")
    
    result__all__ = calculate_kpis_per_bundle(results_all['records'],'THIS_FISCAL_YEAR') 
 
    _nps_text_ =  "NPS = ({}) compared with all org nps = ({})".format(dir_results['NPS'],result__all__['NPS'],'THIS_FISCAL_YEAR')
    fig0 = NPS_gauge_comp(_nps_text_,dir_results['NPS'],result__all__['NPS'])
    fig0.write_image("reports/NPS_gauge_comp.png")
    _csat_text_ = "CSAT = ({}) compared with all org csat = ({})".format(dir_results['CSAT'],result__all__['CSAT'],'THIS_FISCAL_YEAR')
    fig1 = CSAT_gauge_comp(_csat_text_,dir_results['CSAT'],result__all__['CSAT'])
    fig1.write_image("reports/CSAT_gauge_comp.png")
    _ces_text_ = "CES = ({}) compared with all org ces = ({})".format(dir_results['CES'],result__all__['CES'],'THIS_FISCAL_YEAR')
    fig2 = CES_gauge_comp(_ces_text_,dir_results['CES'],result__all__['CES'])
    fig2.write_image("reports/CES_gauge_comp.png")
    page = p.page('Comparision with organization values')
    page.c(1).w('33%').im('NPS_gauge_comp.png')
    page.c(2).w('33%').im('CSAT_gauge_comp.png')
    page.c(3).w('33%').im('CES_gauge_comp.png')


    Case_Complexity__c_type,Root_Cause__Type,Prod_Info__c_type,df_Product_Type = sf_misc_information(sf_ins,option)
    top10cus = Get_Top_Customers(sf_ins,option_list)
    page = p.page('Top 10 Customers YTD')


    dfi.export(top10cus, 'reports/top10cus.png')
    dfi.export(Root_Cause__Type, 'reports/rootcause.png')

    page.im('top10cus.png').cl('white').h('70%')
    
    page = p.page('Root Cause Analysis')
    page.im('rootcause.png').cl('white').h('70%')

    page = p.page('Roundtable')
    table = dict_to_html_table(dir_resultsn)
    page.par(table)

    page = p.page('Performance Review ')
    page.par('please submit your vacations before 12/16/22')

    page = p.page('Project Ownership')
    page.par('we need to define all the proccesses: Starting 01/2023')

    ''''
    # New Section 
    ################################################
    p.sectionpage('Introduction')

    # New Page 
    ################################################
    page = p.page('First case')

    # Paragraph
    page.par('We have a very <b>dense</b> matrix. It is the "correct" matrix, but its density makes\
    it hard to efficiently compute its network charachteristics such as its <b>community structure</b>.')

    # Paragraph
    page.par('Example:')

    # ulist
    l = page.ul()

    # ulist items
    l.item('Large dense similarity matrix.')
    l.item('Dimensionality reduction.')
    l.item('Correlation matrix in <b>genetic</b> or <b>protein</b> interaction networks?')

    # Add vspace
    page.vspace('2em')

    # H2
    page.h2('We need to approximate the graph').cl('h2teal').fr()
    '''


    # Save to file
    ################################################
    p.export('minimal_example.html')



def reflektive(verbose=True):
    """ Module to interact with reflektive """
    print("Reflektive: Creating a new session")
    okta = OktaAuth.get_instance()
    cookie = okta.get_session_data()
    if verbose:
        print("\n> Accessing:", WIND_REFLEKTIVE_URL)


    # First redirect to wind reflektive login
    response = requests.get(WIND_REFLEKTIVE_URL, allow_redirects=False)

    if verbose:
        print("\n> Accessing:", response.headers["location"])
    # Redirection to okta login
    response = requests.get(
        response.headers["location"], allow_redirects=False,verify=False)

    cookies_inicial = response.headers["set-cookie"]
    print(cookies_inicial)
    
    

    if verbose:
        print("\n> Accessing:", response.headers["location"])

    
    # Redirects to SAML auth with okta credentials
    response = requests.get(
        response.headers["location"], allow_redirects=False, headers={"cookie": cookie+cookies_inicial})

    cookies = response.headers["set-cookie"]

    soup = BeautifulSoup(response.text, 'html.parser')
    new_url = soup.find(id="appForm").get("action")
    inputs = soup.find(id="appForm").find_all("input")
    data = {}
    for input_data in inputs:
        data[input_data.get("name")] = input_data.get("value")
    response = requests.post(new_url,
                             allow_redirects=True,
                             data=data, headers={"cookie": cookies+cookies_inicial})

    # Session ID temp
    cookies = f'_session_id={response.cookies.get("_session_id")};'

    print('Coookies \n\n\n{}'.format(cookies))

    if verbose:
        print("\n> Accessing:",
              f'{REFLEKTIVE_URL}/users/oauth?third_party_token={THIRD_PARTY_TOKEN}')
    response = requests.get(f'{REFLEKTIVE_URL}/users/oauth?third_party_token={THIRD_PARTY_TOKEN}',
                            allow_redirects=False, headers={"cookie": response.headers["set-cookie"]+cookies_inicial})

    print("Reflektive: Session succesfully created")
    session_id = f'_session_id={response.cookies.get("_session_id")};'

    # test query
    response = requests.get("https://www.reflektive.com/newsfeed/index/v2?offset=0&limit=25&page=0&type=all",
                            allow_redirects=False, headers={"cookie": session_id})
    print(json.dumps(json.loads(response.content.decode()), indent=4, sort_keys=True))

    
    content = {
        "audience": "everyone",
        "feedback_type": "positive",
        "hashtags": [
            "thewindway",
            "wecare",
            "cstool"
        ],
        "isSender": True,
        "likes": [],
        "points": 0,
        "recipients": [
            "b8d95a43-3330-4814-8714-0e8a2ef85d20"
        ],
        "source": "web:recognition_wall",
        "text": "I appreciate the encouragement you gave me to explore new challenges. I have been learning a lot from it, and I am thrilled to collaborate with the team.<p> #thewindway #wecare #cstool</p><br />",
        "type": "real_time_feedback"
    }
    

    print(json.dumps(content))
    #response = requests.post("https://www.reflektive.com/constant_feedbacks",allow_redirects=False, headers={"cookie": session_id, 'Content-type': 'application/json'}, data=json.dumps(content))

    #print(response, response.content)