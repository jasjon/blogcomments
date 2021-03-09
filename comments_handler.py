import config
import boto3
import uuid


def _get_comments(customer, pageId, dynamodb):
    try:
        comments_table = dynamodb.Table(config.COMMENTS_TABLE_NAME)
        comments = comments_table.get_item(Key={'customer': customer, 'pageId' : pageId})
        if 'Item' in  comments:
            return comments['Item']['comments']
        else:
            return []
    except:
        raise Exception('cannot locate comments for customer / pageId combination')

def _get_comment_by_status(customer, pageId, status, dynamodb):
    try:
        comments = _get_comments(customer,pageId,dynamodb)
        if (status == 'all'):
            return comments
        if len(comments) > 0:
            return list(filter(lambda x: x['status'] == status, comments))
        else:
            return []
    except:
        raise Exception('cannot locate comments for customer / pageId combination')

def get_approved_comments(customer, pageId, dynamodb):
    return _get_comment_by_status(customer,pageId,'approved',dynamodb)
def get_pending_comments(customer, pageId, dynamodb):
    return _get_comment_by_status(customer,pageId,'pending',dynamodb)
def get_rejected_comments(customer, pageId, dynamodb):
    return _get_comment_by_status(customer,pageId,'rejected',dynamodb)
def get_all_comments(customer, pageId, dynamodb):
    return _get_comment_by_status(customer,pageId,'all',dynamodb)

def add_new_comment(customer, pageId, author, comment_text, dynamodb):
    try:
        comments_table = dynamodb.Table(config.COMMENTS_TABLE_NAME)
        comments = get_all_comments(customer,pageId, dynamodb)
        #add in new comment
        new_commentId = uuid.uuid4().hex
        comments.append({
            "status": "pending",
            "text": comment_text,
            "author" :author,
            "commentId": new_commentId
        })
        response = comments_table.update_item(
            Key={
                'customer': customer,
                'pageId': pageId
            },
            UpdateExpression="set comments=:c",
            ExpressionAttributeValues={
                ':c': comments
            },
            ReturnValues="UPDATED_NEW"
        )

    except:
        raise
    else:
        if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
            return new_commentId
        else:
            return ''

def get_commentbyId(customer,pageId,commentId,dynamodb):
    all_comments = get_all_comments(customer,pageId,dynamodb)
    targetComments = [x for x in all_comments if x['commentId'] == commentId]
    if (len(targetComments)==1):
        return targetComments[0]
    else:
        return {}

def approve_comment(customer, pageId, commentId, dynamodb):
    try:
        comments_table = dynamodb.Table(config.COMMENTS_TABLE_NAME)
        comments = get_all_comments(customer,pageId, dynamodb)
        #approve_pending comment
        for d in comments:
            if (d['commentId'] == commentId):
                d['status'] = "approved"
        response = comments_table.update_item(
            Key={
                'customer': customer,
                'pageId': pageId
            },
            UpdateExpression="set comments=:c",
            ExpressionAttributeValues={
                ':c': comments
            },
            ReturnValues="UPDATED_NEW"
        )

    except:
        raise
    else:
        if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
            return True
        else:
            return False

