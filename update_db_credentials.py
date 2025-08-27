#!/usr/bin/env python3
"""
Script to update instance/data.db with current credentials from test/creds.json
"""

import os
import json
import sys
from unqlite import UnQLite

def update_database_credentials():
    """Update database with current credentials from creds.json"""
    
    # Load current credentials
    creds_path = os.path.join('test', 'creds.json')
    if not os.path.exists(creds_path):
        print(f"Credentials file not found: {creds_path}")
        return False
    
    try:
        with open(creds_path, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return False
    
    # Database path
    db_path = os.path.join('instance', 'data.db')
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    print(f"Updating database: {db_path}")
    print("=" * 50)
    
    # Open database
    db = UnQLite(db_path)
    
    try:
        updated_count = 0
        
        if 'data' in creds_data:
            for app in creds_data['data']:
                page_id = app.get('id')
                access_token = app.get('access_token')
                page_name = app.get('name')
                
                if not page_id or not access_token:
                    print(f"Skipping incomplete app data: {app}")
                    continue
                
                db_key = f"user:{page_id}"
                
                print(f"\nUpdating Page: {page_name} (ID: {page_id})")
                print(f"Key: {db_key}")
                print(f"New Token: {access_token[:50]}...")
                
                # Check if key exists in database
                try:
                    existing_data = db[db_key]
                    if isinstance(existing_data, bytes):
                        existing_data = existing_data.decode('utf-8')
                    existing_json = json.loads(existing_data)
                    
                    print(f"Found existing data: {existing_json.get('username', 'N/A')}")
                    
                    # Update the password field (which stores the access token)
                    old_token = existing_json.get('password', '')
                    existing_json['password'] = access_token
                    
                    # Store updated data
                    db[db_key] = json.dumps(existing_json)
                    
                    print(f"✅ Updated access token")
                    if old_token != access_token:
                        print(f"   Old: {old_token[:50]}...")
                        print(f"   New: {access_token[:50]}...")
                    
                    updated_count += 1
                    
                except KeyError:
                    print(f"⚠️  Key {db_key} not found in database, creating new entry")
                    
                    # Create new entry
                    new_data = {
                        "username": page_name,
                        "password": access_token
                    }
                    
                    db[db_key] = json.dumps(new_data)
                    print(f"✅ Created new entry")
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error updating {db_key}: {e}")
        
        print(f"\n" + "=" * 50)
        print(f"Update complete. Updated {updated_count} entries.")
        
        return True
        
    except Exception as e:
        print(f"Error updating database: {e}")
        return False
    finally:
        db.close()

def verify_update():
    """Verify that the update was successful"""
    print("\nVERIFYING UPDATE...")
    print("=" * 30)
    
    # Load credentials again to compare
    creds_path = os.path.join('test', 'creds.json')
    with open(creds_path, 'r', encoding='utf-8') as f:
        creds_data = json.load(f)
    
    # Check database
    db_path = os.path.join('instance', 'data.db')
    db = UnQLite(db_path)
    
    try:
        all_good = True
        
        if 'data' in creds_data:
            for app in creds_data['data']:
                page_id = app.get('id')
                expected_token = app.get('access_token')
                page_name = app.get('name')
                
                db_key = f"user:{page_id}"
                
                try:
                    db_data = db[db_key]
                    if isinstance(db_data, bytes):
                        db_data = db_data.decode('utf-8')
                    db_json = json.loads(db_data)
                    
                    actual_token = db_json.get('password', '')
                    
                    if actual_token == expected_token:
                        print(f"✅ {page_name} (ID: {page_id}) - Token matches")
                    else:
                        print(f"❌ {page_name} (ID: {page_id}) - Token mismatch!")
                        print(f"   Expected: {expected_token[:50]}...")
                        print(f"   Actual:   {actual_token[:50]}...")
                        all_good = False
                        
                except Exception as e:
                    print(f"❌ {page_name} (ID: {page_id}) - Error: {e}")
                    all_good = False
        
        if all_good:
            print("\n🎉 All credentials verified successfully!")
        else:
            print("\n⚠️  Some credentials still don't match")
            
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify-only":
        verify_update()
    else:
        print("🔧 UPDATING DATABASE CREDENTIALS")
        print("=" * 50)
        
        success = update_database_credentials()
        
        if success:
            verify_update()
        else:
            print("Update failed!")
