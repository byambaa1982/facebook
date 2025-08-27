#!/usr/bin/env python3
"""
Test script to verify that routes/post.py can read Facebook apps from creds.json
"""

import sys
import os

# Add the project root to the path so we can import from routes
sys.path.insert(0, os.path.dirname(__file__))

# Import the function we want to test
from routes.post import get_facebook_apps

def test_facebook_apps():
    """Test that we can get Facebook apps from creds.json"""
    print("Testing get_facebook_apps() function...")
    print("=" * 50)
    
    try:
        apps = get_facebook_apps()
        
        if not apps:
            print("❌ No apps returned")
            return False
        
        print(f"✅ Found {len(apps)} Facebook app(s):")
        print()
        
        for i, app in enumerate(apps, 1):
            print(f"App {i}:")
            print(f"  Page ID: {app.get('page_id', 'N/A')}")
            print(f"  Username: {app.get('username', 'N/A')}")
            print(f"  Has Password: {bool(app.get('password'))}")
            if app.get('password'):
                print(f"  Password: {app.get('password')[:50]}...")
            print(f"  Category: {app.get('category', 'N/A')}")
            print(f"  Tasks: {app.get('tasks', [])}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Facebook apps: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_facebook_apps()
