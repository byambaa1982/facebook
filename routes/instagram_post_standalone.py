#!/usr/bin/env python3
"""
Standalone Instagram posting script using system user access
This script can post text and image content to Instagram Business accounts
"""

import os
import json
import requests
import argparse
from datetime import datetime
import time

def load_system_user_token(file_path=None):
    """
    Load system user token from JSON file
    
    Args:
        file_path (str, optional): Path to system_user.json file
        
    Returns:
        str: System user access token
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), 'system_user.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle typo in original file or use correct key
        token_key = 'system_user_access_token'
        if token_key not in data:
            # Fallback to typo version for backwards compatibility
            token_key = 'system_user_access_toke'
        
        if token_key not in data:
            raise KeyError("No system user access token found in file")
            
        return data[token_key]
        
    except FileNotFoundError:
        raise FileNotFoundError(f"System user file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in system user file: {file_path}")

def get_instagram_business_accounts(token):
    """
    Get all Instagram business accounts connected to Facebook pages
    
    Args:
        token (str): System user access token
        
    Returns:
        list: List of Instagram business accounts with their details
    """
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    instagram_accounts = []
    
    try:
        # Get Facebook pages
        response = requests.get(
            f"{facebook_graph_url}/me/accounts",
            params={
                'access_token': token,
                'fields': 'id,name,category,access_token'
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error getting pages: {response.text}")
            return instagram_accounts
        
        pages = response.json().get('data', [])
        
        # Check each page for Instagram business account
        for page in pages:
            page_token = page.get('access_token')
            page_id = page.get('id')
            page_name = page.get('name')
            
            if not page_token:
                continue
            
            # Get Instagram business account info
            ig_response = requests.get(
                f"{facebook_graph_url}/{page_id}",
                params={
                    'access_token': page_token,
                    'fields': 'instagram_business_account{id,username,profile_picture_url,followers_count}'
                },
                timeout=30
            )
            
            if ig_response.status_code == 200:
                ig_data = ig_response.json()
                instagram_account = ig_data.get('instagram_business_account')
                
                if instagram_account:
                    instagram_accounts.append({
                        'page_name': page_name,
                        'page_id': page_id,
                        'page_token': page_token,
                        'instagram_id': instagram_account['id'],
                        'username': instagram_account.get('username', 'Unknown'),
                        'profile_picture': instagram_account.get('profile_picture_url'),
                        'followers_count': instagram_account.get('followers_count', 0)
                    })
        
        return instagram_accounts
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return instagram_accounts

def create_instagram_media_container(instagram_id, page_token, post_data):
    """
    Create Instagram media container
    
    Args:
        instagram_id (str): Instagram business account ID
        page_token (str): Page access token
        post_data (dict): Post data with caption, image_url, etc.
        
    Returns:
        str: Creation ID if successful, None if failed
    """
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    
    try:
        payload = {
            'access_token': page_token,
            'caption': post_data['caption']
        }
        
        # Add media URL if it's an image post
        if 'image_url' in post_data:
            payload['image_url'] = post_data['image_url']
        
        response = requests.post(
            f"{facebook_graph_url}/{instagram_id}/media",
            data=payload,
            timeout=60  # Longer timeout for media processing
        )
        
        if response.status_code == 200:
            return response.json().get('id')
        else:
            print(f"Media container creation failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Media container request failed: {e}")
        return None

def publish_instagram_media(instagram_id, page_token, creation_id):
    """
    Publish Instagram media from container
    
    Args:
        instagram_id (str): Instagram business account ID
        page_token (str): Page access token
        creation_id (str): Media container creation ID
        
    Returns:
        str: Published media ID if successful, None if failed
    """
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    
    try:
        response = requests.post(
            f"{facebook_graph_url}/{instagram_id}/media_publish",
            data={
                'access_token': page_token,
                'creation_id': creation_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('id')
        else:
            print(f"Media publish failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Media publish request failed: {e}")
        return None

def post_to_instagram(caption, image_url=None, dry_run=True, account_index=0):
    """
    Post content to Instagram
    
    Args:
        caption (str): Post caption text
        image_url (str, optional): URL of image to post
        dry_run (bool): If True, simulates posting without actual API calls
        account_index (int): Index of Instagram account to use (if multiple)
        
    Returns:
        dict: Result with success status and details
    """
    result = {
        'success': False,
        'message': '',
        'post_id': None,
        'account_used': None
    }
    
    try:
        print("=" * 60)
        print("INSTAGRAM POSTING")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE POSTING'}")
        print()
        
        # Load system user token
        print("1. Loading system user token...")
        token = load_system_user_token()
        print(f"   ✓ Token loaded: {token[:20]}...")
        print()
        
        # Get Instagram accounts
        print("2. Getting Instagram business accounts...")
        instagram_accounts = get_instagram_business_accounts(token)
        
        if not instagram_accounts:
            result['message'] = "No Instagram business accounts found"
            print(f"   ✗ {result['message']}")
            return result
        
        print(f"   ✓ Found {len(instagram_accounts)} Instagram account(s):")
        for i, account in enumerate(instagram_accounts):
            username = account['username']
            followers = account.get('followers_count', 0)
            print(f"     [{i}] @{username} ({followers:,} followers)")
        print()
        
        # Select account
        if account_index >= len(instagram_accounts):
            result['message'] = f"Account index {account_index} out of range (0-{len(instagram_accounts)-1})"
            print(f"   ✗ {result['message']}")
            return result
        
        selected_account = instagram_accounts[account_index]
        instagram_id = selected_account['instagram_id']
        page_token = selected_account['page_token']
        username = selected_account['username']
        
        print(f"3. Selected account: @{username}")
        print(f"   Instagram ID: {instagram_id}")
        print()
        
        # Prepare post data
        post_data = {'caption': caption}
        if image_url:
            post_data['image_url'] = image_url
            print(f"4. Preparing image post...")
            print(f"   Image URL: {image_url}")
        else:
            print(f"4. Preparing text post...")
        
        print(f"   Caption: {caption}")
        print()
        
        if dry_run:
            print("5. DRY RUN - Simulating post creation...")
            print("   ✓ Would create media container")
            print("   ✓ Would publish media")
            print("   ⚠ No actual posting performed")
            result['success'] = True
            result['message'] = "Dry run completed successfully"
            result['account_used'] = username
            print(f"   {result['message']}")
        else:
            # Real posting
            print("5. Creating media container...")
            creation_id = create_instagram_media_container(instagram_id, page_token, post_data)
            
            if not creation_id:
                result['message'] = "Failed to create media container"
                print(f"   ✗ {result['message']}")
                return result
            
            print(f"   ✓ Media container created: {creation_id}")
            
            # Wait a moment for processing
            print("   Waiting for media processing...")
            time.sleep(2)
            
            print("6. Publishing media...")
            post_id = publish_instagram_media(instagram_id, page_token, creation_id)
            
            if not post_id:
                result['message'] = "Failed to publish media"
                print(f"   ✗ {result['message']}")
                return result
            
            print(f"   ✓ Media published successfully!")
            print(f"   Post ID: {post_id}")
            result['success'] = True
            result['message'] = "Post published successfully"
            result['post_id'] = post_id
            result['account_used'] = username
        
        print()
        print("=" * 60)
        print("POSTING COMPLETED")
        print("=" * 60)
        return result
        
    except Exception as e:
        result['message'] = f"Error: {str(e)}"
        print(f"✗ {result['message']}")
        return result

def list_instagram_accounts():
    """List all available Instagram business accounts"""
    try:
        print("=" * 60)
        print("INSTAGRAM BUSINESS ACCOUNTS")
        print("=" * 60)
        
        token = load_system_user_token()
        accounts = get_instagram_business_accounts(token)
        
        if not accounts:
            print("No Instagram business accounts found")
            print("\nTo connect an Instagram Business Account:")
            print("1. Go to Facebook Business Manager")
            print("2. Connect your Instagram Business Account to your Facebook Page")
            print("3. Ensure proper permissions are granted")
            return
        
        print(f"Found {len(accounts)} Instagram business account(s):\n")
        
        for i, account in enumerate(accounts):
            print(f"[{i}] @{account['username']}")
            print(f"    Page: {account['page_name']}")
            print(f"    Instagram ID: {account['instagram_id']}")
            print(f"    Followers: {account.get('followers_count', 0):,}")
            if account.get('profile_picture'):
                print(f"    Profile Picture: {account['profile_picture']}")
            print()
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(description='Post to Instagram using system user access')
    parser.add_argument('--list', action='store_true', help='List available Instagram accounts')
    parser.add_argument('--caption', type=str, help='Caption for the post')
    parser.add_argument('--image', type=str, help='URL of image to post')
    parser.add_argument('--account', type=int, default=0, help='Account index to use (default: 0)')
    parser.add_argument('--live', action='store_true', help='Perform actual posting (default is dry run)')
    
    args = parser.parse_args()
    
    if args.list:
        list_instagram_accounts()
        return
    
    if not args.caption:
        print("Error: Caption is required for posting")
        print("Use --caption 'Your post text here'")
        return
    
    # Default caption with timestamp if none provided
    caption = args.caption
    if caption.lower() == 'test':
        caption = f"Test post from automated script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Post to Instagram
    result = post_to_instagram(
        caption=caption,
        image_url=args.image,
        dry_run=not args.live,
        account_index=args.account
    )
    
    if result['success']:
        print(f"\n✓ Success: {result['message']}")
        if result['post_id']:
            print(f"  Post ID: {result['post_id']}")
        if result['account_used']:
            print(f"  Account: @{result['account_used']}")
    else:
        print(f"\n✗ Failed: {result['message']}")

if __name__ == '__main__':
    main()
