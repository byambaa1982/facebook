# Facebook Comments Management System

## Overview

The Facebook Comments Management System provides a comprehensive web interface for managing comments on your Facebook posts. This system allows administrators to fetch, view, reply to, and delete comments from posted content.

## Features

### 1. **Comments Fetching**
- Fetch comments from Facebook for specific posts
- Bulk fetch comments for all posted content
- Automatic storage of comments in the local database
- Support for nested comments (replies)

### 2. **Comments Viewing**
- Interactive web interface for viewing comments
- Real-time comment metadata (likes, reply counts, timestamps)
- User information display with avatars
- Hierarchical display of replies

### 3. **Comments Management**
- Reply to comments directly from the interface
- Delete comments from Facebook
- Refresh comments to get latest data
- Filter and search through comments

### 4. **Admin Dashboard Integration**
- Dedicated comments management section in admin dashboard
- Quick access buttons for bulk operations
- Statistics and activity tracking

## How to Use

### Accessing the Comment Management System

1. **Login as Admin**: Ensure you're logged in with admin privileges
2. **Navigate to Dashboard**: Go to `/admin-panel/` 
3. **Access Comments**: Click "Manage Comments" in the Comments Management card

### Managing Comments

#### **Step 1: Load Posted Content**
- Click "Load Posts" to see all content that has been posted to Facebook
- Each post shows title, description, posting date, and Facebook post ID

#### **Step 2: Fetch Comments**
- Click "Fetch Comments" on any post to retrieve comments from Facebook
- Comments are automatically stored in the local database
- Use "Refresh" to get the latest comments for a post

#### **Step 3: View and Manage Comments**
- Click "View Comments" to see all comments for a post
- Comments display user names, timestamps, message content, and engagement metrics
- Replies are shown nested under parent comments

#### **Step 4: Interact with Comments**
- **Reply**: Click the reply button to respond to a comment
- **Delete**: Click the delete button to remove a comment from Facebook
- **View Stats**: See like counts and reply counts for each comment

### Bulk Operations

#### **Bulk Fetch All Comments**
- Use "Bulk Fetch All Comments" from dashboard or comments page
- Fetches comments for all posted content automatically
- Shows progress and results for each post processed

## API Endpoints

The system provides the following REST API endpoints:

### Posts Management
- `GET /admin-panel/api/posts` - List all posted content
- `POST /admin-panel/api/content/<id>/comments/fetch` - Fetch comments for specific post
- `GET /admin-panel/api/content/<id>/comments` - Get stored comments
- `POST /admin-panel/api/posts/<id>/comments/refresh` - Refresh comments

### Comment Actions
- `DELETE /admin-panel/api/comments/<id>/delete` - Delete a comment
- `POST /admin-panel/api/comments/<id>/reply` - Reply to a comment
- `POST /admin-panel/api/comments/bulk-fetch` - Bulk fetch all comments

### Frontend Pages
- `GET /admin-panel/comments` - Comments management interface

## Technical Details

### Database Storage
Comments are stored in UnQLite database with the following structure:
```
Key: comments:<content_id>:<post_id>
Value: {
    "post_id": "facebook_post_id",
    "content_id": "internal_content_id",
    "comments": [...comment_data...],
    "last_updated": "timestamp",
    "total_comments": count
}
```

### Facebook API Integration
- Uses Facebook Graph API v21.0
- Requires valid page access tokens stored in `creds.json`
- Supports comment operations: fetch, delete, reply
- Handles API errors gracefully with user feedback

### Security
- All endpoints require admin authentication
- CSRF protection for state-changing operations
- Secure token handling and validation
- Input sanitization for user messages

## Troubleshooting

### Common Issues

1. **Comments Not Loading**
   - Check Facebook app credentials in `creds.json`
   - Verify page access token permissions
   - Ensure the post exists on Facebook

2. **Permission Errors**
   - Verify admin role assignment
   - Check Facebook page management permissions
   - Validate access token scopes

3. **API Rate Limits**
   - Facebook API has rate limits for comment operations
   - Use bulk fetch sparingly for large numbers of posts
   - Wait between rapid successive API calls

### Error Messages
- **"Access token not found"**: Check `creds.json` configuration
- **"Admin access required"**: Verify user role permissions
- **"Facebook API error"**: Check Facebook token validity and permissions
- **"Content not found"**: Ensure the post was properly stored in database

## File Structure

```
routes/
├── comment.py          # Comment management routes and API
templates/admin/
├── comments_management.html  # Web interface
├── dashboard.html      # Updated with comments section
static/
├── comments.css        # Styling for comment interface
```

## Configuration

Ensure your `routes/creds.json` file contains Facebook app configurations:
```json
{
    "data": [
        {
            "id": "page_id",
            "name": "Page Name",
            "access_token": "page_access_token",
            "category": "page_category"
        }
    ]
}
```

## Support

For issues or questions:
1. Check the console logs for detailed error messages
2. Verify Facebook API documentation for latest changes
3. Test API endpoints individually using tools like Postman
4. Review Flask application logs for server-side errors

---

*Last updated: August 27, 2025*
