#!/usr/bin/env python3
"""
Flask Route Testing for routes/comment.py
Tests the Flask API endpoints for comment functionality
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_login import LoginManager
from db.models import User
from routes.comment import bp_comment

class TestCommentRoutes(unittest.TestCase):
    """Test cases for comment routes"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Set up Flask-Login
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        
        @self.login_manager.user_loader
        def load_user(user_id):
            # Mock user loader for testing
            user = MagicMock()
            user.id = user_id
            user.is_authenticated = True
            user.role = MagicMock()
            user.role.name = 'admin'
            return user
        
        # Register the blueprint
        self.app.register_blueprint(bp_comment)
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()

    def login_as_admin(self):
        """Helper to simulate admin login"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True

    @patch('routes.comment.get_posts_from_db')
    def test_list_posted_content_success(self, mock_get_posts):
        """Test successful retrieval of posted content"""
        self.login_as_admin()
        
        mock_posts = [
            {
                'id': 'content_1',
                'title': 'Test Post 1',
                'facebook_post_id': 'fb_post_1',
                'posted_to_page': 'page_123'
            },
            {
                'id': 'content_2', 
                'title': 'Test Post 2',
                'facebook_post_id': 'fb_post_2',
                'posted_to_page': 'page_456'
            }
        ]
        mock_get_posts.return_value = mock_posts
        
        response = self.client.get('/admin-panel/api/posts')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['posts']), 2)
        self.assertEqual(data['count'], 2)

    def test_list_posted_content_unauthorized(self):
        """Test unauthorized access to posted content"""
        response = self.client.get('/admin-panel/api/posts')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Authentication required', data['error'])

    @patch('routes.comment.get_facebook_apps')
    @patch('routes.comment.get_post_comments_from_facebook')
    @patch('routes.comment.store_comments_in_db')
    def test_fetch_comments_success(self, mock_store, mock_fetch_comments, mock_get_apps):
        """Test successful comment fetching from Facebook"""
        self.login_as_admin()
        
        # Mock Facebook apps
        mock_get_apps.return_value = [
            {
                'page_id': 'page_123',
                'username': 'Test Page',
                'password': 'test_token_123'
            }
        ]
        
        # Mock Facebook API response
        mock_fetch_comments.return_value = {
            'data': [
                {
                    'id': 'comment_1',
                    'message': 'Great post!',
                    'created_time': '2025-08-27T10:00:00+0000'
                }
            ]
        }
        
        # Mock successful storage
        mock_store.return_value = True
        
        response = self.client.post(
            '/admin-panel/api/content/content_123/comments/fetch',
            json={
                'page_id': 'page_123',
                'post_id': 'fb_post_123',
                'limit': 25
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['comments_count'], 1)
        self.assertIn('comments', data)

    def test_fetch_comments_missing_data(self):
        """Test comment fetching with missing required data"""
        self.login_as_admin()
        
        response = self.client.post(
            '/admin-panel/api/content/content_123/comments/fetch',
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Page ID and Post ID are required', data['error'])

    @patch('routes.comment.get_facebook_apps')
    def test_fetch_comments_app_not_found(self, mock_get_apps):
        """Test comment fetching when Facebook app is not found"""
        self.login_as_admin()
        
        mock_get_apps.return_value = []
        
        response = self.client.post(
            '/admin-panel/api/content/content_123/comments/fetch',
            json={
                'page_id': 'nonexistent_page',
                'post_id': 'fb_post_123'
            }
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Facebook app not found', data['error'])

    @patch('routes.comment.get_comments_from_db')
    def test_get_stored_comments_success(self, mock_get_comments):
        """Test successful retrieval of stored comments"""
        self.login_as_admin()
        
        mock_get_comments.return_value = {
            'post_id': 'fb_post_123',
            'content_id': 'content_123',
            'comments': [
                {'id': 'comment_1', 'message': 'Test comment'}
            ],
            'total_comments': 1
        }
        
        response = self.client.get('/admin-panel/api/content/content_123/comments')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_comments'], 1)

    @patch('routes.comment.get_comments_from_db')
    def test_get_stored_comments_not_found(self, mock_get_comments):
        """Test retrieval when no comments are found"""
        self.login_as_admin()
        
        mock_get_comments.return_value = None
        
        response = self.client.get('/admin-panel/api/content/content_123/comments')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('No comments found', data['error'])

    @patch('routes.comment.get_posts_from_db')
    @patch('routes.comment.get_facebook_apps')
    @patch('routes.comment.get_post_comments_from_facebook')
    @patch('routes.comment.store_comments_in_db')
    def test_bulk_fetch_comments_success(self, mock_store, mock_fetch, mock_get_apps, mock_get_posts):
        """Test successful bulk comment fetching"""
        self.login_as_admin()
        
        # Mock posts
        mock_get_posts.return_value = [
            {
                'id': 'content_1',
                'facebook_post_id': 'fb_post_1',
                'posted_to_page': 'page_123'
            }
        ]
        
        # Mock apps
        mock_get_apps.return_value = [
            {
                'page_id': 'page_123',
                'password': 'test_token'
            }
        ]
        
        # Mock Facebook response
        mock_fetch.return_value = {
            'data': [{'id': 'comment_1', 'message': 'Test'}]
        }
        
        # Mock storage
        mock_store.return_value = True
        
        response = self.client.post('/admin-panel/api/comments/bulk-fetch')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['successful_fetches'], 1)

def run_route_tests():
    """Run the route tests"""
    print("\n" + "="*60)
    print("FLASK ROUTE TESTS: Testing comment API endpoints")
    print("="*60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCommentRoutes)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All route tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False

if __name__ == '__main__':
    run_route_tests()
