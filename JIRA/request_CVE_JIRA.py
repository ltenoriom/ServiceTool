import csv
import getpass
import requests
from requests.auth import HTTPBasicAuth

files = "cves.csv"


def parseCSV(fileName):
    cveList = []
    with open(fileName) as f:
        reader = csv.reader(f, delimiter=",")
        for i in reader:
            cveList.append(i[0])
    # print(cveList)
    return cveList


def getRequest(user, password, url, cve):
    # Request for LTS18
    data = {"jql": "project = LIN9 AND text ~ \"" +
            str(cve)+"\"", "startAt": 0, "maxResults": 1, "fields": ["comment", "summary"]}
    # Sending get request and saving the response as response object
    r = requests.get(url=url, auth=HTTPBasicAuth(user, password), params=data)
    # Extracting data in json format
    data = r.json()
    # First we search if there are issues in LTS18
    if(data['issues'] != []):
        version = "LIN9"
        summary = data['issues'][0]['fields']['summary']
        summary = summary.split(' - ')[1]
        # If case does not have comments
        if(data['issues'][0]['fields']['comment']['comments'] == []):
            comment = "No comments."
        # If it does, attach the comment.
        else:
            comment = data['issues'][0]['fields']['comment']['comments'][0]['body']

    # If it is not in LTS18 we search in LTS17
    else:
        # Request for LTS17
        data = {"jql": "project = LIN8 AND text ~ \"" +
                str(cve)+"\"", "startAt": 0, "maxResults": 1, "fields": ["comment", "summary"]}
        # Sending get request and saving the response as response object
        r = requests.get(url=url, auth=HTTPBasicAuth(
            user, password), params=data)
        # Extracting data in json format
        data = r.json()
        # Now we search if there are issues in LTS17
        if(data['issues'] != []):
            version = "LIN8"
            summary = data['issues'][0]['fields']['summary']
            summary = summary.split(' - ')[1]
            # If case does not have comments
            if(data['issues'][0]['fields']['comment']['comments'] == []):
                comment = "No comments."
            # If it does, attach the comment.
            else:
                comment = data['issues'][0]['fields']['comment']['comments'][0]['body']
        # There are no issue for Linux 10
        else:
            comment = "Not in DB."
            summary = ""
            version = "none"
            print("Not found in Linux 10.")
    return [comment, summary, version]


notVulnerableCommentList = [
    "Not supported", "Closed by wrj:\n\nNot whitelisted", "Not in whitelist"]


def interpretComment(comment):
    if(notVulnerableCommentList.count(comment) > 0 or str(comment[:6]) == "ERROR:"):
        return "Not Vulnerable"
    else:
        return "Needs Revision"


def main():
    url = "http://jira.wrs.com:8080/rest/api/2/search"
    username = input("Username: ")
    password = getpass.getpass(prompt='Password: ')
    files = "NIDB.csv"
    cveList = parseCSV(files)
    commentList = []
    # for i in cveList:
    with open('statusNIDB.csv', 'w', newline='') as file:
        fieldnames = ['CVE', 'Version', 'Package', 'Status', 'Comment']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(0, len(cveList)):
            commentList.append(getRequest(username, password, url, cveList[i]))
            writer.writerow({'CVE': cveList[i], 'Version': commentList[i][2], 'Package': commentList[i][1], 'Status': interpretComment(
                str(commentList[i][0])), 'Comment': str(commentList[i][0])})
            print("CVE: "+str(cveList[i])+" Version: "+commentList[i][2]+" Package: "+str(commentList[i][1]) +
                  " Status: "+interpretComment(str(commentList[i][0]))+" Comment: "+str(commentList[i][0]))

    # print(commentList)


main()
