#!/usr/bin/env python3
"""
Test Facebook Access Tokens
============================
"""

import requests
import json
import os

def test_token(token, token_name):
    """Test if a Facebook access token is valid"""
    print(f"\n🔑 Testing {token_name}...")
    print(f"   Token: {'***' + token[-10:] if len(token) > 10 else '***'}")
    
    try:
        # Test the token by getting basic page info
        response = requests.get(
            "https://graph.facebook.com/v18.0/me",
            params={
                "fields": "id,name,category,fan_count",
                "access_token": token
            }
        )
        
        data = response.json()
        
        if 'error' in data:
            error = data['error']
            print(f"   ❌ Invalid - {error.get('message', 'Unknown error')}")
            print(f"      Error code: {error.get('code', 'Unknown')}")
            return False
        else:
            print(f"   ✅ Valid!")
            print(f"      Page: {data.get('name', 'Unknown')}")
            print(f"      ID: {data.get('id', 'Unknown')}")
            print(f"      Category: {data.get('category', 'Unknown')}")
            return True
            
    except Exception as e:
        print(f"   ❌ Error testing token: {e}")
        return False

def main():
    print("🔍 Testing Facebook Access Tokens...")
    print("=" * 50)
    
    tokens_tested = 0
    valid_tokens = 0
    
    # Try to load creds from both locations
    for creds_path in ['routes/creds.json', 'test/creds.json']:
        if os.path.exists(creds_path):
            print(f"\n📂 Reading from: {creds_path}")
            
            try:
                with open(creds_path, 'r', encoding='utf-8') as f:
                    creds_data = json.load(f)
                
                # Test tokens from data array
                if 'data' in creds_data and creds_data['data']:
                    for i, app in enumerate(creds_data['data']):
                        token = app.get('access_token')
                        if token:
                            tokens_tested += 1
                            if test_token(token, f"Data Array Token #{i+1}"):
                                valid_tokens += 1
                
                # Test root level page_token
                if 'page_token' in creds_data:
                    token = creds_data['page_token']
                    if token:
                        tokens_tested += 1
                        if test_token(token, "Root Level page_token"):
                            valid_tokens += 1
                
            except Exception as e:
                print(f"❌ Error reading {creds_path}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Tokens tested: {tokens_tested}")
    print(f"   Valid tokens: {valid_tokens}")
    
    if valid_tokens == 0:
        print("\n💡 No valid tokens found. You need to:")
        print("   1. Run get_token.py to generate fresh tokens")
        print("   2. Make sure you complete the OAuth flow")
        print("   3. Ensure your Facebook app has the correct permissions")

if __name__ == "__main__":
    main()
