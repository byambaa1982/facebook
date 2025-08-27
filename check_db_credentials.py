#!/usr/bin/env python3
"""
Script to check credentials in instance/data.db and compare with test/creds.json
"""

import os
import json
import sys
from unqlite import UnQLite

def check_database_credentials():
    """Check what credentials are stored in the database"""
    
    # Database path
    db_path = os.path.join('instance', 'data.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    print(f"Checking database: {db_path}")
    print("=" * 50)
    
    # Open database
    db = UnQLite(db_path)
    
    try:
        # List all keys and data
        all_data = {}
        for key, value in db.items():
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = str(key)
                
            if isinstance(value, bytes):
                value_str = value.decode('utf-8')
            else:
                value_str = str(value)
            
            print(f"Key: {key_str}")
            print(f"Raw Value: {value_str[:100]}...")  # First 100 chars
            
            # Try to parse as JSON
            try:
                parsed_value = json.loads(value_str)
                all_data[key_str] = parsed_value
                print(f"Parsed JSON: {json.dumps(parsed_value, indent=2)[:200]}...")
            except json.JSONDecodeError:
                all_data[key_str] = value_str
                print(f"Not JSON, stored as string")
            
            print("-" * 30)
        
        return all_data
        
    except Exception as e:
        print(f"Error reading database: {e}")
        return False
    finally:
        db.close()

def load_creds_json():
    """Load credentials from test/creds.json"""
    creds_path = os.path.join('test', 'creds.json')
    
    if not os.path.exists(creds_path):
        print(f"Credentials file not found: {creds_path}")
        return None
    
    try:
        with open(creds_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

def compare_credentials():
    """Compare database credentials with creds.json"""
    print("COMPARING CREDENTIALS")
    print("=" * 50)
    
    # Load from files
    db_data = check_database_credentials()
    creds_data = load_creds_json()
    
    if not db_data or not creds_data:
        print("Could not load data for comparison")
        return
    
    print("\nCREDS.JSON DATA:")
    print("=" * 30)
    print(json.dumps(creds_data, indent=2))
    
    print("\nDATABASE DATA:")
    print("=" * 30)
    for key, value in db_data.items():
        print(f"Key: {key}")
        print(f"Value: {json.dumps(value, indent=2) if isinstance(value, dict) else value}")
        print("-" * 20)
    
    # Look for matching credentials
    print("\nCOMPARISON ANALYSIS:")
    print("=" * 30)
    
    if 'data' in creds_data:
        for app in creds_data['data']:
            page_id = app.get('id')
            access_token = app.get('access_token')
            page_name = app.get('name')
            
            print(f"\nLooking for Page: {page_name} (ID: {page_id})")
            print(f"Expected access token: {access_token[:50]}...")
            
            # Search in database
            found = False
            for db_key, db_value in db_data.items():
                if isinstance(db_value, dict):
                    # Check if this contains our page data
                    if str(page_id) in str(db_value) or page_id in str(db_value):
                        print(f"Found matching page in DB key: {db_key}")
                        print(f"DB Value: {json.dumps(db_value, indent=2)}")
                        
                        # Check if access token matches
                        db_token = None
                        if 'access_token' in db_value:
                            db_token = db_value['access_token']
                        elif 'password' in db_value:
                            db_token = db_value['password']
                        elif 'token' in db_value:
                            db_token = db_value['token']
                        
                        if db_token:
                            if db_token == access_token:
                                print("✅ ACCESS TOKEN MATCHES!")
                            else:
                                print("❌ ACCESS TOKEN MISMATCH!")
                                print(f"Expected: {access_token}")
                                print(f"Found:    {db_token}")
                        else:
                            print("⚠️  No access token found in database entry")
                        
                        found = True
                        break
            
            if not found:
                print(f"❌ Page {page_name} (ID: {page_id}) not found in database")

if __name__ == "__main__":
    compare_credentials()
