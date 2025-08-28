#!/usr/bin/env python3
"""
Add Sample Posts to Database
===========================
"""

import sys
import os
sys.path.append('.')

from routes.comment import get_unqlite_db
import json
from datetime import datetime

def add_sample_posts():
    """Add sample posts to the database for testing"""
    db = get_unqlite_db()
    
    # Sample posts data
    sample_posts = [
        {
            'id': 'sample_post_1',
            'title': 'Test Post with Facebook ID',
            'content': 'This is a test post that has been posted to Facebook. It should appear in the display.',
            'description': 'This is a test post that has been posted to Facebook. It should appear in the display.',
            'facebook_post_id': '682084288324866_122126034368938534',
            'posted_to_facebook': True,
            'posted_to_page': 'Эхлэл',
            'posted_at': '2025-08-27T20:00:00Z',
            'created_at': '2025-08-27T19:30:00Z',
            'content_type': 'text'
        },
        {
            'id': 'sample_post_2', 
            'title': 'Another Test Post',
            'content': 'This is another test post with Facebook integration.',
            'description': 'This is another test post with Facebook integration.',
            'facebook_post_id': '682084288324866_122126038772938534',
            'posted_to_facebook': True,
            'posted_to_page': 'Эхлэл',
            'posted_at': '2025-08-27T19:00:00Z',
            'created_at': '2025-08-27T18:30:00Z',
            'content_type': 'text'
        },
        {
            'id': 'sample_post_3',
            'title': 'Local Post (No Facebook)',
            'content': 'This post exists locally but was not posted to Facebook.',
            'description': 'This post exists locally but was not posted to Facebook.',
            'posted_to_facebook': False,
            'created_at': '2025-08-27T18:00:00Z',
            'content_type': 'text'
        }
    ]
    
    print("Adding sample posts to database...")
    
    for post in sample_posts:
        key = f"content:{post['id']}"
        value = json.dumps(post)
        
        try:
            db[key] = value
            print(f"✅ Added post: {post['title']}")
        except Exception as e:
            print(f"❌ Error adding post {post['id']}: {e}")
    
    print(f"\n✅ Successfully added {len(sample_posts)} sample posts to database")
    
    # Verify by listing keys
    print("\n🔍 Verifying database contents:")
    content_keys = []
    for key in db:
        try:
            if isinstance(key, tuple):
                key_bytes = key[0] if key else b''
            elif isinstance(key, bytes):
                key_bytes = key
            else:
                key_bytes = str(key).encode('utf-8')
            
            if hasattr(key_bytes, 'decode'):
                key_str = key_bytes.decode('utf-8')
            else:
                key_str = str(key_bytes)
            
            if key_str.startswith('content:'):
                content_keys.append(key_str)
                print(f"  📝 {key_str}")
        except Exception as e:
            print(f"  ❌ Error reading key: {e}")
    
    print(f"\n📊 Total content keys found: {len(content_keys)}")
    
    db.close()

if __name__ == "__main__":
    add_sample_posts()
