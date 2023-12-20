import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import datetime
import csv
from collections import Counter
import plotly.express as px
from Salesforce import users


def fetch_surveys_inf(sf_ins,days,filename):
    manager_id = users.sf_user_translate(sf_ins, 'Alias', 'Id', 'Ezunigam')
    c_dict, _c_dict = users.sf_user_get_employees(sf_ins, manager_id)

    manager_id = users.sf_user_translate(sf_ins, 'Alias', 'Id', 'nmarguet')
    b_dict, _b_dict = users.sf_user_get_employees(sf_ins, manager_id)
    a_dict = {**c_dict, **b_dict}
    _a_dict = {**_c_dict, **_b_dict}
    print(a_dict)

    delta_t = datetime.datetime.now() - datetime.timedelta(days=days)
    time_t = str(delta_t).split()[0] + 'T00:00:00.000Z'
    print(time_t)
    query_data = "SELECT Case__c,Chat_Agent__c,Contact__c,Customer_Effort_Score__c,Customer_Support_Engineer_Feedback__c,Doc_Feedback__c,LastModifiedDate,OwnerId,Recommend_Raiting__c,Satisfaction_Raiting__c FROM Survey_Result__c WHERE LastModifiedDate > %s" % time_t
    print(query_data)
    data = sf_ins.query_all_iter(query_data)
    headers = ['Case__c','Chat_Agent__c','Contact__c','Customer_Effort_Score__c','Customer_Support_Engineer_Feedback__c','Doc_Feedback__c','LastModifiedDate','OwnerId','Recommend_Raiting__c','Satisfaction_Raiting__c']
    with open(filename, mode='w') as csv_file_wr:
        csv_object = csv.writer(csv_file_wr, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_object.writerow(headers)
        count = 0
        for row in data:
            count += 1
            items = []
            for header in headers:
                if row[header]:
                    if header == "Chat_Agent__c":
                        items.append(users.sf_user_id2name(sf_ins,row[header]))
                    else:
                        items.append(row[header])
                else:
                    items.append("empty")
            csv_object.writerow(items)

    print(str(count) + " case has been extracted and opened since " + str(days) + " ago")
    return 0

def fetch_cases(sf_ins, config, days, filename, closed_cretead):
    print(filename,closed_cretead,days,config)
    manager_id = users.sf_user_translate(sf_ins, 'Alias', 'Id', 'Ezunigam')
    c_dict, _c_dict = users.sf_user_get_employees(sf_ins, manager_id)

    manager_id = users.sf_user_translate(sf_ins, 'Alias', 'Id', 'nmarguet')
    b_dict, _b_dict = users.sf_user_get_employees(sf_ins, manager_id)
    a_dict = {**c_dict, **b_dict}
    _a_dict = {**_c_dict, **_b_dict}

    names = ""
    for user in a_dict:
        print(user, a_dict[user])
        names += "OwnerId = '%s' OR " % (a_dict[user])
    names = names[:-3]

    delta_t = datetime.datetime.now() - datetime.timedelta(days=days)
    time_t = str(delta_t).split()[0] + 'T00:00:00.000Z'
    print(time_t)

    if closed_cretead == 'CLOSED':
        string = 'ClosedDate'
    else:
        string = 'CreatedDate'

    if config == 'CVE':
        query_data = 'SELECT Account_Name__c,CaseNumber,CreatedDate,Id,OwnerId,Priority,Product_Level_Three__c,' \
                     'Product_Level_Two__c FROM Case WHERE (Subject LIKE \'%CVE-%\') AND (' + names + ') AND Product_Level_Two__c = \'Linux\' AND %s > %s' % (
                     string, time_t)
    elif config == 'NOCVE':
        query_data = 'SELECT Account_Name__c,CaseNumber,CreatedDate,Id,OwnerId,Priority,Product_Level_Three__c,' \
                     'Product_Level_Two__c FROM Case WHERE (NOT Subject LIKE \'%CVE-%\') AND (' + names + ') AND Product_Level_Two__c = \'Linux\' AND %s > %s' % (
                     string, time_t)
    else:
        query_data = 'SELECT Account_Name__c,CaseNumber,CreatedDate,Id,OwnerId,Priority,Product_Level_Three__c,' \
                     'Product_Level_Two__c FROM Case WHERE (' + names + ') AND Product_Level_Two__c = \'Linux\' AND %s > %s' % (
                     string, time_t)

    data = sf_ins.query_all_iter(query_data)
    headers = ["Account_Name__c", "CaseNumber", "CreatedDate", "Id", "OwnerId", "Priority", "Product_Level_Three__c",
               "Product_Level_Two__c"]
    count = 0
    with open(filename, mode='w') as csv_file_wr:
        csv_object = csv.writer(csv_file_wr, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_object.writerow(headers)
        for row in data:
            count += 1
            items = []
            for header in headers:
                if row[header]:
                    if header == "OwnerId":
                        items.append(_a_dict[row[header]])
                    else:
                        items.append(row[header])
                else:
                    items.append("empty")
            csv_object.writerow(items)

    print(str(count) + " case has been extracted and opened since " + str(days) + " ago")
    df_tmp = pd.read_csv(filename)

    return df_tmp['Id']


def init(sf_ins, config=None):
    _ = fetch_cases(sf_ins, 'CVE', 60, 'cve_open_cases.csv', 'CREATED')
    _ = fetch_cases(sf_ins, 'NOCVE', 60, 'open_cases.csv', 'CREATED')
    _ = fetch_cases(sf_ins, 'NOCVE', 60, 'closed_cases.csv', 'CLOSED')
    _ = fetch_surveys_inf(sf_ins, 60, 'surveys_info.csv')
