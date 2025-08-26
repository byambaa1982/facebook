from unqlite import UnQLite
import json
import os

# Get database path
db_path = os.path.join('instance', 'data.db')
print(f'Database path: {db_path}')
print(f'Database exists: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    db = UnQLite(db_path)
    
    content_count = 0
    print('\nAll content entries in database:')
    for key, value in db.items():
        if isinstance(key, bytes):
            key_str = key.decode('utf-8')
        else:
            key_str = str(key)
            
        if key_str.startswith('content:'):
            content_count += 1
            try:
                if isinstance(value, bytes):
                    value_str = value.decode('utf-8')
                else:
                    value_str = str(value)
                content_data = json.loads(value_str)
                print(f'{content_count}. Key: {key_str}')
                print(f'   Title: {content_data.get("title", "No title")}')
                print(f'   Type: {content_data.get("content_type", "No type")}')
                print(f'   File path: {content_data.get("file_path", "No file")}')
                print(f'   Created: {content_data.get("created_at", "No date")}')
                print('')
            except Exception as e:
                print(f'   Error parsing: {e}')
    
    print(f'Total content entries found: {content_count}')
    db.close()
else:
    print('Database file not found!')
