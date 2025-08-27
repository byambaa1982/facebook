#!/usr/bin/env python3
"""
Test the exact Flask route logic for posting content
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(__file__))

from routes.post import get_facebook_apps, get_content_by_id, post_text_to_facebook

def test_flask_route_logic():
    """Test the exact logic used in the Flask route"""
    
    # Simulate the Flask route parameters
    content_id = 'f124633a-3ac7-49a2-bee0-0d032bb16b30'  # From the log
    page_id = '682084288324866'  # The page we want to post to
    
    print(f"Testing content ID: {content_id}")
    print(f"Target page ID: {page_id}")
    
    # Get content from database (same as Flask route)
    content = get_content_by_id(content_id)
    if not content:
        print("❌ Content not found")
        return
    
    print(f"Content found: {content.get('title')}")
    print(f"Content type: {content.get('content_type')}")
    
    # Get Facebook app data (same as Flask route)
    facebook_apps = get_facebook_apps()
    print(f"Found {len(facebook_apps)} Facebook apps")
    
    selected_app = None
    for app in facebook_apps:
        print(f"  App: {app.get('username')} (Page ID: {app.get('page_id')})")
        if app.get('page_id') == page_id:
            selected_app = app
            print(f"  ✅ Selected this app!")
            break
    
    if not selected_app:
        print("❌ Facebook app not found for this page")
        return
    
    access_token = selected_app.get('password')
    if not access_token:
        print("❌ Access token not found for this page")
        return
    
    print(f"Access token (first 50 chars): {access_token[:50]}...")
    
    # Prepare post message (same as Flask route)
    post_message = f"{content['title']}\\n\\n{content['description']}"
    if content.get('tags'):
        tags = content['tags'].split(',')
        hashtags = ' '.join([f'#{tag.strip()}' for tag in tags if tag.strip()])
        post_message += f"\\n\\n{hashtags}"
    
    print(f"Post message: {post_message[:100]}...")
    
    # Test the posting function directly
    print("\\nTesting post_text_to_facebook function...")
    result = post_text_to_facebook(page_id, access_token, post_message)
    
    if 'error' in result:
        print(f"❌ Facebook API Error: {result['error']}")
        
        # Let's also test the raw API call
        print("\\nTesting raw Facebook API call...")
        graph_url = "https://graph.facebook.com/v21.0"
        url = f"{graph_url}/{page_id}/feed"
        
        response = requests.post(url, data={
            "message": post_message,
            "access_token": access_token
        })
        
        print(f"Raw API status code: {response.status_code}")
        try:
            raw_result = response.json()
            print(f"Raw API response: {raw_result}")
        except:
            print(f"Raw API response (text): {response.text}")
            
    else:
        print(f"✅ SUCCESS! Post ID: {result.get('id')}")

if __name__ == "__main__":
    test_flask_route_logic()
