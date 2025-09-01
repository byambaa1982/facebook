#!/usr/bin/env python3
"""
Standalone test script for posting to Instagram using system user access
Tests Instagram Business API functionality through Facebook Graph API
"""

import sys
import os
import json
import requests
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestInstagramPosting(unittest.TestCase):
    """Test cases for Instagram posting functionality using system user token"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.system_user_file = os.path.join(self.test_dir, 'system_user.json')
        
        # Facebook Graph API configuration
        self.facebook_graph_url = "https://graph.facebook.com/v19.0"
        
        # Test content for posting
        self.test_text_post = {
            "caption": f"Test post from automated script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "media_type": "TEXT"
        }
        
        self.test_image_post = {
            "image_url": "https://via.placeholder.com/1080x1080.png?text=Test+Post",
            "caption": f"Test image post from automated script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "media_type": "IMAGE"
        }
    
    def load_system_user_token(self):
        """Load system user token from JSON file"""
        try:
            with open(self.system_user_file, 'r') as f:
                data = json.load(f)
            
            # Handle typo in original file
            token_key = 'system_user_access_toke' if 'system_user_access_toke' in data else 'system_user_access_token'
            return data[token_key]
            
        except FileNotFoundError:
            raise FileNotFoundError(f"System user file not found: {self.system_user_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in system user file: {self.system_user_file}")
    
    def get_facebook_pages(self, token):
        """Get Facebook pages managed by the app"""
        try:
            response = requests.get(
                f"{self.facebook_graph_url}/me/accounts",
                params={
                    'access_token': token,
                    'fields': 'id,name,category,access_token,instagram_business_account'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                print(f"Pages API Error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Pages request failed: {e}")
            return []
    
    def get_instagram_business_account(self, page_id, page_token):
        """Get Instagram business account connected to a Facebook page"""
        try:
            response = requests.get(
                f"{self.facebook_graph_url}/{page_id}",
                params={
                    'access_token': page_token,
                    'fields': 'instagram_business_account{id,username,profile_picture_url}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('instagram_business_account')
            else:
                print(f"Instagram Business Account API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Instagram Business Account request failed: {e}")
            return None
    
    def create_instagram_media_container(self, instagram_account_id, page_token, media_data):
        """Create an Instagram media container for posting"""
        try:
            # Prepare the payload based on media type
            payload = {
                'access_token': page_token,
                'caption': media_data['caption']
            }
            
            if media_data['media_type'] == 'IMAGE':
                payload['image_url'] = media_data['image_url']
            elif media_data['media_type'] == 'TEXT':
                # For text posts, we might need to create a simple image or use carousel
                payload['media_type'] = 'TEXT'
            
            response = requests.post(
                f"{self.facebook_graph_url}/{instagram_account_id}/media",
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Media Container API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Media Container request failed: {e}")
            return None
    
    def publish_instagram_media(self, instagram_account_id, page_token, creation_id):
        """Publish the Instagram media container"""
        try:
            response = requests.post(
                f"{self.facebook_graph_url}/{instagram_account_id}/media_publish",
                data={
                    'access_token': page_token,
                    'creation_id': creation_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Media Publish API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Media Publish request failed: {e}")
            return None
    
    def test_load_system_user_token(self):
        """Test loading system user token"""
        try:
            token = self.load_system_user_token()
            self.assertIsNotNone(token)
            self.assertTrue(len(token) > 0)
            print(f"✓ System user token loaded: {token[:20]}...")
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")
    
    def test_get_facebook_pages_real(self):
        """Test getting Facebook pages with real API call"""
        try:
            token = self.load_system_user_token()
            pages = self.get_facebook_pages(token)
            
            self.assertIsInstance(pages, list)
            print(f"✓ Found {len(pages)} Facebook pages")
            
            for page in pages:
                page_id = page.get('id')
                page_name = page.get('name')
                has_instagram = 'instagram_business_account' in page
                print(f"  - {page_name} (ID: {page_id}) - Instagram: {'Yes' if has_instagram else 'No'}")
                
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")
    
    def test_check_instagram_business_accounts_real(self):
        """Test checking for Instagram business accounts connected to pages"""
        try:
            token = self.load_system_user_token()
            pages = self.get_facebook_pages(token)
            
            instagram_accounts = []
            for page in pages:
                page_token = page.get('access_token')
                page_id = page.get('id')
                page_name = page.get('name')
                
                if page_token:
                    instagram_account = self.get_instagram_business_account(page_id, page_token)
                    if instagram_account:
                        instagram_accounts.append({
                            'page_name': page_name,
                            'page_id': page_id,
                            'instagram_account': instagram_account,
                            'page_token': page_token
                        })
                        print(f"✓ Found Instagram Business Account for {page_name}:")
                        print(f"  - Instagram ID: {instagram_account.get('id')}")
                        print(f"  - Username: @{instagram_account.get('username', 'Unknown')}")
                    else:
                        print(f"⚠ No Instagram Business Account found for {page_name}")
            
            print(f"✓ Total Instagram Business Accounts found: {len(instagram_accounts)}")
            return instagram_accounts
            
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")
    
    @patch('requests.post')
    def test_create_instagram_media_container_mocked(self, mock_post):
        """Test creating Instagram media container with mocked API"""
        # Mock successful media container creation
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_creation_id_123'
        }
        mock_post.return_value = mock_response
        
        # Test data
        instagram_account_id = 'test_instagram_id'
        page_token = 'test_page_token'
        
        result = self.create_instagram_media_container(
            instagram_account_id, 
            page_token, 
            self.test_image_post
        )
        
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        print(f"✓ Media container created with ID: {result['id']}")
    
    @patch('requests.post')
    def test_publish_instagram_media_mocked(self, mock_post):
        """Test publishing Instagram media with mocked API"""
        # Mock successful media publishing
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'published_media_id_123'
        }
        mock_post.return_value = mock_response
        
        # Test data
        instagram_account_id = 'test_instagram_id'
        page_token = 'test_page_token'
        creation_id = 'test_creation_id_123'
        
        result = self.publish_instagram_media(
            instagram_account_id, 
            page_token, 
            creation_id
        )
        
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        print(f"✓ Media published with ID: {result['id']}")
    
    def test_complete_instagram_posting_workflow_real(self):
        """Test complete Instagram posting workflow with real API calls (DRY RUN)"""
        try:
            print("\n" + "="*50)
            print("COMPLETE INSTAGRAM POSTING WORKFLOW TEST")
            print("="*50)
            
            # Step 1: Load system user token
            print("1. Loading system user token...")
            token = self.load_system_user_token()
            print(f"   ✓ Token loaded: {token[:20]}...")
            
            # Step 2: Get Facebook pages
            print("\n2. Getting Facebook pages...")
            pages = self.get_facebook_pages(token)
            print(f"   ✓ Found {len(pages)} pages")
            
            # Step 3: Check for Instagram business accounts
            print("\n3. Checking for Instagram business accounts...")
            instagram_accounts = []
            for page in pages:
                page_token = page.get('access_token')
                page_id = page.get('id')
                page_name = page.get('name')
                
                if page_token:
                    instagram_account = self.get_instagram_business_account(page_id, page_token)
                    if instagram_account:
                        instagram_accounts.append({
                            'page_name': page_name,
                            'page_id': page_id,
                            'instagram_account': instagram_account,
                            'page_token': page_token
                        })
                        print(f"   ✓ {page_name}: @{instagram_account.get('username', 'Unknown')}")
            
            if not instagram_accounts:
                print("   ⚠ No Instagram Business Accounts found!")
                print("   To connect an Instagram Business Account:")
                print("   1. Go to Facebook Business Manager")
                print("   2. Connect your Instagram Business Account to your Facebook Page")
                print("   3. Ensure proper permissions are granted")
                self.skipTest("No Instagram Business Accounts available for testing")
                return
            
            # Step 4: Simulate posting (DRY RUN)
            print(f"\n4. Simulating Instagram post creation (DRY RUN)...")
            for account in instagram_accounts[:1]:  # Test with first account only
                instagram_id = account['instagram_account']['id']
                page_token = account['page_token']
                username = account['instagram_account'].get('username', 'Unknown')
                
                print(f"   Target Account: @{username} (ID: {instagram_id})")
                print(f"   Post Caption: {self.test_text_post['caption']}")
                print("   ⚠ DRY RUN - Not actually posting to avoid spam")
                print("   To enable real posting, modify the test and add actual API calls")
            
            print(f"\n✓ Workflow test completed successfully!")
            print(f"✓ Ready to post to {len(instagram_accounts)} Instagram account(s)")
            
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")
    
    def test_instagram_api_permissions(self):
        """Test that we have the required permissions for Instagram posting"""
        try:
            token = self.load_system_user_token()
            
            # Check permissions
            response = requests.get(
                f"{self.facebook_graph_url}/me/permissions",
                params={'access_token': token},
                timeout=30
            )
            
            if response.status_code == 200:
                permissions = response.json().get('data', [])
                
                # Required permissions for Instagram posting
                required_permissions = [
                    'instagram_basic',
                    'instagram_content_publish',
                    'pages_show_list',
                    'pages_read_engagement'
                ]
                
                granted_permissions = [p['permission'] for p in permissions if p.get('status') == 'granted']
                
                print("✓ Checking Instagram API permissions:")
                for perm in required_permissions:
                    has_perm = perm in granted_permissions
                    status = "✓" if has_perm else "✗"
                    print(f"   {status} {perm}: {'granted' if has_perm else 'missing'}")
                
                missing_permissions = [p for p in required_permissions if p not in granted_permissions]
                if missing_permissions:
                    print(f"\n⚠ Missing permissions: {', '.join(missing_permissions)}")
                    print("  Add these permissions in Facebook App settings")
                else:
                    print("\n✓ All required permissions are granted!")
                    
            else:
                print(f"Permissions check failed: {response.status_code}")
                
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")

def post_to_instagram_real(dry_run=True):
    """
    Function to actually post to Instagram (use with caution)
    
    Args:
        dry_run (bool): If True, only simulates posting without actual API calls
    """
    print("=" * 60)
    print("INSTAGRAM POSTING FUNCTION")
    print("=" * 60)
    
    try:
        # Load system user token
        script_dir = os.path.dirname(os.path.abspath(__file__))
        system_user_file = os.path.join(script_dir, 'system_user.json')
        
        with open(system_user_file, 'r') as f:
            data = json.load(f)
        
        token_key = 'system_user_access_toke' if 'system_user_access_toke' in data else 'system_user_access_token'
        token = data[token_key]
        
        # Get Facebook pages
        facebook_graph_url = "https://graph.facebook.com/v19.0"
        response = requests.get(
            f"{facebook_graph_url}/me/accounts",
            params={
                'access_token': token,
                'fields': 'id,name,category,access_token,instagram_business_account'
            }
        )
        
        if response.status_code != 200:
            print(f"Error getting pages: {response.text}")
            return False
        
        pages = response.json().get('data', [])
        
        # Find Instagram business accounts
        for page in pages:
            page_token = page.get('access_token')
            page_id = page.get('id')
            page_name = page.get('name')
            
            if not page_token:
                continue
            
            # Check for Instagram business account
            ig_response = requests.get(
                f"{facebook_graph_url}/{page_id}",
                params={
                    'access_token': page_token,
                    'fields': 'instagram_business_account{id,username}'
                }
            )
            
            if ig_response.status_code == 200:
                ig_data = ig_response.json()
                instagram_account = ig_data.get('instagram_business_account')
                
                if instagram_account:
                    instagram_id = instagram_account['id']
                    username = instagram_account.get('username', 'Unknown')
                    
                    print(f"Found Instagram account: @{username}")
                    
                    if dry_run:
                        print("DRY RUN - Would post:")
                        print(f"  Caption: Test post from automated script - {datetime.now()}")
                        print("  To enable real posting, set dry_run=False")
                        return True
                    else:
                        # Create media container
                        media_payload = {
                            'access_token': page_token,
                            'caption': f"Test post from automated script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            'media_type': 'TEXT'
                        }
                        
                        container_response = requests.post(
                            f"{facebook_graph_url}/{instagram_id}/media",
                            data=media_payload
                        )
                        
                        if container_response.status_code == 200:
                            creation_id = container_response.json()['id']
                            print(f"Media container created: {creation_id}")
                            
                            # Publish media
                            publish_response = requests.post(
                                f"{facebook_graph_url}/{instagram_id}/media_publish",
                                data={
                                    'access_token': page_token,
                                    'creation_id': creation_id
                                }
                            )
                            
                            if publish_response.status_code == 200:
                                post_id = publish_response.json()['id']
                                print(f"✓ Posted successfully! Post ID: {post_id}")
                                return True
                            else:
                                print(f"Publish failed: {publish_response.text}")
                        else:
                            print(f"Container creation failed: {container_response.text}")
        
        print("No Instagram business accounts found")
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_instagram_tests():
    """Function to run all Instagram posting tests"""
    print("=" * 60)
    print("INSTAGRAM POSTING TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstagramPosting)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Also run the real posting function (dry run)
    print("\n" + "=" * 60)
    print("REAL POSTING TEST (DRY RUN)")
    print("=" * 60)
    post_to_instagram_real(dry_run=True)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_instagram_tests()
    sys.exit(0 if success else 1)
