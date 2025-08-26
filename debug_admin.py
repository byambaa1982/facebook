from routes.admin import get_unqlite_db, get_recent_contents
import sys

print('Testing get_recent_contents function...')
try:
    db = get_unqlite_db()
    contents = get_recent_contents(db, limit=10)
    print(f'Found {len(contents)} contents:')
    
    for i, content in enumerate(contents, 1):
        print(f'{i}. Title: {content.get("title", "No title")}')
        print(f'   Type: {content.get("content_type", "No type")}')
        print(f'   File: {content.get("file_path", "No file")}')
        print(f'   Created: {content.get("created_at", "No date")}')
        print('')
        
    db.close()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
