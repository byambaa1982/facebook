#!/usr/bin/env python3
"""
Demo script showcasing the FacebookPageManager class functionality.
Run this to test posting, commenting, and reviewing features.
"""

from faceClass import FacebookPageManager
import time

def demo_basic_posting(fb):
    """Demo basic posting functionality."""
    print("\n🚀 === POSTING DEMO ===")
    
    # Text post
    print("1. Creating a text post...")
    post_id = fb.post_text("Hello from Graph API! 🤖 This is a demo post.")

    if post_id:
        # Add a comment to our own post
        print("2. Adding a comment to the post...")
        comment_id = fb.write_comment(post_id, "This is an automated comment! 💬")
        
        # Like the post
        print("3. Liking the post...")
        fb.like_post(post_id)
        
        return post_id, comment_id
    
    return None, None

def demo_photo_posting(fb):
    """Demo photo posting functionality."""
    print("\n📸 === PHOTO POSTING DEMO ===")
    
    # Check if image file exists
    import os
    if os.path.exists("duckdb.png"):
        print("1. Posting a local image...")
        photo_id = fb.post_photo("duckdb.png", "Demo photo posted via FacebookPageManager class! 📷")
        return photo_id
    else:
        print("1. Posting an image from URL...")
        # Using a sample image URL
        photo_id = fb.post_photo_url(
            "https://via.placeholder.com/400x300/0066cc/ffffff?text=Demo+Image",
            "Demo image from URL via FacebookPageManager! 🌐"
        )
        return photo_id

def demo_comment_management(fb, post_id):
    """Demo comment management functionality."""
    if not post_id:
        return
        
    print("\n💬 === COMMENT MANAGEMENT DEMO ===")
    
    # Add multiple comments
    print("1. Adding multiple comments...")
    comment_ids = []
    comments = [
        "Great post! 👍",
        "Thanks for sharing! 🙏",
        "Very informative! 📚"
    ]
    
    for comment_text in comments:
        comment_id = fb.write_comment(post_id, comment_text)
        if comment_id:
            comment_ids.append(comment_id)
        time.sleep(1)  # Small delay to avoid rate limiting
    
    # Get all comments on the post
    print("2. Retrieving all comments...")
    all_comments = fb.get_post_comments(post_id)
    print(f"   Found {len(all_comments)} comments on the post")
    
    for comment in all_comments[:3]:  # Show first 3
        print(f"   • {comment.get('message', 'No message')[:50]}...")
    
    # Reply to the first comment
    if comment_ids:
        print("3. Replying to a comment...")
        fb.reply_to_comment(comment_ids[0], "Thanks for your comment! 😊")

def demo_page_analytics(fb):
    """Demo page analytics and review functionality."""
    print("\n📊 === ANALYTICS & REVIEW DEMO ===")
    
    # Show page information
    print("1. Page Information:")
    page_info = fb.get_page_info()
    if page_info:
        print(f"   📖 Name: {page_info.get('name')}")
        print(f"   👥 Followers: {page_info.get('followers_count', 'N/A')}")
        print(f"   📂 Category: {page_info.get('category', 'N/A')}")
        print(f"   🌐 Website: {page_info.get('website', 'N/A')}")
    
    # Show recent posts
    print("\n2. Recent Posts:")
    recent_posts = fb.get_page_posts(limit=5)
    for i, post in enumerate(recent_posts, 1):
        message = post.get('message', 'No message')
        message = message[:60] + "..." if len(message) > 60 else message
        reactions = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
        comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
        print(f"   {i}. {message}")
        print(f"      👍 {reactions} reactions, 💬 {comments} comments")
    
    # Show activity summary
    print("\n3. Activity Summary:")
    fb.print_activity_summary(days=30)

def demo_content_moderation(fb, post_id, comment_id):
    """Demo content moderation features."""
    if not post_id:
        return
        
    print("\n🛡️ === CONTENT MODERATION DEMO ===")
    
    # This is just for demo - in real usage, be careful about deleting content!
    print("1. Content moderation features available:")
    print("   • Delete inappropriate comments")
    print("   • Delete posts if needed") 
    print("   • Reply to comments for customer service")
    
    # Uncomment these if you want to test deletion (be careful!)
    # if comment_id:
    #     print("2. Deleting a test comment...")
    #     fb.delete_comment(comment_id)
    # 
    # print("3. Deleting the test post...")
    # fb.delete_post(post_id)

def interactive_demo():
    """Interactive demo allowing user to choose what to test."""
    print("🎯 FacebookPageManager Interactive Demo")
    print("=" * 50)
    
    try:
        fb = FacebookPageManager()
        print("✅ Successfully connected to Facebook Page!")
        
        while True:
            print("\nChoose a demo to run:")
            print("1. 📝 Basic Posting (text + comment + like)")
            print("2. 📸 Photo Posting")
            print("3. 💬 Comment Management") 
            print("4. 📊 Page Analytics & Review")
            print("5. 🛡️ Content Moderation Info")
            print("6. 🎬 Run All Demos")
            print("0. ❌ Exit")
            
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                post_id, comment_id = demo_basic_posting(fb)
            elif choice == "2":
                demo_photo_posting(fb)
            elif choice == "3":
                # Need a post ID for this demo
                posts = fb.get_page_posts(limit=1)
                if posts:
                    demo_comment_management(fb, posts[0]['id'])
                else:
                    print("No posts found. Create a post first!")
            elif choice == "4":
                demo_page_analytics(fb)
            elif choice == "5":
                demo_content_moderation(fb, None, None)
            elif choice == "6":
                print("🎬 Running all demos...")
                post_id, comment_id = demo_basic_posting(fb)
                demo_photo_posting(fb)
                demo_comment_management(fb, post_id)
                demo_page_analytics(fb)
                demo_content_moderation(fb, post_id, comment_id)
            else:
                print("❌ Invalid choice. Please try again.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your creds.json file has valid credentials!")

if __name__ == "__main__":
    interactive_demo()
