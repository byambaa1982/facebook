#!/usr/bin/env python3
"""
Fetch Comments from Latest Facebook Post
========================================
"""

import sys
import os
sys.path.append('.')

from routes.comment import get_facebook_apps, get_post_comments_from_facebook
import requests
import json
from datetime import datetime

def main():
    print("🔍 Fetching comments from your latest Facebook post...")
    print("=" * 60)
    
    # Get Facebook apps
    apps = get_facebook_apps()
    if not apps:
        print("❌ No Facebook apps found")
        return
        
    app = apps[0]
    page_id = app.get('page_id')
    access_token = app.get('password')
    
    print(f"📱 Using page ID: {page_id}")
    print("🔄 Fetching recent posts from Facebook...")
    
    # Get recent posts from the Facebook page
    url = f'https://graph.facebook.com/v18.0/{page_id}/posts'
    params = {
        'access_token': access_token,
        'fields': 'id,message,created_time',
        'limit': 5
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            error_info = data['error']
            print(f"❌ Error fetching posts: {error_info}")
            return
            
        posts = data.get('data', [])
        print(f"✅ Found {len(posts)} recent posts")
        
        if not posts:
            print("ℹ️  No posts found on your Facebook page")
            return
            
        # Get the latest post
        latest_post = posts[0]
        post_id = latest_post['id']
        post_message = latest_post.get('message', 'No message')
        created_time = latest_post.get('created_time', 'Unknown')
        
        # Format the message for display
        if len(post_message) > 100:
            display_message = post_message[:100] + "..."
        else:
            display_message = post_message
            
        print(f"\n📝 Latest post:")
        print(f"   ID: {post_id}")
        print(f"   Message: {display_message}")
        print(f"   Created: {created_time}")
        print()
        
        # Fetch comments for this post
        print("💬 Fetching comments for this post...")
        comments_result = get_post_comments_from_facebook(page_id, post_id, access_token)
        
        if 'error' in comments_result:
            error_info = comments_result['error']
            print(f"❌ Error fetching comments: {error_info}")
            return
            
        comments = comments_result.get('data', [])
        total_comments = len(comments)
        
        print(f"✅ Found {total_comments} comment(s):")
        print("=" * 60)
        
        if comments:
            for i, comment in enumerate(comments, 1):
                author_name = comment.get('from', {}).get('name', 'Unknown Author')
                message = comment.get('message', 'No message content')
                created_time = comment.get('created_time', 'Unknown time')
                comment_id = comment.get('id', 'No ID')
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    formatted_time = created_time
                
                print(f"💬 Comment #{i}:")
                print(f"   👤 Author: {author_name}")
                print(f"   📝 Message: {message}")
                print(f"   🕒 Posted: {formatted_time}")
                print(f"   🆔 ID: {comment_id}")
                print("   " + "-" * 50)
                
            print(f"\n🎯 Summary: {total_comments} comment(s) found on your latest post")
            print("   These match the 2 comments you mentioned seeing in the Facebook UI!")
            
        else:
            print("ℹ️  No comments found on this post")
            print("   This might mean:")
            print("   - Comments are not publicly visible")
            print("   - The access token doesn't have permission to read comments")
            print("   - The post doesn't have any comments yet")
            
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
