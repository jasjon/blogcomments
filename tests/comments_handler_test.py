import sys
sys.path.append("/Users/jjones/dev/apps/blog_comments/")
sys.path.append("/Users/jjones/dev/apps/blog_comments/tests/")

from comments_handler import Customer
from comments_handler import Comments
import boto3
import config
import os

import dynamodb_local_setup

class Test_Customer:
    dynamodb = ''

    @classmethod
    def setup_class(cls):
        cls.dynamodb = dynamodb_local_setup.set_up_customer()

    def test_cant_recreate_same_customer(self):
        dynamodb_local_setup.clear_customers(self.dynamodb, 'blogCustomer')
        customer = 'pauserun_test'
        password = "".join(map(chr, os.urandom(32)))
        
        cust = Customer(self.dynamodb)
        customer_create = cust.create_customer(customer, password)
        assert(customer_create)
        #now, try to create with the same, name, diff password
        password = "".join(map(chr, os.urandom(32)))
        customer_create = cust.create_customer(customer, password)
        assert(customer_create == False)
       
    def test_create_customer(self):
        dynamodb_local_setup.clear_customers(self.dynamodb, 'blogCustomer')
        customer1 = 'pauserun_test'
        customer2 = 'pauserun_test2'
        password = "".join(map(chr, os.urandom(32)))
        password2 = "".join(map(chr, os.urandom(32)))

        cust = Customer(self.dynamodb)

        customer_create = cust.create_customer(customer1, password)
        customer_create2 = cust.create_customer(customer2, password2)
        assert(customer_create)
        
        
        pw_check = cust.validate_customer_password(customer1, password)
        pw_check2 = cust.validate_customer_password(customer2, password2)
        assert(pw_check)
        assert(pw_check2)
        
        # wrong password for customer should return false
        pw_check3 = cust.validate_customer_password(customer1, "not the password")
        assert(pw_check3 == False)


class Test_Comments:
    dynamodb = ''
    customer = 'pauserun_test'
    customer_password = 'secretPa$$word'
    pageId = 'AWS-Hammer'
    cts = ''

    @classmethod
    def setup_class(self):
        self.dynamodb = dynamodb_local_setup.set_up_comments()
        dynamodb_local_setup.set_up_customer()
        self.cts = Comments(self.dynamodb)
        cust = Customer(self.dynamodb)
        customer_create = cust.create_customer(self.customer, self.customer_password)

    def test_4_comments_exist(self):
        comments = self.cts.get_all_comments(self.customer, self.customer_password, self.pageId)
        assert (len(comments) == 4)

    def test_comment_does_not_exist_for_invalid_customer(self):
        comments = self.cts.get_all_comments('invalid_customer','wrong pw', self.pageId)
        assert (len(comments) ==  0)

    def test_status_approved(self):
        comments = self.cts.get_approved_comments(self.customer,self.pageId)
        assert (len(comments) ==  2)

    def test_status_pending(self):
        comments = self.cts.get_pending_comments(self.customer, self.customer_password, self.pageId)
        assert (len(comments) ==  1)

    def test_status_rejected(self):
        comments = self.cts.get_rejected_comments(self.customer,self.customer_password,self.pageId)
        assert (len(comments) ==  1)
    
    def test_add_new_comment(self):
        commentId = self.cts.add_new_comment(self.customer, self.pageId, 'a new author', 'some sample text')
        assert(len(commentId) == 32)
        pending_comments = self.cts.get_pending_comments(self.customer,self.customer_password,self.pageId)
        assert(len(pending_comments) == 2)

    def test_get_comment_byId(self):
        pendingComment = self.cts.get_commentbyId(self.customer, self.pageId, 'ABC123')
        assert(pendingComment['status'] == 'pending')

    def test_approve_comment(self):
        commentId = self.cts.add_new_comment(self.customer, self.pageId, 'a new author', 'some sample text')
        self.cts.approve_comment(self.customer, self.pageId, commentId)
        updated_comment = self.cts.get_commentbyId(self.customer, self.pageId, commentId)
        assert(updated_comment['status'] == 'approved')


# def test_one():
#     dynamodb = boto3.resource('dynamodb')
#     comments = comments_handler.get_translation('pauserun_test','AWS-Hammer',dynamodb)
#     assert (len(comments['text']) >  10)
    