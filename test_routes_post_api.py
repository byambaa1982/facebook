#!/usr/bin/env python3
"""
Test script to verify routes/post.py API functionality
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_routes_post_api():
    """Test the routes/post.py API functions with actual Facebook calls"""
    try:
        print("Testing routes/post.py API functionality...")
        
        # Import the functions
        from routes.post import get_facebook_apps, post_text_to_facebook
        
        # Get Facebook apps
        apps = get_facebook_apps()
        if not apps:
            print("✗ No Facebook apps found")
            return False
            
        app = apps[0]  # Use first app
        page_id = app.get('page_id')
        access_token = app.get('password')
        
        if not page_id or not access_token:
            print("✗ Missing credentials")
            return False
            
        print(f"Using page: {app.get('username')} (ID: {page_id})")
        
        # Test posting text
        test_message = "Test post from routes/post.py - " + str(os.urandom(4).hex())
        print(f"Posting message: {test_message}")
        
        result = post_text_to_facebook(page_id, access_token, test_message)
        
        if 'error' in result:
            print(f"✗ Facebook API Error: {result['error']}")
            return False
        elif 'id' in result:
            print(f"✓ Post successful! Post ID: {result['id']}")
            return True
        else:
            print(f"✗ Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("Testing routes/post.py API Functionality")
    print("="*60)
    
    success = test_routes_post_api()
    
    print("\n" + "="*60)
    if success:
        print("✓ routes/post.py is working correctly!")
    else:
        print("✗ routes/post.py has issues!")
