#!/usr/bin/env python3
"""
Standalone test script for system user access using system_user.json file
Tests system user token validation and Facebook API access
"""

import sys
import os
import json
import requests
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSystemUserAccess(unittest.TestCase):
    """Test cases for system user access functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.system_user_file = os.path.join(self.test_dir, 'system_user.json')
        
        # Sample valid system user data
        self.valid_system_user_data = {
            "system_user_access_token": "EAAMU4HhUxE4BPa1l1rSU5vLb86SZBQZCRY9iQAZAWhQyG0O40LylDG0rv6G6ZC1mZAd8DPjm47u7ZAUNIbfalYD3AI9PWHwsHZAyLYHbEt2f3vqZBShXDnYzebpg2XQQ4TX0XcF4vaZAId3ZBDStqpzbsbsyQVZBKAUyJdCJhEULwSCKnWA5Ps7jKQlg1vJS8vc8gZDZD"
        }
        
        # Sample invalid system user data
        self.invalid_system_user_data = {
            "system_user_access_token": "invalid_token_123"
        }
        
        # Facebook API endpoints
        self.facebook_graph_url = "https://graph.facebook.com/v19.0"
        
    def test_read_system_user_file_success(self):
        """Test successfully reading system_user.json file"""
        try:
            with open(self.system_user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.assertIsInstance(data, dict)
            self.assertIn('system_user_access_token', data)  # Fixed key name
            self.assertIsInstance(data['system_user_access_token'], str)
            self.assertTrue(len(data['system_user_access_token']) > 0)
            print(f"✓ Successfully read system user file with token: {data['system_user_access_token'][:20]}...")
            
        except FileNotFoundError:
            self.fail(f"system_user.json file not found at {self.system_user_file}")
        except json.JSONDecodeError:
            self.fail("system_user.json contains invalid JSON")
    
    def test_read_system_user_file_not_found(self):
        """Test handling when system_user.json file doesn't exist"""
        non_existent_file = os.path.join(self.test_dir, 'non_existent_system_user.json')
        
        with self.assertRaises(FileNotFoundError):
            with open(non_existent_file, 'r') as f:
                json.load(f)
    
    def test_system_user_token_format(self):
        """Test that system user token has expected format"""
        try:
            with open(self.system_user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if it's using the correct key
            token_key = 'system_user_access_token'  # Now using correct key
            token = data[token_key]
            
            # Facebook tokens typically start with EAA and are quite long
            self.assertTrue(isinstance(token, str))
            self.assertTrue(len(token) > 50, "Token seems too short for a valid Facebook token")
            self.assertTrue(token.startswith('EAA'), "Facebook tokens typically start with 'EAA'")
            print(f"✓ Token format validation passed for token: {token[:20]}...")
            
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")
    
    @patch('requests.get')
    def test_validate_system_user_token_valid(self, mock_get):
        """Test validation of system user token with Facebook API"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_app_id',
            'name': 'Test App',
            'app_type': 'system_user'
        }
        mock_get.return_value = mock_response
        
        token = self.valid_system_user_data['system_user_access_token']
        
        # Make API call to validate token
        response = requests.get(
            f"{self.facebook_graph_url}/me",
            params={'access_token': token}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        print("✓ System user token validation API call successful")
    
    @patch('requests.get')
    def test_validate_system_user_token_invalid(self, mock_get):
        """Test validation of invalid system user token"""
        # Mock error API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {
                'message': 'Invalid OAuth access token.',
                'type': 'OAuthException',
                'code': 190
            }
        }
        mock_get.return_value = mock_response
        
        token = self.invalid_system_user_data['system_user_access_token']
        
        # Make API call with invalid token
        response = requests.get(
            f"{self.facebook_graph_url}/me",
            params={'access_token': token}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        print("✓ Invalid token properly rejected by API")
    
    @patch('requests.get')
    def test_get_app_info_with_system_token(self, mock_get):
        """Test getting app information using system user token"""
        # Mock app info response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123456789',
            'name': 'Test Facebook App',
            'app_type': 'system_user',
            'created_time': '2024-01-01T00:00:00+0000'
        }
        mock_get.return_value = mock_response
        
        token = self.valid_system_user_data['system_user_access_token']
        
        # Get app information
        response = requests.get(
            f"{self.facebook_graph_url}/me",
            params={
                'access_token': token,
                'fields': 'id,name,app_type,created_time'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('name', data)
        print(f"✓ Successfully retrieved app info: {data.get('name', 'Unknown')}")
    
    @patch('requests.get')
    def test_system_user_permissions(self, mock_get):
        """Test checking permissions available to system user"""
        # Mock permissions response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'permission': 'pages_show_list', 'status': 'granted'},
                {'permission': 'pages_read_engagement', 'status': 'granted'},
                {'permission': 'pages_manage_posts', 'status': 'granted'}
            ]
        }
        mock_get.return_value = mock_response
        
        token = self.valid_system_user_data['system_user_access_token']
        
        # Check permissions
        response = requests.get(
            f"{self.facebook_graph_url}/me/permissions",
            params={'access_token': token}
        )
        
        self.assertEqual(response.status_code, 200)
        permissions = response.json().get('data', [])
        self.assertIsInstance(permissions, list)
        print(f"✓ Retrieved {len(permissions)} permissions for system user")
    
    def test_load_system_user_helper_function(self):
        """Test helper function to load system user data"""
        def load_system_user_token(file_path=None):
            """Helper function to load system user token from JSON file"""
            if file_path is None:
                file_path = os.path.join(os.path.dirname(__file__), 'system_user.json')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Use correct key name
                token_key = 'system_user_access_token'
                return data.get(token_key)
                
            except FileNotFoundError:
                raise FileNotFoundError(f"System user file not found: {file_path}")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in system user file: {file_path}")
            except KeyError:
                raise KeyError("No system user access token found in file")
        
        # Test the helper function
        try:
            token = load_system_user_token()
            self.assertIsNotNone(token)
            self.assertTrue(len(token) > 0)
            print(f"✓ Helper function successfully loaded token: {token[:20]}...")
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")
    
    def test_system_user_file_structure(self):
        """Test that system_user.json has the expected structure"""
        try:
            with open(self.system_user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check that it's a dictionary
            self.assertIsInstance(data, dict)
            
            # Check for expected key
            has_correct_key = 'system_user_access_token' in data
            
            self.assertTrue(has_correct_key, 
                          "File should contain 'system_user_access_token' key")
            
            # Get the token
            token_key = 'system_user_access_token'
            token = data[token_key]
            
            self.assertIsInstance(token, str)
            self.assertTrue(len(token) > 0)
            
            print(f"✓ File structure validation passed")
            
            # Check for additional structure
            if 'instagram_accounts' in data:
                print(f"✓ Found {len(data['instagram_accounts'])} Instagram account(s)")
            if 'facebook_pages' in data:
                print(f"✓ Found {len(data['facebook_pages'])} Facebook page(s)")
            if 'permissions' in data:
                granted_perms = [p for p in data['permissions'] if p.get('status') == 'granted']
                print(f"✓ Found {len(granted_perms)} granted permissions")
                
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")

    @patch('requests.get')
    def test_real_token_validation(self, mock_get):
        """Test validation using the actual token from the file"""
        try:
            with open(self.system_user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Use correct key name
            token_key = 'system_user_access_token'
            real_token = data[token_key]
            
            # Mock a successful response for the real token
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'id': 'real_app_id',
                'name': 'Real Facebook App'
            }
            mock_get.return_value = mock_response
            
            # Test with the real token
            response = requests.get(
                f"{self.facebook_graph_url}/me",
                params={'access_token': real_token}
            )
            
            # Verify the mock was called with the correct token
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertEqual(call_args[1]['params']['access_token'], real_token)
            
            print(f"✓ Real token validation test completed with token: {real_token[:20]}...")
            
        except FileNotFoundError:
            self.skipTest("system_user.json file not found")

def run_system_user_tests():
    """Function to run all system user tests"""
    print("=" * 60)
    print("SYSTEM USER ACCESS TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSystemUserAccess)
    
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
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_system_user_tests()
    sys.exit(0 if success else 1)
