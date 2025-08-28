"""
Demo script showing how to use the new comment functionality.

This script demonstrates how to:
1. Fetch comments from Facebook for posted content
2. Store comments in the database
3. Retrieve stored comments
4. Bulk fetch comments for all posts

The comment.py module provides the following API endpoints:

1. GET /admin-panel/api/posts
   - Lists all posted content that has been posted to Facebook

2. POST /admin-panel/api/content/<content_id>/comments/fetch
   - Fetches comments from Facebook for a specific post
   - Requires: page_id, post_id, optional: limit (default 25)

3. GET /admin-panel/api/content/<content_id>/comments
   - Gets stored comments for specific content
   - Optional query param: post_id

4. POST /admin-panel/api/posts/<post_id>/comments/refresh
   - Refreshes comments for a specific Facebook post
   - Requires: page_id, content_id, optional: limit (default 50)

5. POST /admin-panel/api/comments/bulk-fetch
   - Fetches comments for all posted content at once

Usage Examples:

# 1. List all posted content
curl -X GET "http://localhost:5000/admin-panel/api/posts" \
     -H "Content-Type: application/json"

# 2. Fetch comments for specific content
curl -X POST "http://localhost:5000/admin-panel/api/content/12345/comments/fetch" \
     -H "Content-Type: application/json" \
     -d '{
       "page_id": "your_page_id",
       "post_id": "your_facebook_post_id",
       "limit": 25
     }'

# 3. Get stored comments
curl -X GET "http://localhost:5000/admin-panel/api/content/12345/comments" \
     -H "Content-Type: application/json"

# 4. Refresh comments for a post
curl -X POST "http://localhost:5000/admin-panel/api/posts/facebook_post_id/comments/refresh" \
     -H "Content-Type: application/json" \
     -d '{
       "page_id": "your_page_id",
       "content_id": "12345",
       "limit": 50
     }'

# 5. Bulk fetch all comments
curl -X POST "http://localhost:5000/admin-panel/api/comments/bulk-fetch" \
     -H "Content-Type: application/json"

Database Structure:

The comments are stored in the UnQLite database using the following structure:

Key: comments:<content_id>:<post_id>
Value: {
    "post_id": "facebook_post_id",
    "content_id": "internal_content_id",
    "comments": [
        {
            "id": "comment_id",
            "message": "comment text",
            "created_time": "2024-01-01T00:00:00+0000",
            "from": {
                "name": "Commenter Name",
                "id": "commenter_id"
            },
            "like_count": 5,
            "comment_count": 2,
            "replies": [
                {
                    "id": "reply_id",
                    "message": "reply text",
                    "created_time": "2024-01-01T00:01:00+0000",
                    "from": {
                        "name": "Replier Name",
                        "id": "replier_id"
                    },
                    "like_count": 1
                }
            ]
        }
    ],
    "last_updated": "2024-01-01T00:00:00",
    "total_comments": 1
}

Features:

- Admin authentication required for all endpoints
- Automatic storage of fetched comments in UnQLite database
- Support for comment replies (nested comments)
- Bulk operations for fetching comments from all posts
- Error handling for Facebook API issues
- Configurable comment limits
- Comments include metadata like like counts and timestamps

"""

print("Comment functionality has been successfully implemented!")
print("See this file for usage examples and API documentation.")
print("\nTo start using:")
print("1. Make sure your Flask app is running")
print("2. Ensure you're logged in as an admin user")
print("3. Use the provided API endpoints to manage comments")
print("\nKey files created/modified:")
print("- routes/comment.py (new comment blueprint)")
print("- flask_app.py (updated to register comment blueprint)")
