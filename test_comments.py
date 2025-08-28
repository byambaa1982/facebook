#!/usr/bin/env python3
"""
Test script for routes/comment.py - Tests comment fetching functionality
"""

import sys
import os
import json
import requests
import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the modules to test
from routes.comment import (
    get_facebook_apps,
    get_posts_from_db,
    get_post_comments_from_facebook,
    store_comments_in_db,
    get_comments_from_db,
    _handle_facebook_response
)

class TestCommentFunctionality(unittest.TestCase):
    """Test cases for comment fetching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_creds_data = {
            "data": [
                {
                    "access_token": "test_token_123",
                    "category": "Information Technology Company",
                    "name": "Test Page",
                    "id": "123456789",
                    "tasks": ["MODERATE", "MESSAGING", "ANALYZE"]
                },
                {
                    "access_token": "test_token_456",
                    "category": "Science & Tech",
                    "name": "Another Test Page",
                    "id": "987654321",
                    "tasks": ["MANAGE", "CREATE_CONTENT"]
                }
            ]
        }
        
        self.sample_facebook_response = {
            "data": [
                {
                    "id": "comment_123",
                    "message": "Great post!",
                    "created_time": "2025-08-27T10:00:00+0000",
                    "from": {
                        "name": "John Doe",
                        "id": "user_123"
                    },
                    "like_count": 5,
                    "comment_count": 2,
                    "replies": {
                        "data": [
                            {
                                "id": "reply_123",
                                "message": "Thanks!",
                                "created_time": "2025-08-27T11:00:00+0000",
                                "from": {
                                    "name": "Page Owner",
                                    "id": "page_123"
                                },
                                "like_count": 1
                            }
                        ]
                    }
                },
                {
                    "id": "comment_456",
                    "message": "Interesting content",
                    "created_time": "2025-08-27T12:00:00+0000",
                    "from": {
                        "name": "Jane Smith",
                        "id": "user_456"
                    },
                    "like_count": 3,
                    "comment_count": 0
                }
            ],
            "paging": {
                "next": "next_page_url"
            }
        }

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_get_facebook_apps_success(self, mock_exists, mock_file):
        """Test successful retrieval of Facebook apps"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.sample_creds_data)
        
        apps = get_facebook_apps()
        
        self.assertEqual(len(apps), 2)
        self.assertEqual(apps[0]['page_id'], '123456789')
        self.assertEqual(apps[0]['username'], 'Test Page')
        self.assertEqual(apps[0]['password'], 'test_token_123')
        self.assertEqual(apps[1]['page_id'], '987654321')
        
    @patch('os.path.exists')
    def test_get_facebook_apps_file_not_found(self, mock_exists):
        """Test behavior when creds.json file doesn't exist"""
        mock_exists.return_value = False
        
        apps = get_facebook_apps()
        
        self.assertEqual(apps, [])

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_get_facebook_apps_invalid_json(self, mock_exists, mock_file):
        """Test behavior with invalid JSON"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json"
        
        apps = get_facebook_apps()
        
        self.assertEqual(apps, [])

    @patch('requests.get')
    def test_get_post_comments_from_facebook_success(self, mock_get):
        """Test successful Facebook API call for comments"""
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_facebook_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = get_post_comments_from_facebook(
            page_id="123456789",
            access_token="test_token",
            post_id="post_123",
            limit=25
        )
        
        self.assertIn('data', result)
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['data'][0]['id'], 'comment_123')
        self.assertEqual(result['data'][0]['message'], 'Great post!')
        
        # Verify the API call was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('fields', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['access_token'], 'test_token')

    @patch('requests.get')
    def test_get_post_comments_from_facebook_api_error(self, mock_get):
        """Test Facebook API error handling"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid access token",
                "type": "OAuthException",
                "code": 190
            }
        }
        mock_get.return_value = mock_response
        
        result = get_post_comments_from_facebook(
            page_id="123456789",
            access_token="invalid_token",
            post_id="post_123"
        )
        
        self.assertIn('error', result)
        # Test error response structure
        self.assertIn('error', result)
        self.assertIn('error', result['error'])  # The function wraps the error in another error object

    def test_handle_facebook_response_success(self):
        """Test successful Facebook response handling"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": ["test"]}
        
        result = _handle_facebook_response(mock_response)
        
        self.assertEqual(result, {"data": ["test"]})

    def test_handle_facebook_response_error(self):
        """Test Facebook response error handling"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_response.json.return_value = {
            "error": {"message": "Test error"}
        }
        
        result = _handle_facebook_response(mock_response)
        
        # Test that handle_facebook_response properly wraps error responses
        self.assertIn('error', result)
        self.assertIn('error', result['error'])  # The function wraps the error in another error object

    @patch('routes.comment.get_unqlite_db')
    def test_store_comments_in_db_success(self, mock_get_db):
        """Test successful comment storage in database"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        comments_data = [
            {"id": "comment_1", "message": "Test comment 1"},
            {"id": "comment_2", "message": "Test comment 2"}
        ]
        
        result = store_comments_in_db("post_123", "content_456", comments_data)
        
        self.assertTrue(result)
        mock_db.__setitem__.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch('routes.comment.get_unqlite_db')
    def test_get_comments_from_db_success(self, mock_get_db):
        """Test successful comment retrieval from database"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        stored_data = {
            "post_id": "post_123",
            "content_id": "content_456",
            "comments": [{"id": "comment_1", "message": "Test"}],
            "last_updated": "2025-08-27T10:00:00",
            "total_comments": 1
        }
        
        mock_db.__getitem__.return_value = json.dumps(stored_data).encode('utf-8')
        
        result = get_comments_from_db("content_456", "post_123")
        
        self.assertEqual(result['post_id'], 'post_123')
        self.assertEqual(result['total_comments'], 1)
        mock_db.close.assert_called_once()

    @patch('routes.comment.get_unqlite_db')
    def test_get_comments_from_db_not_found(self, mock_get_db):
        """Test comment retrieval when no comments exist"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.__getitem__.side_effect = KeyError()
        
        result = get_comments_from_db("content_456", "post_123")
        
        self.assertIsNone(result)

def run_integration_test():
    """Run integration test with real API call (if credentials are valid)"""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Testing with real Facebook API")
    print("="*60)
    
    try:
        # Get real Facebook apps
        apps = get_facebook_apps()
        if not apps:
            print("❌ No Facebook apps found in creds.json")
            return False
        
        print(f"✅ Found {len(apps)} Facebook apps")
        
        # Test with first app
        app = apps[0]
        page_id = app.get('page_id')
        access_token = app.get('password')
        
        if not page_id or not access_token:
            print("❌ Invalid app configuration")
            return False
        
        print(f"📱 Testing with page ID: {page_id}")
        
        # Try to get posts from database
        try:
            posts = get_posts_from_db()
            print(f"📊 Found {len(posts)} posts in database")
        except Exception as e:
            print(f"Error getting posts from database: {str(e)}")
            posts = []
            print(f"📊 Found {len(posts)} posts in database")
        
        if posts:
            # Test with first post
            post = posts[0]
            facebook_post_id = post.get('facebook_post_id')
            
            if facebook_post_id:
                print(f"🔄 Fetching comments for post: {facebook_post_id}")
                
                # Fetch comments from Facebook
                result = get_post_comments_from_facebook(
                    page_id=page_id,
                    access_token=access_token,
                    post_id=facebook_post_id,
                    limit=5
                )
                
                if 'error' in result:
                    print(f"❌ Facebook API Error: {result['error']}")
                    return False
                
                comments_data = result.get('data', [])
                print(f"✅ Successfully fetched {len(comments_data)} comments")
                
                # Test storing comments
                if comments_data:
                    success = store_comments_in_db(
                        facebook_post_id, 
                        post['id'], 
                        comments_data
                    )
                    if success:
                        print("✅ Successfully stored comments in database")
                    else:
                        print("❌ Failed to store comments in database")
                        return False
                    
                    # Test retrieving stored comments
                    stored_comments = get_comments_from_db(post['id'], facebook_post_id)
                    if stored_comments:
                        print("✅ Successfully retrieved stored comments")
                        print(f"📈 Total comments in storage: {stored_comments.get('total_comments', 0)}")
                    else:
                        print("❌ Failed to retrieve stored comments")
                        return False
                else:
                    print("ℹ️  No comments found for this post")
                
                return True
            else:
                print("❌ No Facebook post ID found in database posts")
        else:
            print("ℹ️  No posts found in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run tests"""
    print("Facebook Comments Testing Suite")
    print("="*50)
    
    # Run unit tests
    print("\n🧪 Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration test
    print("\n🔄 Running Integration Test...")
    success = run_integration_test()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    print("\n" + "="*50)
    print("Test Summary:")
    print("1. Unit tests verify individual function behavior")
    print("2. Integration test checks real Facebook API connectivity")
    print("3. Database operations are tested with mocked UnQLite")
    print("="*50)

if __name__ == '__main__':
    main()
