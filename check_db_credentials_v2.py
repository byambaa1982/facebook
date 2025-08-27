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
            try:
                if isinstance(key, bytes):
                    key_str = key.decode('utf-8')
                else:
                    key_str = str(key)
                    
                if isinstance(value, bytes):
                    try:
                        value_str = value.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try latin-1 as fallback
                        value_str = value.decode('latin-1')
                else:
                    value_str = str(value)
                
                print(f"Key: {key_str}")
                print(f"Raw Value: {value_str[:100]}...")  # First 100 chars
                
                # Try to parse as JSON
                try:
                    parsed_value = json.loads(value_str)
                    all_data[key_str] = parsed_value
                    print(f"Parsed JSON successfully")
                    
                    # Show relevant fields
                    if isinstance(parsed_value, dict):
                        for field in ['username', 'password', 'access_token', 'id', 'name']:
                            if field in parsed_value:
                                value = parsed_value[field]
                                if field in ['password', 'access_token'] and len(str(value)) > 50:
                                    print(f"  {field}: {str(value)[:50]}...")
                                else:
                                    print(f"  {field}: {value}")
                    
                except json.JSONDecodeError as e:
                    all_data[key_str] = value_str
                    print(f"Not JSON: {e}")
                
                print("-" * 30)
            except Exception as e:
                print(f"Error processing key {key}: {e}")
                continue
        
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
        with open(creds_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        try:
            with open(creds_path, 'r', encoding='latin-1') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading credentials with latin-1: {e}")
            return None
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

def compare_credentials():
    """Compare database credentials with creds.json"""
    print("COMPARING CREDENTIALS")
    print("=" * 50)
    
    # Load from files
    print("Loading database data...")
    db_data = check_database_credentials()
    
    print("\nLoading creds.json data...")
    creds_data = load_creds_json()
    
    if not creds_data:
        print("Could not load creds.json for comparison")
        return
    
    print("\nCREDS.JSON DATA:")
    print("=" * 30)
    if 'data' in creds_data:
        for i, app in enumerate(creds_data['data']):
            print(f"App {i+1}:")
            print(f"  Name: {app.get('name', 'N/A')}")
            print(f"  ID: {app.get('id', 'N/A')}")
            print(f"  Access Token: {str(app.get('access_token', 'N/A'))[:50]}...")
            print()
    
    if not db_data:
        print("No database data loaded")
        return
    
    print("\nDATABASE DATA:")
    print("=" * 30)
    for key, value in db_data.items():
        print(f"Key: {key}")
        if isinstance(value, dict):
            for field in ['username', 'password', 'access_token', 'id', 'name']:
                if field in value:
                    val = value[field]
                    if field in ['password', 'access_token'] and len(str(val)) > 50:
                        print(f"  {field}: {str(val)[:50]}...")
                    else:
                        print(f"  {field}: {val}")
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
            
            # Search in database - look for user:page_id key
            db_key = f"user:{page_id}"
            if db_key in db_data:
                db_value = db_data[db_key]
                print(f"✅ Found exact key match: {db_key}")
                
                # Check access token
                db_token = db_value.get('password')  # routes/post.py uses 'password' field
                if db_token:
                    if db_token == access_token:
                        print("✅ ACCESS TOKEN MATCHES!")
                    else:
                        print("❌ ACCESS TOKEN MISMATCH!")
                        print(f"Expected: {access_token}")
                        print(f"Found:    {db_token}")
                        
                        # Check if they're similar (maybe truncated)
                        if access_token.startswith(db_token) or db_token.startswith(access_token):
                            print("⚠️  Tokens appear related (one might be truncated)")
                else:
                    print("❌ No password field found in database entry")
            else:
                print(f"❌ Key {db_key} not found in database")
                
                # Look for partial matches
                found_partial = False
                for db_key_check, db_value_check in db_data.items():
                    if str(page_id) in db_key_check or (isinstance(db_value_check, dict) and str(page_id) in str(db_value_check)):
                        print(f"⚠️  Found partial match in key: {db_key_check}")
                        found_partial = True
                
                if not found_partial:
                    print(f"❌ No trace of page ID {page_id} found in database")

if __name__ == "__main__":
    compare_credentials()
