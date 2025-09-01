#!/usr/bin/env python3
"""
Example usage script for system user access
Demonstrates how to use the system_user.json file for Facebook API access
"""

import os
import json
import requests
from datetime import datetime

def load_system_user_token(file_path=None):
    """
    Load system user token from JSON file
    
    Args:
        file_path (str, optional): Path to system_user.json file
        
    Returns:
        str: System user access token
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the JSON is invalid
        KeyError: If the token key is not found
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), 'system_user.json')
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle typo in original file (system_user_access_toke vs system_user_access_token)
        token_key = 'system_user_access_toke' if 'system_user_access_toke' in data else 'system_user_access_token'
        
        if token_key not in data:
            raise KeyError("No system user access token found in file")
            
        return data[token_key]
        
    except FileNotFoundError:
        raise FileNotFoundError(f"System user file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in system user file: {file_path}")

def validate_system_user_token(token):
    """
    Validate system user token with Facebook API
    
    Args:
        token (str): System user access token
        
    Returns:
        dict: API response data if successful, None if failed
    """
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    
    try:
        response = requests.get(
            f"{facebook_graph_url}/me",
            params={'access_token': token},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def get_app_permissions(token):
    """
    Get permissions available to the system user
    
    Args:
        token (str): System user access token
        
    Returns:
        list: List of permissions with their status
    """
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    
    try:
        response = requests.get(
            f"{facebook_graph_url}/me/permissions",
            params={'access_token': token},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Permissions API Error: {response.status_code} - {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Permissions request failed: {e}")
        return []

def get_app_pages(token):
    """
    Get pages managed by the app using system user token
    
    Args:
        token (str): System user access token
        
    Returns:
        list: List of pages
    """
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    
    try:
        response = requests.get(
            f"{facebook_graph_url}/me/accounts",
            params={
                'access_token': token,
                'fields': 'id,name,category,access_token'
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

def main():
    """Main function to demonstrate system user access"""
    print("=" * 60)
    print("SYSTEM USER ACCESS DEMONSTRATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Load system user token
        print("1. Loading system user token...")
        token = load_system_user_token()
        print(f"   ✓ Token loaded: {token[:20]}...{token[-10:]}")
        print()
        
        # Validate token
        print("2. Validating system user token...")
        app_info = validate_system_user_token(token)
        if app_info:
            print(f"   ✓ Token is valid")
            print(f"   App ID: {app_info.get('id', 'Unknown')}")
            print(f"   App Name: {app_info.get('name', 'Unknown')}")
        else:
            print("   ✗ Token validation failed")
            return
        print()
        
        # Get permissions
        print("3. Checking app permissions...")
        permissions = get_app_permissions(token)
        if permissions:
            print(f"   ✓ Found {len(permissions)} permissions:")
            for perm in permissions[:5]:  # Show first 5 permissions
                status = perm.get('status', 'unknown')
                perm_name = perm.get('permission', 'unknown')
                print(f"     - {perm_name}: {status}")
            if len(permissions) > 5:
                print(f"     ... and {len(permissions) - 5} more")
        else:
            print("   ⚠ No permissions found or request failed")
        print()
        
        # Get pages
        print("4. Fetching managed pages...")
        pages = get_app_pages(token)
        if pages:
            print(f"   ✓ Found {len(pages)} pages:")
            for page in pages[:3]:  # Show first 3 pages
                page_id = page.get('id', 'Unknown')
                page_name = page.get('name', 'Unknown')
                category = page.get('category', 'Unknown')
                print(f"     - {page_name} (ID: {page_id}, Category: {category})")
            if len(pages) > 3:
                print(f"     ... and {len(pages) - 3} more")
        else:
            print("   ⚠ No pages found or request failed")
        print()
        
        print("=" * 60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"✗ File Error: {e}")
    except ValueError as e:
        print(f"✗ JSON Error: {e}")
    except KeyError as e:
        print(f"✗ Key Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")

if __name__ == '__main__':
    main()
