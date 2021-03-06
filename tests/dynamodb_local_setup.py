import os
import boto3
import hashlib
from boto3.dynamodb.types import Binary
import testConfig

dynamoLocation = 'Local'
# dynamoLocation = 'Remote'

def create_comments_table(dynamodb, table_name):
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'customer',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'pageId',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'customer',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'pageId',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

def create_customer_table(dynamodb, table_name):
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'customer',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'customer',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

def put_comments(dynamodb, table_name):

    table = dynamodb.Table(table_name)
    response = table.put_item(
       Item={
            "customer": testConfig.CUSTOMER,
            "pageId": testConfig.PAGEID,
            "comments": [
            {
            "status": "approved",
            "text": "This is approved",
            "commentId" : "ABC100"
            },
            {
            "status": "pending",
            "text": "This is pending",
            "commentId" : "ABC123"
            },
            {
            "status": "approved",
            "text": "This is also approved",
            "commentId" : "ABC101"
            },
            {
            "status": "rejected",
            "text": "This is rejected",
            "commentId" : "ABC102"
            }
            ]
            }
        
    )
    return response

def get_comments(dynamodb, table_name):
    try:
        comments_table = dynamodb.Table(table_name)
        comments = comments_table.get_item(Key={'customer': testConfig.CUSTOMER, 'pageId' : testConfig.PAGEID})
        if 'Item' in  comments:
            return comments['Item']['comments']
        else:
            return []
    except:
        raise Exception('cannot locate comments for customer / pageId combination')

def clear_comments(dynamodb, table_name):
    try:
        comments_table = dynamodb.Table(table_name)
        response = comments_table.delete_item(
            Key={
                'customer': testConfig.CUSTOMER, 
                'pageId' : testConfig.PAGEID
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
    else:
        return response

def clear_customers(dynamodb, table_name):
    try:
        customers_table = dynamodb.Table(table_name)
        response = customers_table.scan()
        for x in response['Items']:
            cust = x['customer']
            response = customers_table.delete_item(
                    Key={
                        'customer': cust
                    }
            )
    except:
        raise
    else:
        return response


def check_table(dynamodb, table_name):
    table = dynamodb.list_tables()
    if (table_name in table['TableNames']):
        return True
    else:
        return False

def set_up_comments():
    if dynamoLocation == 'Local':
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
        dynamodbclient = boto3.client('dynamodb', endpoint_url="http://localhost:8000")
    else:
        dynamodb = boto3.resource('dynamodb')
        dynamodbclient = boto3.client('dynamodb')

    if (check_table(dynamodbclient, 'blogComments') == False):
        comments_table = create_comments_table(dynamodb, 'blogComments')
        print("Table status:", comments_table.table_status)
        
    else:
        print("Table already created")
    
    cc = clear_comments(dynamodb, 'blogComments')
    print(cc)
    put_comments(dynamodb, 'blogComments')

    print(get_comments(dynamodb,'blogComments'))
    return dynamodb

def set_up_customer(addCustomer = False):
    tbl_name = 'blogCustomer'
    if dynamoLocation == 'Local':
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
        dynamodbclient = boto3.client('dynamodb', endpoint_url="http://localhost:8000")
    else:
        dynamodb = boto3.resource('dynamodb')
        dynamodbclient = boto3.client('dynamodb')

    if (check_table(dynamodbclient, tbl_name) == False):
        
        create_customer_table(dynamodb, tbl_name)
        print("Table created")
        
    else:
        print("customer table already created")
    
    clear_customers(dynamodb, tbl_name)
    if addCustomer:
        customer = testConfig.CUSTOMER
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256',testConfig.CUSTOMER_PW.encode('utf-8'),salt, 100000)
        try:
            customer_table = dynamodb.Table(tbl_name)
            response = customer_table.put_item(
                Item={
                    "customer": customer,
                    "key": Binary(key), 
                    "salt": Binary(salt)
                })
        except:
            raise
    return dynamodb

if __name__ == '__main__':
    set_up_comments()
    set_up_customer()