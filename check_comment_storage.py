#!/usr/bin/env python3
"""
Check and Store Comments in UnQLite Database
============================================
"""

import sys
import os
sys.path.append('.')

from routes.comment import (
    get_comments_from_db, 
    store_comments_in_db, 
    get_facebook_apps, 
    get_post_comments_from_facebook
)
import json

def check_and_store_comments():
    print('🔍 Checking if comments are stored in unqlite database...')
    print('=' * 60)
    
    # The post ID that had 2 comments
    post_id = '682084288324866_122126034368938534'
    content_id = 'test_content_for_comments'  # Using a test content ID
    
    print(f'📝 Checking for comments in database for post: {post_id}')
    
    # Try to get comments from database first
    stored_comments = get_comments_from_db(content_id, post_id)
    
    if stored_comments:
        total = stored_comments.get('total_comments', 0)
        comments = stored_comments.get('comments', [])
        print(f'✅ Found {total} comment(s) already in database!')
        
        for i, comment in enumerate(comments, 1):
            author = comment.get('author_name', 'Unknown')
            message = comment.get('message', 'No message')
            created_time = comment.get('created_time', 'Unknown')
            
            print(f'  💬 Comment {i}:')
            print(f'    👤 Author: {author}')
            print(f'    📝 Message: {message}')
            print(f'    🕒 Time: {created_time}')
            print()
        
        return True
    else:
        print('❌ No comments found in database!')
        print('   The comments were fetched from Facebook but not stored in unqlite.')
        print()
        print('🔄 Let me fetch and store them now...')
        
        # Get Facebook apps
        apps = get_facebook_apps()
        if not apps:
            print('❌ No Facebook apps found')
            return False
            
        app = apps[0]
        page_id = app.get('page_id')
        access_token = app.get('password')
        
        if not page_id or not access_token:
            print('❌ Invalid Facebook app configuration')
            return False
        
        # Fetch comments from Facebook
        print(f'📡 Fetching comments from Facebook for post: {post_id}')
        comments_result = get_post_comments_from_facebook(page_id, post_id, access_token)
        
        if 'error' in comments_result:
            error_info = comments_result['error']
            print(f'❌ Error fetching comments from Facebook: {error_info}')
            return False
        
        comments_data = comments_result.get('data', [])
        if not comments_data:
            print('❌ No comments data received from Facebook')
            return False
        
        print(f'📥 Attempting to store {len(comments_data)} comment(s) in database...')
        
        # Store comments in database
        success = store_comments_in_db(post_id, content_id, comments_data)
        
        if success:
            print('✅ Comments successfully stored in unqlite database!')
            
            # Verify storage by reading back
            print('🔍 Verifying storage...')
            stored_comments = get_comments_from_db(content_id, post_id)
            
            if stored_comments:
                total = stored_comments.get('total_comments', 0)
                comments = stored_comments.get('comments', [])
                print(f'✅ Verification successful: {total} comment(s) now in database')
                
                # Display stored comments
                for i, comment in enumerate(comments, 1):
                    author = comment.get('author_name', 'Unknown')
                    message = comment.get('message', 'No message')
                    created_time = comment.get('created_time', 'Unknown')
                    
                    print(f'  💬 Stored Comment {i}:')
                    print(f'    👤 Author: {author}')
                    print(f'    📝 Message: {message}')
                    print(f'    🕒 Time: {created_time}')
                    print()
                
                return True
            else:
                print('❌ Verification failed: Comments not found after storage attempt')
                return False
        else:
            print('❌ Failed to store comments in database')
            return False

def main():
    print("UnQLite Comment Storage Check")
    print("="*60)
    
    try:
        success = check_and_store_comments()
        
        print("\n" + "="*60)
        if success:
            print("🎉 SUCCESS: Comments are now stored in the unqlite database!")
            print("   ✅ Comment fetching from Facebook API: Working")
            print("   ✅ Comment storage in unqlite database: Working")
            print("   ✅ Comment retrieval from database: Working")
        else:
            print("❌ FAILED: Comments could not be stored in the database")
            print("   This could be due to:")
            print("   - Database permission issues")
            print("   - Invalid Facebook tokens")
            print("   - Network connectivity problems")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during comment storage check: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
