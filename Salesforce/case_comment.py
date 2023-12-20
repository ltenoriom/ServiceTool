import json
import logging

from Salesforce import case

visibilityPC = "InternalUsers"
visibilityPCA = "AllUsers"
# detailed information about how tom manage comments :
# https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_feed_element.htm


# change visibility visibility="InternalUsers" /visibility="AllUsers"
def post_comment(sf, number, text, type):
    logging.debug("Commenting on " + number)
    if type == "internal":
        visibility = "InternalUsers"
    elif type == "all":
        visibility = "AllUsers"
    else:
        print("Value is not correct... use all/internal")
        return -1

    logging.debug(text)
    try:
        case_id = case.sf_case_get_id(sf, number)
    except Exception as e:
        print((e))
        return None

    data = {
        "body": {
            "messageSegments": [
                {
                    "type": "Text",
                    "text": text
                }]
        },
        "feedElementType": "FeedItem",
        "subjectId": case_id,
        "visibility": visibility
    }
    url = (
        'https://{instance}/services/data/v42.0/chatter/feed-elements'.format(instance=sf.sf_instance))
    logging.debug(url)
    result = sf._call_salesforce('POST', url, data=json.dumps(data))
    return result

def get_comments(sf_ins, number):
    logging.debug("Commenting on " + number)
    case_id = case.sf_case_get_id(sf_ins, number)
    str_query = "SELECT Id, ContactId, OwnerId FROM Case WHERE Id = '%s'" % case_id
    case_qry1 = sf_ins.query_all(str_query)
    str_query = "SELECT Id, Body, CreatedById FROM CaseFeed WHERE ParentId = '%s' AND (Type = 'ContentPost' OR Type = 'TextPost')" % case_id
    case_qry = sf_ins.query_all(str_query)
    # create empty DF
    d_frame = None
    d_frame = pd.DataFrame(columns=['id', 'case_id', 'body',
                                'created_by_id', 'contactId',
                                'ownerId', 'createdDate'])

    for case1 in case_qry1['records']:
        contact_id = case1['ContactId']
        owner_id = case1['OwnerId']

    if case_qry['totalSize'] != 0:
        for comment in case_qry['records']:
            print(comment)
            comment_id = comment['Id']
            created_by_id = comment['CreatedById']
            thread = sf_ins.query_more(
                "/services/data/v48.0/chatter/feed-elements/" + comment_id, True)

            comment_thread = thread["body"]["text"]
            comment_thread_date = thread["createdDate"]
            comment_id_link = 'https://windriver.lightning.force.com/lightning/r/CaseFeed/{}/view'.format(comment_id)
            d_frame.loc[-1] = [comment_id_link, number, comment_thread, users.sf_user_id2name(sf_ins,created_by_id),
                            users.sf_Contact_id2name(sf_ins,contact_id), users.sf_user_id2name(sf_ins,owner_id), comment_thread_date]  # add a row
            d_frame.index = d_frame.index + 1  # shift index
            d_frame = d_frame.sort_index()  # sort by index

    print(d_frame['id'][0])
    print(d_frame['case_id'][0])
    print(d_frame['body'][0])
    print(d_frame['created_by_id'][0])
    print(d_frame['createdDate'][0])

    analyzer = SentimentIntensityAnalyzer()
    for sentence in d_frame['body']:
        vs = analyzer.polarity_scores(sentence)
        print("{:-<65} {}".format(sentence, str(vs)))

