#!/usr/bin/env python3
"""
Token Validation and Comment Fetching
=====================================
"""

import requests
import json
import sys

def test_token(token, page_id):
    """Test if a Facebook access token is valid"""
    print(f"🔍 Testing token: {token[:20]}...")
    
    # Test basic page access
    url = f'https://graph.facebook.com/v18.0/{page_id}'
    params = {'access_token': token}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error']['message']
            print(f"  ❌ Token invalid: {error_msg}")
            return False
        else:
            page_name = data.get('name', 'Unknown')
            print(f"  ✅ Token valid! Page: {page_name}")
            return True
            
    except Exception as e:
        print(f"  ❌ Error testing token: {e}")
        return False

def fetch_comments_with_token(token, page_id):
    """Fetch comments using a valid token"""
    print(f"\n💬 Fetching posts and comments with valid token...")
    
    # Get recent posts
    posts_url = f'https://graph.facebook.com/v18.0/{page_id}/posts'
    posts_params = {
        'access_token': token,
        'fields': 'id,message,created_time',
        'limit': 3
    }
    
    try:
        response = requests.get(posts_url, params=posts_params)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error']['message']
            print(f"❌ Cannot access posts: {error_msg}")
            return
            
        posts = data.get('data', [])
        print(f"✅ Found {len(posts)} recent posts")
        
        if not posts:
            print("ℹ️  No posts found")
            return
            
        # Get comments for each post
        for i, post in enumerate(posts):
            post_id = post['id']
            message = post.get('message', 'No message')[:50] + '...'
            
            print(f"\n📝 Post {i+1}: {message}")
            print(f"   ID: {post_id}")
            
            # Fetch comments
            comments_url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
            comments_params = {
                'access_token': token,
                'fields': 'id,message,from,created_time'
            }
            
            comments_response = requests.get(comments_url, params=comments_params)
            comments_data = comments_response.json()
            
            if 'error' in comments_data:
                error_msg = comments_data['error']['message']
                print(f"   ❌ Cannot access comments: {error_msg}")
            else:
                comments = comments_data.get('data', [])
                print(f"   💬 Found {len(comments)} comment(s)")
                
                for j, comment in enumerate(comments):
                    author = comment.get('from', {}).get('name', 'Unknown')
                    message = comment.get('message', 'No message')
                    created_time = comment.get('created_time', 'Unknown')
                    
                    print(f"     Comment {j+1}:")
                    print(f"       👤 {author}")
                    print(f"       💬 {message}")
                    print(f"       🕒 {created_time}")
                    
    except Exception as e:
        print(f"❌ Error fetching posts/comments: {e}")

def main():
    # Read tokens from creds.json
    try:
        with open('routes/creds.json', 'r', encoding='utf-8') as f:
            creds = json.load(f)
    except Exception as e:
        print(f"❌ Cannot read credentials: {e}")
        return
    
    page_id = creds.get('page_id', '682084288324866')
    print(f"📱 Using page ID: {page_id}")
    
    # Get all possible tokens
    tokens_to_test = []
    
    # Page token from top level
    if 'page_token' in creds:
        tokens_to_test.append(creds['page_token'])
    
    # Access tokens from data array
    if 'data' in creds:
        for app in creds['data']:
            if 'access_token' in app:
                tokens_to_test.append(app['access_token'])
    
    print(f"🔍 Found {len(tokens_to_test)} token(s) to test")
    
    # Test each token
    valid_token = None
    for i, token in enumerate(tokens_to_test):
        print(f"\n--- Testing Token {i+1} ---")
        if test_token(token, page_id):
            valid_token = token
            break
    
    if valid_token:
        print(f"\n🎉 Found valid token! Fetching your posts and comments...")
        fetch_comments_with_token(valid_token, page_id)
    else:
        print("\n❌ No valid tokens found. You may need to refresh your Facebook access token.")
        print("   Visit https://developers.facebook.com/tools/explorer/ to get a new token.")

if __name__ == "__main__":
    main()
