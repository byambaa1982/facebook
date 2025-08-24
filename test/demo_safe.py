#!/usr/bin/env python3
"""
Facebook Page Manager Safe Demo Script

This script demonstrates the basic functionality of the FacebookPageManager class
with safe, read-only operations by default. Posting is disabled unless explicitly enabled.
"""

from faceClass import FacebookPageManager
from datetime import datetime
import os

def main():
    print("🚀 FACEBOOK PAGE MANAGER SAFE DEMO")
    print("=" * 50)
    
    try:
        # Initialize Facebook Page Manager
        fb = FacebookPageManager()
        
        # Display page info
        print("\n📄 Page Information:")
        page_info = fb.get_page_info()
        if page_info:
            print(f"   Name: {page_info.get('name')}")
            print(f"   Category: {page_info.get('category')}")
            print(f"   Followers: {page_info.get('fan_count', 'N/A')}")
            print(f"   About: {page_info.get('about', 'N/A')}")
        
        # Show recent activity
        print("\n📊 Recent Activity:")
        fb.print_activity_summary(days=7)
        
        # Demo: Safe operations (read-only)
        print("\n🔍 Recent Posts Preview:")
        posts = fb.get_page_posts(limit=3)
        for i, post in enumerate(posts):
            message = post.get('message', 'No message')[:100]
            reactions = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
            comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
            created = post.get('created_time', 'Unknown')
            print(f"\n   Post {i+1}:")
            print(f"   📝 {message}...")
            print(f"   👍 {reactions} reactions, 💬 {comments} comments")
            print(f"   📅 {created}")
        
        # Demo: Comment operations (safe to test)
        if posts:
            test_post_id = posts[0]['id']
            print(f"\n💬 Comments on latest post ({test_post_id}):")
            comments = fb.get_post_comments(test_post_id, limit=5)
            if comments:
                for i, comment in enumerate(comments):
                    message = comment.get('message', 'No message')[:50]
                    author = comment.get('from', {}).get('name', 'Unknown')
                    print(f"   {i+1}. {author}: {message}...")
            else:
                print("   No comments found")
        
        # OPTIONAL: Test posting (disabled by default)
        print("\n🔒 POSTING DEMO (DISABLED)")
        print("To enable posting, uncomment the lines below in demo_safe.py:")
        print()
        print("# Test text post")
        print("# post_id = fb.post_text('Demo post from FacebookPageManager! 🤖')")
        print("# if post_id:")
        print("#     print(f'✅ Demo post created: {post_id}')")
        print("#     # Test comment on own post")
        print("#     comment_id = fb.write_comment(post_id, 'This is an automated demo comment!')")
        print("#     if comment_id:")
        print("#         print(f'✅ Demo comment added: {comment_id}')")
        print()
        print("# Test photo post (if duckdb.png exists)")
        print("# if os.path.exists('duckdb.png'):")
        print("#     photo_id = fb.post_photo('duckdb.png', 'Demo photo via API! 📸')")
        print("#     if photo_id:")
        print("#         print(f'✅ Demo photo posted: {photo_id}')")
        
        print("\n✅ Safe demo completed successfully!")
        print("💡 Run 'python test.py' to validate your token and permissions")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("\nCommon solutions:")
        print("  1. Run 'python get_token.py' to regenerate your Page Access Token")
        print("  2. Ensure config.json has valid page_id and page_token")
        print("  3. Check that your Facebook app has the required permissions")


if __name__ == "__main__":
    main()
