#!/usr/bin/env python3
"""
Test script to debug Facebook posting in Flask app context
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from routes.post import (
    get_facebook_apps, 
    get_content_by_id, 
    post_text_to_facebook, 
    post_photo_to_facebook
)
import json

def test_facebook_apps():
    """Test if we can get Facebook apps from database"""
    print("=== Testing Facebook Apps ===")
    try:
        apps = get_facebook_apps()
        print(f"Found {len(apps)} Facebook apps:")
        for i, app in enumerate(apps, 1):
            print(f"  {i}. Page ID: {app.get('page_id')}")
            print(f"     Username: {app.get('username')}")
            print(f"     Has Token: {'Yes' if app.get('password') else 'No'}")
            print(f"     Token (first 20 chars): {app.get('password', '')[:20]}...")
        return apps
    except Exception as e:
        print(f"Error getting Facebook apps: {e}")
        return []

def test_content():
    """Test if we can get content from database"""
    print("\n=== Testing Content ===")
    try:
        # Test with known content ID from debug output
        content_ids = [
            '7da195f3-a182-4f3c-8dae-ae77cf3e769c',
            'a54cefb7-2dad-431a-84ff-bd63fda9a3b0', 
            'f124633a-3ac7-49a2-bee0-0d032bb16b30'
        ]
        
        contents = []
        for content_id in content_ids:
            content = get_content_by_id(content_id)
            if content:
                print(f"Content ID: {content_id}")
                print(f"  Title: {content.get('title')}")
                print(f"  Type: {content.get('content_type')}")
                print(f"  Description: {content.get('description', '')[:100]}...")
                contents.append((content_id, content))
        
        return contents
    except Exception as e:
        print(f"Error getting content: {e}")
        return []

def test_facebook_posting(apps, contents):
    """Test actual Facebook posting"""
    print("\n=== Testing Facebook Posting ===")
    
    if not apps:
        print("No Facebook apps available for testing")
        return
    
    if not contents:
        print("No content available for testing")
        return
    
    # Use first app and first text content
    app = apps[0]
    page_id = app.get('page_id')
    access_token = app.get('password')
    
    print(f"Using page: {app.get('username')} (ID: {page_id})")
    
    # Find text content to test
    text_content = None
    for content_id, content in contents:
        if content.get('content_type') == 'text':
            text_content = (content_id, content)
            break
    
    if text_content:
        content_id, content = text_content
        print(f"Testing with text content: {content.get('title')}")
        
        # Prepare message
        message = f"[TEST] {content.get('title')}\n\n{content.get('description', '')}"
        print(f"Message to post: {message[:100]}...")
        
        # Try posting
        try:
            result = post_text_to_facebook(page_id, access_token, message)
            print(f"Post result: {result}")
            
            if 'error' in result:
                print(f"❌ FACEBOOK API ERROR: {result['error']}")
            else:
                print(f"✅ SUCCESS: Post ID = {result.get('id')}")
                
        except Exception as e:
            print(f"❌ EXCEPTION during posting: {e}")
    else:
        print("No text content found for testing")

if __name__ == "__main__":
    print("Testing Facebook posting functionality in Flask app context...")
    
    # Test Facebook apps
    apps = test_facebook_apps()
    
    # Test content
    contents = test_content()
    
    # Test posting
    test_facebook_posting(apps, contents)
    
    print("\nTesting complete!")
