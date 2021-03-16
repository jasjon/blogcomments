import sys
sys.path.append("/Users/jjones/dev/apps/blog_comments/")
sys.path.append("/Users/jjones/dev/apps/blog_comments/tests/")
import dynamodb_local_setup
import pytest
from comments_handler import Customer
from comments_handler import Comments
import comments_handler
import testConfig
import json

class lambda_context:
    invoked_function_arn = 'local'
    # invoked_function_arn = ''

def get_post_data(type_of_body):
    postdata = {'version': '2.0', 'routeKey': 'POST /comments', 'rawPath': '/prod/comments', 'rawQueryString': '', 'headers':{'accept': '*/*', 'accept-encoding': 'gzip, deflate, br', 'cache-control': 'no-cache', 'content-length': '118',
    'content-type': 'application/json', 'host':'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'postman-token': 'dd3e119e-8d63-43e4-a29a-86dde86e4623', 'user-agent': 'PostmanRuntime/7.26.10', 'x-amzn-trace-id':'Root=1-604dd0a8-51b1da226dfd258457ab5ab5', 'x-forwarded-for': '86.12.192.198', 'x-forwarded-port': '443',
    'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '428972862868', 'apiId': 'a490war5g1', 'domainName':'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'domainPrefix': 'a490war5g1', 'http': {'method': 'POST', 'path':'/prod/comments', 'protocol': 'HTTP/1.1', 'sourceIp': '86.12.192.198', 'userAgent': 'PostmanRuntime/7.26.10'},
    'requestId': 'cK2KUiMGjoEEP9g=', 'routeKey': 'POST /comments', 'stage': 'prod', 'time': '14/Mar/2021:09:00:24 +0000','timeEpoch': 1615712424345}, 'isBase64Encoded': False}

    if (type_of_body == 'bad'):
        postdata['body'] = '{"action":"new", "customer": "pauserun_test", "pageId":"AWS-Hammer", "comment":"this isnt a comment", "name": "jason"}'
    elif (type_of_body == 'good'):
        postdata['body'] = '{"action":"new", "customer": "pauserun_test", "author":"jason", "pageId":"AWS-Hammer", "comment":"this isnt a comment", "name": "jason"}'

    return postdata

def get_get_data(customer,pageId, path='comments', password = None):
    getdata = {'version': '2.0', 'routeKey': 'GET /' + path, 'rawPath': '/prod/' + path, 'rawQueryString': 'customer=rigur',
        'headers': {'accept': '*/*', 'accept-encoding': 'gzip, deflate, br', 'cache-control': 'no-cache', 'content-length': '0',
        'host': 'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'postman-token': 'da3cfdb2-a395-4636-a8f8-6923e937227d',
        'user-agent': 'PostmanRuntime/7.26.10', 'x-amzn-trace-id': 'Root=1-604cb0d0-311668de7bf5ef471fbd282f',
        'x-forwarded-for': '86.12.192.198', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '428972862868', 'apiId': 'a490war5g1', 'domainName':
        'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'domainPrefix': 'a490war5g1', 'http': {'method': 'GET', 'path':
        '/prod/' + path, 'protocol': 'HTTP/1.1', 'sourceIp': '86.12.192.198', 'userAgent': 'PostmanRuntime/7.26.10'},
        'requestId': 'cICQlhexDoEEP3Q=', 'routeKey': 'GET /' + path, 'stage': 'prod', 'time': '13/Mar/2021:12:32:16 +0000',
        'timeEpoch': 1615638736410}, 'isBase64Encoded': False} 

    getdata['queryStringParameters'] = {'customer': customer, 'pageId': pageId}
    if (password):
        getdata['queryStringParameters'] = {'customer': customer, 'pageId': pageId, 'pw': password}
    return getdata

lc = lambda_context

@pytest.fixture
def setup_cts_and_cst():
    dynamodb = dynamodb_local_setup.set_up_customer(True)
    dynamodb_local_setup.set_up_comments()
    yield dynamodb


def test_add_comment_good_data(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    pending,passwordOK = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    comments_handler.handler(get_post_data('good'), lc)
    new_pending, passwordOK = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    assert(len(new_pending) == len(pending) + 1)

def test_two_comments_same_author_one_addition(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    pending, passwordOK = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    response = comments_handler.handler(get_post_data('good'), lc)
    assert(response['statusCode'] == 200)
    response = comments_handler.handler(get_post_data('good'), lc)
    assert(response['statusCode'] == 200)
    new_pending, passwordOK = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    assert(len(new_pending) == len(pending) + 1)

def test_get_comments_page_does_not_exist(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    getdata = get_get_data(testConfig.CUSTOMER, 'nonon')
    response = comments_handler.handler(getdata, lc)
    assert(response['statusCode'] == 200)
    comments = json.loads(response['body'])
    assert(len(comments) == 0)

def test_get_comments_good_page(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    getdata = get_get_data(testConfig.CUSTOMER, testConfig.PAGEID)
    response = comments_handler.handler(getdata, lc)
    assert(response['statusCode'] == 200)
    comments = json.loads(response['body'])
    assert(len(comments) == 2)

def test_get_comments_no_customer_no_page(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    getdata = get_get_data('nonon', 'nonon')
    response = comments_handler.handler(getdata, lc)
    assert(response['statusCode'] == 200)
    comments = json.loads(response['body'])
    assert(len(comments) == 0)
    
def test_get_pending_comments_bad_pw(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    getdata = get_get_data('nonon', 'nonon', 'pending', testConfig.CUSTOMER_PW)
    response = comments_handler.handler(getdata, lc)
    assert(response['statusCode'] == 401)
    comments = json.loads(response['body'])
    assert(len(comments) == 0)

def test_get_pending_comments_good_pw(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    getdata = get_get_data(testConfig.CUSTOMER, testConfig.PAGEID, 'pending', testConfig.CUSTOMER_PW)
    response = comments_handler.handler(getdata, lc)
    assert(response['statusCode'] == 200)
    comments = json.loads(response['body'])
    assert(len(comments) == 1)

def test_get_pending_comments_invalid_page(setup_cts_and_cst):
    cmt = Comments(setup_cts_and_cst)
    getdata = get_get_data(testConfig.CUSTOMER, 'nnnn', 'pending', testConfig.CUSTOMER_PW)
    response = comments_handler.handler(getdata, lc)
    assert(response['statusCode'] == 200)
    comments = json.loads(response['body'])
    assert(len(comments) == 0)

