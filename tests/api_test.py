import sys
sys.path.append("/Users/jjones/dev/apps/blog_comments/")
sys.path.append("/Users/jjones/dev/apps/blog_comments/tests/")
import dynamodb_local_setup
import pytest
from comments_handler import Customer
from comments_handler import Comments
import comments_handler
import testConfig

postdata_incomplete = {'version': '2.0', 'routeKey': 'POST /comments', 'rawPath': '/prod/comments', 'rawQueryString': '', 'headers':{'accept': '*/*', 'accept-encoding': 'gzip, deflate, br', 'cache-control': 'no-cache', 'content-length': '118',
'content-type': 'application/json', 'host':'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'postman-token':
'dd3e119e-8d63-43e4-a29a-86dde86e4623', 'user-agent': 'PostmanRuntime/7.26.10', 'x-amzn-trace-id':'Root=1-604dd0a8-51b1da226dfd258457ab5ab5', 'x-forwarded-for': '86.12.192.198', 'x-forwarded-port': '443',
'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '428972862868', 'apiId': 'a490war5g1', 'domainName':'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'domainPrefix': 'a490war5g1', 'http': {'method': 'POST', 'path':'/prod/comments', 'protocol': 'HTTP/1.1', 'sourceIp': '86.12.192.198', 'userAgent': 'PostmanRuntime/7.26.10'},
'requestId': 'cK2KUiMGjoEEP9g=', 'routeKey': 'POST /comments', 'stage': 'prod', 'time': '14/Mar/2021:09:00:24 +0000','timeEpoch': 1615712424345}, 'body': '{"action":"new", "customer": "pauserun_test", "pageId":"AWS-Hammer", "comment":"this isnt a comment", "name": "jason"}', 'isBase64Encoded': False}

postdata_good = {'version': '2.0', 'routeKey': 'POST /comments', 'rawPath': '/prod/comments', 'rawQueryString': '', 'headers':{'accept': '*/*', 'accept-encoding': 'gzip, deflate, br', 'cache-control': 'no-cache', 'content-length': '118',
'content-type': 'application/json', 'host':'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'postman-token':
'dd3e119e-8d63-43e4-a29a-86dde86e4623', 'user-agent': 'PostmanRuntime/7.26.10', 'x-amzn-trace-id':'Root=1-604dd0a8-51b1da226dfd258457ab5ab5', 'x-forwarded-for': '86.12.192.198', 'x-forwarded-port': '443',
'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '428972862868', 'apiId': 'a490war5g1', 'domainName':'a490war5g1.execute-api.eu-west-1.amazonaws.com', 'domainPrefix': 'a490war5g1', 'http': {'method': 'POST', 'path':'/prod/comments', 'protocol': 'HTTP/1.1', 'sourceIp': '86.12.192.198', 'userAgent': 'PostmanRuntime/7.26.10'},
'requestId': 'cK2KUiMGjoEEP9g=', 'routeKey': 'POST /comments', 'stage': 'prod', 'time': '14/Mar/2021:09:00:24 +0000','timeEpoch': 1615712424345}, 'body': '{"action":"new", "customer": "pauserun_test", "author":"jason", "pageId":"AWS-Hammer", "comment":"this isnt a comment", "name": "jason"}', 'isBase64Encoded': False}

lambda_context = {"invoked_function_arn": "localtest"}

@pytest.fixture
def setup_customers():
    yield dynamodb_local_setup.set_up_customer(True)



def test_add_comment_good_data(setup_customers):
    cmt = Comments(setup_customers)
    pending = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    comments_handler.handler(postdata_good, lambda_context)
    new_pending = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    assert(len(new_pending) == len(pending) + 1)

def test_two_comments_same_author_one_addition(setup_customers):
    cmt = Comments(setup_customers)
    pending = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    comments_handler.handler(postdata_good, lambda_context)
    comments_handler.handler(postdata_good, lambda_context)
    new_pending = cmt.get_pending_comments(testConfig.CUSTOMER,testConfig.CUSTOMER_PW, testConfig.PAGEID)
    assert(len(new_pending) == len(pending))


