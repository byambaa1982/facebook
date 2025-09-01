#!/usr/bin/env python3
"""
Fetch Comments from Latest Facebook Post - Standalone Version
==============================================================
"""

import requests
import json
import os
from datetime import datetime

def get_facebook_apps():
    """Get all Facebook apps from creds.json"""
    apps = []
    
    try:
        # Try routes/creds.json first, then test/creds.json
        for creds_path in ['routes/creds.json', 'test/creds.json']:
            if os.path.exists(creds_path):
                print(f"📂 Reading credentials from: {creds_path}")
                
                with open(creds_path, 'r', encoding='utf-8') as f:
                    creds_data = json.load(f)
                
                # First try root level tokens (these are often more recent)
                if 'page_id' in creds_data and 'page_token' in creds_data:
                    print("✅ Using root-level tokens from creds.json")
                    app_data = {
                        'page_id': creds_data.get('page_id'),
                        'username': 'Facebook Page',
                        'password': creds_data.get('page_token'),
                        'category': 'Page',
                        'tasks': []
                    }
                    apps.append(app_data)
                    break
                
                # Fallback to data array tokens
                elif 'data' in creds_data and creds_data['data']:
                    print("⚠️  Using data array tokens from creds.json")
                    for app in creds_data['data']:
                        # Transform the data structure
                        app_data = {
                            'page_id': app.get('id'),  # Map 'id' to 'page_id'
                            'username': app.get('name'),  # Map 'name' to 'username'
                            'password': app.get('access_token'),  # Map 'access_token' to 'password'
                            'category': app.get('category'),
                            'tasks': app.get('tasks', [])
                        }
                        apps.append(app_data)
                    break
                    
    except Exception as e:
        print(f"❌ Error getting Facebook apps from creds.json: {e}")
    
    return apps

def get_post_comments_from_facebook(page_id, post_id, access_token):
    """Get comments for a specific Facebook post"""
    try:
        url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
        params = {
            'access_token': access_token,
            'fields': 'id,message,from,created_time,like_count,comment_count',
            'limit': 100
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            return data
            
        return data
        
    except Exception as e:
        return {'error': {'message': str(e), 'type': 'Exception'}}

def main():
    print("🔍 Fetching comments from your latest Facebook post...")
    print("=" * 60)
    
    # Get Facebook apps
    apps = get_facebook_apps()
    if not apps:
        print("❌ No Facebook apps found")
        print("💡 Make sure you have run get_token.py and have valid credentials")
        return
        
    app = apps[0]
    page_id = app.get('page_id')
    access_token = app.get('password')
    
    if not page_id or not access_token:
        print("❌ Invalid credentials - missing page_id or access_token")
        print(f"   page_id: {page_id}")
        print(f"   access_token: {'***' + access_token[-10:] if access_token else 'None'}")
        return
    
    print(f"📱 Using page ID: {page_id}")
    print(f"🔑 Access token: {'***' + access_token[-10:] if access_token else 'None'}")
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
            print(f"   Error type: {error_info.get('type', 'Unknown')}")
            print(f"   Error code: {error_info.get('code', 'Unknown')}")
            print(f"   Error message: {error_info.get('message', 'Unknown')}")
            
            # Provide helpful troubleshooting tips
            if error_info.get('code') == 190:
                print("\n💡 Troubleshooting tips:")
                print("   - Your access token may have expired")
                print("   - Run get_token.py again to generate a new token")
                print("   - Make sure your Facebook app has the correct permissions")
            
            return
            
        posts = data.get('data', [])
        print(f"✅ Found {len(posts)} recent posts")
        
        if not posts:
            print("ℹ️  No posts found on your Facebook page")
            print("   This could mean:")
            print("   - Your page doesn't have any posts yet")
            print("   - The access token doesn't have permission to read posts")
            print("   - Your page visibility settings are restrictive")
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
            print(f"   Error type: {error_info.get('type', 'Unknown')}")
            print(f"   Error message: {error_info.get('message', 'Unknown')}")
            
            # Provide helpful troubleshooting tips for comment errors
            print("\n💡 Troubleshooting tips:")
            print("   - Make sure your access token has 'pages_read_engagement' permission")
            print("   - Check if the post allows public comments")
            print("   - Verify that your Facebook app has the necessary permissions")
            
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
                like_count = comment.get('like_count', 0)
                
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
                print(f"   👍 Likes: {like_count}")
                print(f"   🆔 ID: {comment_id}")
                print("   " + "-" * 50)
                
            print(f"\n🎯 Summary: {total_comments} comment(s) found on your latest post")
            
        else:
            print("ℹ️  No comments found on this post")
            print("   This might mean:")
            print("   - The post doesn't have any comments yet")
            print("   - Comments are not publicly visible")
            print("   - The access token doesn't have permission to read comments")
            print("   - Comment settings on the post are restrictive")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error occurred: {str(e)}")
        print("   Check your internet connection and try again")
        
    except Exception as e:
        print(f"❌ Unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
