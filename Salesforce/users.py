import pandas as pd

def sf_user_id2alias(sf, UserID):
    case_list_query = "SELECT Alias FROM User WHERE Id = '%s'" % UserID
    user = sf.query_all(case_list_query)
    return user['records'][0]['Alias']


def sf_user_alias2id(sf, Alias):
    case_list_query = "SELECT Id FROM User WHERE Alias = '%s'" % Alias
    user = sf.query_all(case_list_query)
    if user['totalSize'] == 0:
        print('NO USER FOUND')
        exit(0)
    else:
        return user['records'][0]['Id']

def sf_user_name2id(sf, Name):
    case_list_query = "SELECT Id,ManagerId FROM User WHERE Name = '%s'" % Name
    user = sf.query_all(case_list_query)
    if user['totalSize'] == 0:
        return "FAIL", "FAIL"
    else:
        return user['records'][0]['Id'], user['records'][0]['ManagerId']


def sf_Contact_id2name(sf, Id):
    case_list_query = "SELECT Name FROM User WHERE Id = '%s'" % Id
    user = sf.query_all(case_list_query)
    if user['totalSize']:
        return user['records'][0]['Name']
    else:
        return Id

def sf_user_id2name(sf, Id):
    case_list_query = "SELECT Name FROM User WHERE Id = '%s'" % Id
    user = sf.query_all(case_list_query)
    if user['totalSize']:
        return user['records'][0]['Name']
    else:
        return "NOT_ASSIGNED"

def sf_user_id2email(sf, Id):
    case_list_query = "SELECT Email FROM User WHERE Id = '%s'" % Id
    user = sf.query_all(case_list_query)
    return user['records'][0]['Email']

def sf_user_id2title(sf, Id):
    case_list_query = "SELECT Title FROM User WHERE Id = '%s'" % Id
    user = sf.query_all(case_list_query)
    return user['records'][0]['Title']


def sf_user_translate(sf, From, select_item, item):
    case_list_query = "SELECT %s FROM User WHERE %s = '%s'" % (
        select_item, From, item)
    user = sf.query_all(case_list_query)
    return user['records'][0][select_item]


def sf_user_get_employees(sf, ManagerId):
    case_list_query = "SELECT Alias,Id FROM User WHERE ManagerId = '%s' AND IsActive = True" % ManagerId
    userlist = sf.query_all(case_list_query)
    options = []
    Ids = []
    managerAlias = sf_user_id2alias(sf, ManagerId)
    options.append(managerAlias)
    Ids.append(ManagerId)
    for con in userlist['records']:
        options.append(con['Alias'])
        Ids.append(con['Id'])
    zip_iterator = zip(options, Ids)
    zip2_iterator = zip(Ids, options)
    a_dict = dict(zip_iterator)
    b_dictionary = dict(zip2_iterator)
    return a_dict, b_dictionary

def get_all_dep_users(sf):
    user_list_query = "SELECT Id,Name FROM User WHERE (Department LIKE '%Support%' OR Department LIKE '%Licensing%' OR Department LIKE '%CSO%') AND IsActive = True AND (NOT Department LIKE '%CSP%') AND Email LIKE '%windriver%'"
    usr_list = sf.query_all(user_list_query)
    __dict__ = []       
    for con in usr_list['records']:
        __dict__.append({'Id': con['Id'], 'Name': con['Name']})
    
    return __dict__

def sf_case_get_ownerid(sf_ins, number):
    """ Get the case ID from Salesforce

    Attributes
    ----------
    sf_ins(Salesforce): This refers to salesforce object used by the request
    number(str) : Case number

    Returns
    -------
    str: Contact Name
    """
    case_list_query = "SELECT OwnerId FROM Case WHERE CaseNumber = '%s'" % number
    case_list = sf_ins.query_all(case_list_query)
    contact_name = sf_user_id2name(
        sf_ins, case_list['records'][0]['OwnerId'])
    return contact_name

def get_list_of_users(sf,verbose=False,isActive=True):

    keys = "Id,Name,Title,Email,ManagerId,Alias,Department,Country"
    __keys = keys.split(',')
    query = sf.query_all("SELECT {} FROM User WHERE Email LIKE '%windriver%' AND IsActive = {}".format(keys,isActive))

    dict_ = []
    for item in query['records']:
        __array__ = {}
        for key in __keys:
            __array__[key] = item[key]
        dict_.append(__array__)
    
    if verbose:
        print('review the file users.html to see the list of users')
        df = pd.DataFrame.from_dict(dict_)
        html = df.to_html(index=False)
        df.to_json('reports/users.json', orient='records', lines=True)
        with open("reports/users.html", "w") as f:
            f.write(html)
    return dict_               
        
def get_users_with_option(sf,option,verbose=False):
    ''' this will handle the request for all the users on the department 
    option can be 'man:<manager_alias>' or 'eng:<eng_alias> or cso (all department) ' 
    '''
    dict_user__ = get_list_of_users(sf)
    dict__ = []
    if "eng" in option:
        print('select only for one user')
        for user in dict_user__:
            if user['Alias'] == option.split(":")[1]:
                dict__.append({'Id': user['Id'], 'Name': user['Name']})
    elif "man" in option:
        print('select for multiple users and one manager')
        ''' get the id from the the manager'''
        rr = list(filter(lambda person: person['Alias'] == option.split(":")[1], dict_user__))
        manager_id = rr[0]['Id']
        for user in dict_user__:
            if user['ManagerId'] == manager_id:
                dict__.append({'Id': user['Id'], 'Name': user['Name']})
    elif "cso" == option:
        ### Department LIKE '%Support%' OR Department LIKE '%Licensing%' OR Department LIKE '%CSO%'
        for user in dict_user__:
            if user['Department'] is not None and ("Support" in user['Department'] or "Licensing" in user['Department'] or "CSO" in user['Department']):
                dict__.append({'Id': user['Id'], 'Name': user['Name']})
    elif "costarica" in option:
        ### Department LIKE '%Costa Rica%'
        for user in dict_user__:
            if (user['Department'] is not None and user['Country'] is not None) and "Costa Rica" in user['Country']:
                dict__.append({'Id': user['Id'], 'Name': user['Name']})
    elif "na" in option:
        ### Department LIKE '%Costa Rica%'
        for user in dict_user__:
            if user['Department'] is not None and ("Support" in user['Department'] or "Licensing" in user['Department'] or "CSO" in user['Department']) and "CSP" not in user['Department']:
                if (user['Department'] is not None and user['Country'] is not None) and ("Costa Rica" == user['Country'] or "United States" == user['Country'] or "Canada" == user['Country']):
                    dict__.append({'Id': user['Id'], 'Name': user['Name']})
    else: 
        dict__ = dict_user__
   
    return dict__