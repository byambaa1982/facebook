from unqlite import UnQLite
import json
import os

# Get database path
db_path = os.path.join('instance', 'data.db')
print(f'Database path: {db_path}')

if os.path.exists(db_path):
    db = UnQLite(db_path)
    
    print('\nFacebook app entries in database:')
    for key, value in db.items():
        if isinstance(key, bytes):
            key_str = key.decode('utf-8')
        else:
            key_str = str(key)
            
        if key_str.startswith('user:'):
            try:
                if isinstance(value, bytes):
                    value_str = value.decode('utf-8')
                else:
                    value_str = str(value)
                app_data = json.loads(value_str)
                print(f'App: {key_str}')
                print(f'  Username: {app_data.get("username", "No username")}')
                print(f'  Page ID: {app_data.get("page_id", "No page_id")}')
                print(f'  Has token: {"Yes" if app_data.get("password") else "No"}')
                print('')
            except Exception as e:
                print(f'   Error parsing: {e}')
    
    db.close()
else:
    print('Database file not found!')
