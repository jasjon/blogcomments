import sys
sys.path.append("/Users/jjones/dev/apps/blog_comments/")
sys.path.append("/Users/jjones/dev/apps/blog_comments/tests/")

import comments_handler
import boto3
import config

import dynamodb_local_setup


class Test_Comments:
    dynamodb = ''
    customer = 'pauserun_test'
    pageId = 'AWS-Hammer'

    @classmethod
    def setup_class(cls):
        cls.dynamodb = dynamodb_local_setup.set_up_tests()

    def test_4_comments_exist(self):
        dynamodb = self.dynamodb
        comments = comments_handler.get_all_comments(self.customer,self.pageId, dynamodb)
        assert (len(comments) == 4)

    def test_comment_does_not_exist_for_invalid_customer(self):
        dynamodb = self.dynamodb
        comments = comments_handler.get_all_comments('invalid_customer',self.pageId, dynamodb)
        assert (len(comments) ==  0)

    def test_status_approved(self):
        dynamodb = self.dynamodb
        comments = comments_handler.get_approved_comments(self.customer,self.pageId, dynamodb)
        assert (len(comments) ==  2)

    def test_status_pending(self):
        dynamodb = self.dynamodb
        comments = comments_handler.get_pending_comments(self.customer,self.pageId, dynamodb)
        assert (len(comments) ==  1)

    def test_status_rejected(self):
        dynamodb = self.dynamodb
        comments = comments_handler.get_rejected_comments(self.customer,self.pageId, dynamodb)
        assert (len(comments) ==  1)
    
    def test_add_new_comment(self):
        dynamodb = self.dynamodb
        commentId = comments_handler.add_new_comment(self.customer, self.pageId, 'a new author', 'some sample text', dynamodb)
        assert(len(commentId) == 32)
        pending_comments = comments_handler.get_pending_comments(self.customer,self.pageId,dynamodb)
        assert(len(pending_comments) == 2)

    def test_get_comment_byId(self):
        dynamodb = self.dynamodb
        pendingComment = comments_handler.get_commentbyId(self.customer, self.pageId, 'ABC123', dynamodb)
        assert(pendingComment['status'] == 'pending')

    def test_approve_comment(self):
        dynamodb = self.dynamodb
        commentId = comments_handler.add_new_comment(self.customer, self.pageId, 'a new author', 'some sample text', dynamodb)
        comments_handler.approve_comment(self.customer, self.pageId, commentId, dynamodb)
        updated_comment = comments_handler.get_commentbyId(self.customer, self.pageId, commentId, dynamodb)
        assert(updated_comment['status'] == 'approved')


# def test_one():
#     dynamodb = boto3.resource('dynamodb')
#     comments = comments_handler.get_translation('pauserun_test','AWS-Hammer',dynamodb)
#     assert (len(comments['text']) >  10)
    