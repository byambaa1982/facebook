#!/usr/bin/env python3
"""
Test script to check if the Facebook access tokens in creds.json are still valid
"""

import json
import requests
import os

def test_facebook_tokens():
    """Test if Facebook access tokens are still valid"""
    
    # Load tokens from routes/creds.json
    creds_path = os.path.join('routes', 'creds.json')
    
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return
    
    try:
        with open(creds_path, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return
    
    print("Testing Facebook Access Tokens")
    print("=" * 50)
    
    if 'data' not in creds_data:
        print("❌ No 'data' field found in creds.json")
        return
    
    for i, app in enumerate(creds_data['data'], 1):
        page_id = app.get('id')
        access_token = app.get('access_token')
        page_name = app.get('name')
        
        print(f"\nApp {i}: {page_name} (ID: {page_id})")
        print(f"Token: {access_token[:50]}...")
        
        if not access_token:
            print("❌ No access token found")
            continue
        
        # Test the token by making a simple API call
        try:
            # Try to get basic page info
            url = f"https://graph.facebook.com/v21.0/{page_id}"
            params = {
                'access_token': access_token,
                'fields': 'id,name,category'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Token is VALID")
                print(f"   Page Name: {data.get('name', 'N/A')}")
                print(f"   Category: {data.get('category', 'N/A')}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'message': response.text}
                print(f"❌ Token is INVALID")
                print(f"   Status Code: {response.status_code}")
                print(f"   Error: {error_data.get('error', {}).get('message', error_data.get('message', 'Unknown error'))}")
                
                # Check for specific error codes
                error_code = error_data.get('error', {}).get('code')
                if error_code == 190:
                    print("   → This means the access token has expired or been invalidated")
                    print("   → You need to generate a new access token")
                
        except requests.RequestException as e:
            print(f"❌ Network error testing token: {e}")
        except Exception as e:
            print(f"❌ Error testing token: {e}")

if __name__ == "__main__":
    test_facebook_tokens()
