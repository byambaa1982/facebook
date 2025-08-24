#!/usr/bin/env python3
"""
UnQLite Database Ingestion Script

This script reads data from test/creds.json and creates a UnQLite database (data.db)
with username and password fields. Since the JSON contains Facebook page data,
we'll use the page name as username and access_token as password.
"""

import json
import os
from unqlite import UnQLite

def create_database():
    """Create and return UnQLite database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'data.db')
    return UnQLite(db_path)

def load_credentials():
    """Load credentials from test/creds.json"""
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'test', 'creds.json')
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")
    
    with open(creds_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ingest_data():
    """Main function to ingest data from JSON to UnQLite database"""
    print("Starting data ingestion...")
    
    # Load credentials from JSON
    try:
        creds_data = load_credentials()
        print(f"Loaded credentials file with {len(creds_data.get('data', []))} records")
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return False
    
    # Create database connection
    try:
        db = create_database()
        print("Connected to UnQLite database: data.db")
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    # Process and insert data
    try:
        inserted_count = 0
        updated_count = 0
        
        for record in creds_data.get('data', []):
            # Extract username (page name) and password (access_token)
            username = record.get('name', '')
            password = record.get('access_token', '')
            page_id = record.get('id', '')
            category = record.get('category', '')
            
            # Create a unique key for each record
            key = f"user:{page_id}"
            
            # Create the record to store
            user_data = {
                'username': username,
                'password': password,
                'page_id': page_id,
                'category': category,
                'tasks': record.get('tasks', [])
            }
            
            # Check if record already exists
            try:
                existing = db[key]
                # Record exists, update it
                db[key] = json.dumps(user_data)
                updated_count += 1
                print(f"Updated record: {username} (ID: {page_id})")
            except KeyError:
                # Record doesn't exist, insert new
                db[key] = json.dumps(user_data)
                inserted_count += 1
                print(f"Inserted new record: {username} (ID: {page_id})")
        
        # Commit and close
        db.commit()
        db.close()
        
        print(f"\nData ingestion completed successfully!")
        print(f"New records inserted: {inserted_count}")
        print(f"Existing records updated: {updated_count}")
        print(f"Database saved as: data.db")
        
        return True
        
    except Exception as e:
        print(f"Error during data ingestion: {e}")
        if 'db' in locals():
            db.close()
        return False

def verify_data():
    """Verify the data was inserted correctly"""
    print("\nVerifying inserted data...")
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'data.db')
        db = UnQLite(db_path)
        
        # Use direct key access since we know the pattern
        known_page_ids = ['682084288324866', '348160448389210']
        count = 0
        
        for page_id in known_page_ids:
            key = f'user:{page_id}'
            try:
                value = db[key]
                data = json.loads(value)
                count += 1
                
                print(f"Key: {key}")
                print(f"  Username: {data.get('username', 'N/A')}")
                print(f"  Password: {data.get('password', 'N/A')[:20]}..." if data.get('password') else "  Password: N/A")
                print(f"  Page ID: {data.get('page_id', 'N/A')}")
                print(f"  Category: {data.get('category', 'N/A')}")
                print()
            except KeyError:
                print(f"Key not found: {key}")
        
        print(f"Total records verified: {count}")
        db.close()
        
    except Exception as e:
        print(f"Error verifying data: {e}")

if __name__ == "__main__":
    # Run the ingestion process
    success = ingest_data()
    
    if success:
        # Verify the data was inserted correctly
        verify_data()
    else:
        print("Data ingestion failed!")
