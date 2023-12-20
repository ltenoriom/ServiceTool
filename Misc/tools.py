'''
Miscellaneous utilities
'''
from datetime import date
import re

from Salesforce.case import sf_case_get_report


JIRA_ISSUE_URL = 'https://jira.wrs.com/browse/'  # + DEFECT_ID
ERROR_RETURN = -1


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


def print_warning(text):
    print(bcolors.WARNING + text + bcolors.ENDC)


def print_failure(text):
    print(bcolors.FAIL + text + bcolors.ENDC)


def print_ok(text):
    print(bcolors.OKGREEN + text + bcolors.ENDC)


def is_not_blank(s):
    return bool(s and s.strip())


def print_cyan(text):
    print(bcolors.OKCYAN + text + bcolors.ENDC)


def print_item_value(item, value):
    print(bcolors.OKCYAN + item + bcolors.ENDC + ' : ' + value)


def print_list_no_spaces(field, list_object):
    """ This function will replace spaces and print to std output

    Attributes
    ----------
    field(field): Field to print
    list_object(list): List to iterate and print

    Returns
    -------
    str: String without spaces
    """
    result = None
    tmp = list_object[field]
    if list_object[field]:
        print(field + "content is : " + tmp.replace('\n', ' ').replace('\r', ''))
        result = tmp.replace('\n', ' ').replace('\r', '')
    else:
        print_failure(field + "content is : null")
    return result


def yes_or_no(question):
    while True:
        reply = str(input(question + ' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        elif reply[0] == 'n':
            return False
        else:
            print("Please Enter (y/n) ")


def isalist(ini_list1):
    if isinstance(ini_list1, list):
        return 0
    else:
        return -1


def CheckIFKeyAvailable(object, key):
    if key in object.keys():
        return True
    else:
        return False


def map_linux_version(map_value):
    if map_value == "Linux 6 - Legacy":
        map_value = "LIN6"
    elif map_value == "Linux 8 - Legacy":
        map_value = "LIN8"
    elif map_value == "Linux LTS 18":
        map_value = "LIN1018"
    else:
        map_value = "nothing"
        print("Something wrong with the linux version provided")
        exit()

    return map_value


def deltamodification(mydate):
    v = mydate.split('T')
    today = date.today()
    f_date = date(int(v[0].split('-')[0]),
                  int(v[0].split('-')[1]), int(v[0].split('-')[2]))
    l_date = date(int(today.strftime("%Y")), int(
        today.strftime("%m")), int(today.strftime("%d")))
    delta = l_date - f_date
    if int(delta.days) > 3:
        if int(delta.days) > 5:
            string = 'ALERT'
        else:
            string = 'WARNING'
    else:
        string = 'OKnow'
    return string + ' -- ' + str(delta.days) + ' days'


def dict2html(tbl, name, title):
    print("file " + name + " contains the results")
    cols = ["<td>{0}</td>".format("</td><td>".join(t)) for t in tbl]
    # then use it to join the rows (tr)
    rows = "<tr>{0}</tr>".format("</tr>\n<tr>".join(cols))
    # finalLy, inject it into the html...
    display = open(name, 'w')
    display.write(
        "<HTML><head><link rel=\"stylesheet\" href=\"style.css\"></head><body><h1>" + title +
        "</h1><table border = '1' align ='left'>{0}</table></body></HTML>".format(rows))


def add_html_tags2defect(defect_id):
    return "<a href=%s/%s>%s</a>" % (JIRA_ISSUE_URL, defect_id, defect_id)

# Python program to convert a list
# to string using join() function

# Function to convert


def translate_list2string(s):
    # initialize an empty string
    str1 = " "

    # return string
    return str1.join(s)

def is_text_commit_id(text):
    """ Check if the text contains only a commit ID hash

    The current implementation only checks for white spaces

    Attributes
    ----------
    text(String): Text to validate

    Returns
    -------
    Bool: True if only continous characters. False otherwise
    """
    return not bool(re.search(r"\s", text))
