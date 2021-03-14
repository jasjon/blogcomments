import config
import boto3
from boto3.dynamodb.types import Binary
import uuid
import os
import hashlib
from base64 import b64encode
import json

def handler(event, context):
    try:
        action = event['requestContext']['http']['path'].split('/')[-1:][0]
        method = event['requestContext']['http']['method']
            
        if action == 'comments':
            if method == 'GET':
                customerId = event['queryStringParameters']['customer']
                pageId = event['queryStringParameters']['pageId']
                cts = Comments()
                if context['invoked_function_arn'] == 'localtest':
                    cts = Comments(boto3.resource('dynamodb', endpoint_url="http://localhost:8000"))
                comments = c.get_approved_comments(customerId, pageId)
                return {'statusCode': 200,'headers': {'Content-Type': 'text/html'},'body': comments}
                        
            elif method == 'POST':
                body = json.loads(event['body'])
                action = body['action']
                if action == 'new':
                    customer = body.get('customer')
                    pageId = body.get('pageId')
                    author = body.get('author', 'Anon')
                    comment = body.get('comment')
                    if (customer == None or pageId ==None or comment ==None):
                        raise 'Missing, customer, pageId or comment'
                    cts = Comments()
                    if context['invoked_function_arn'] == 'localtest':
                        cts = Comments(boto3.resource('dynamodb', endpoint_url="http://localhost:8000"))
                    new_comment_id = False
                    new_comment_id = cts.add_new_comment(customer,pageId,author,comment)                    
                    if new_comment_id:
                        #comment saved sucessfully
                        return {'statusCode': 200,'headers': {'Content-Type': 'text/html'},'body': comment}
                    else:
                        return {'statusCode': 500,'headers': {'Content-Type': 'text/html'},'body': comment}


    except Exception as e:
        return {'statusCode': 500,'headers': {'Content-Type': 'text/html'},'body': 'Error during processing' + str(e)}

        



class Comments:
    dynamodb = ''

    def __init__(self, dynamodb = boto3.resource('dynamodb')): 
        self.dynamodb = dynamodb

    def _get_comments(self, customer, pageId):
        try:
            comments_table = self.dynamodb.Table(config.COMMENTS_TABLE_NAME)
            comments = comments_table.get_item(Key={'customer': customer, 'pageId' : pageId})
            if 'Item' in  comments:
                return comments['Item']['comments']
            else:
                return []
        except:
            raise Exception('cannot locate comments for customer / pageId combination')

    def _get_comment_by_status(self, customer, pageId, status):
        try:
            comments = self._get_comments(customer,pageId)
            if (status == 'all'):
                return comments
            if len(comments) > 0:
                return list(filter(lambda x: x['status'] == status, comments))
            else:
                return []
        except:
            raise Exception('cannot locate comments for customer / pageId combination')

    def get_approved_comments(self, customer, pageId):
        #no password needed here.
        return self._get_comment_by_status(customer,pageId,'approved')

    def get_pending_comments(self, customer, customer_password, pageId):
        cust = Customer(self.dynamodb)
        if cust.validate_customer_password(customer, customer_password):
            return self._get_comment_by_status(customer,pageId,'pending')
        else:
            return []

    def get_rejected_comments(self, customer, customer_password,pageId):
        cust = Customer(self.dynamodb)
        if cust.validate_customer_password(customer, customer_password):
            return self._get_comment_by_status(customer,pageId,'rejected')
        else:
            return []

    def get_all_comments(self, customer, customer_password,pageId):
        cust = Customer(self.dynamodb)
        if cust.validate_customer_password(customer, customer_password):
            return self._get_comment_by_status(customer,pageId,'all')
        else:
            return []

    def add_new_comment(self, customer, pageId, author, comment_text):
        try:
            comments_table = self.dynamodb.Table(config.COMMENTS_TABLE_NAME)
            comments = self._get_comment_by_status(customer,pageId,'all')
            new_commentId = uuid.uuid4().hex
            new_item = {"status": "pending", "text": comment_text,"author" :author,"commentId": new_commentId}
            #is there a pending comment for the same customer, pageId,author combo?
            existing_comments = list(filter(
                                    lambda x: (
                                        x.get('status', 'pending') == 'pending' and 
                                        x.get('author','Anon') == author), 
                                        comments))
            if len(existing_comments )> 1:
                raise 'more than 1 existing commment for given author'
            if len(existing_comments) == 1:
                #replace the comment
                for index, item in enumerate(comments):
                    if (item.get('status', 'pending') == 'pending' and item.get('author','Anon') == author):
                        comments[index] = new_item
            else:
                #add in new comment
                comments.append(new_item)
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

        except Exception as e:
            raise e
        else:
            if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
                return new_commentId
            else:
                return ''

    def get_commentbyId(self, customer,pageId,commentId):
        all_comments = self._get_comment_by_status(customer,pageId,'all')
        targetComments = [x for x in all_comments if x['commentId'] == commentId]
        if (len(targetComments)==1):
            return targetComments[0]
        else:
            return {}

    def approve_comment(self, customer, pageId, commentId):
        try:
            comments_table = self.dynamodb.Table(config.COMMENTS_TABLE_NAME)
            comments = self._get_comment_by_status(customer,pageId,'all')
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

class Customer:
    dynamodb = ''

    def __init__(self, dynamodb = boto3.resource('dynamodb')): 
        self.dynamodb = dynamodb

    def create_customer(self, customer, customer_password):
        ctr = self._get_customer(customer)
        if ('Item' in ctr):
            #we already have a customer with that name and we can't re-create
            return False
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256',customer_password.encode('utf-8'),salt, 100000)
        try:
            customer_table = self.dynamodb.Table(config.CUSTOMER_TABLE_NAME)
            response = customer_table.put_item(
                Item={
                    "customer": customer,
                    "key": Binary(key), 
                    "salt": Binary(salt)
                })
        except:
            raise
        else:
            if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
                return True
            else:
                return False

    def validate_customer_password(self, customer, customer_password):
        key_from_storage, salt_from_storage = self.get_customer_stored_key_salt(customer)
        try:
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                customer_password.encode('utf-8'), # Convert the password to bytes
                salt_from_storage, 
                100000
            )
        except Exception as e:
            return False

        if new_key == key_from_storage:
            return True
        else:
            return False

    def get_customer_stored_key_salt(self, customer):
        try:
            ctr = self._get_customer(customer)
            if 'Item' in  ctr:
                key = ctr['Item']['key'].value
                salt = ctr['Item']['salt'].value
                return key,salt
            else:
                return b'', b''
        except:
            raise Exception('cannot locate comments for customer / pageId combination')

    def _get_customer(self, customer):
        try:
            customer_table = self.dynamodb.Table(config.CUSTOMER_TABLE_NAME)
            ctr = customer_table.get_item(Key={'customer': customer})
            if (ctr):
                return ctr
            else:
                return null
        except:
            raise
            
