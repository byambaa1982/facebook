#!/usr/bin/env python3
"""
Update Facebook access tokens in the Flask app database
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from routes.post import get_unqlite_db

def update_facebook_token():
    """Update Facebook access token in database from test config"""
    
    # Get current working token from test config
    try:
        with open('test/config.json', 'r') as f:
            config = json.load(f)
        current_token = config['page_token']
        page_id = config['page_id']
        print(f"Loaded current token for page {page_id}")
        print(f"Token (first 50 chars): {current_token[:50]}...")
    except Exception as e:
        print(f"Error loading test config: {e}")
        return False
    
    # Update database
    db = get_unqlite_db()
    try:
        # Find and update the Facebook app entry
        for key, value in db.items():
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = str(key)
                
            if key_str.startswith('user:') and key_str.endswith(page_id):
                try:
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8')
                    else:
                        value_str = str(value)
                    
                    app_data = json.loads(value_str)
                    old_token = app_data.get('password', '')
                    
                    print(f"Found app: {app_data.get('username')} (Page ID: {app_data.get('page_id')})")
                    print(f"Old token (first 50 chars): {old_token[:50]}...")
                    
                    # Update token
                    app_data['password'] = current_token
                    app_data['updated_at'] = str(__import__('datetime').datetime.now())
                    
                    # Save back to database
                    db[key] = json.dumps(app_data)
                    print(f"✅ Updated token for {app_data.get('username')}")
                    
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error processing key {key_str}: {e}")
                    continue
        
        db.commit()
        print("✅ Database updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating database: {e}")
        return False
    finally:
        db.close()

def test_updated_token():
    """Test if the updated token works"""
    print("\n=== Testing Updated Token ===")
    try:
        from routes.post import get_facebook_apps, post_text_to_facebook
        
        apps = get_facebook_apps()
        for app in apps:
            if app.get('page_id') == '682084288324866':
                page_id = app.get('page_id')
                access_token = app.get('password')
                
                # Test with a simple message
                test_message = f"Token update test - {__import__('datetime').datetime.now()}"
                result = post_text_to_facebook(page_id, access_token, test_message)
                
                if 'error' in result:
                    print(f"❌ Still getting error: {result['error']}")
                    return False
                else:
                    print(f"✅ SUCCESS! Post ID: {result.get('id')}")
                    return True
        
        print("No matching app found")
        return False
        
    except Exception as e:
        print(f"Error testing token: {e}")
        return False

if __name__ == "__main__":
    print("Updating Facebook access token in database...")
    
    if update_facebook_token():
        # Test the updated token
        test_updated_token()
    else:
        print("Failed to update token")
