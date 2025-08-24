# Facebook Page Manager

A comprehensive Python class for managing Facebook Pages through the Graph API. This project includes posting content, managing comments, and reviewing page activity with proper token validation and error handling.

## 🚀 Quick Start

1. **Setup Facebook App**: Create a Facebook App at [developers.facebook.com](https://developers.facebook.com)
2. **Generate Tokens**: Run `python get_token.py` to get your Page Access Token
3. **Test Setup**: Run `python test.py` to validate your configuration
4. **Run Demo**: Run `python demo_safe.py` for a safe demo or use the full `demo.py`

## 📁 Project Structure

```
facebook/
├── faceClass.py        # Main FacebookPageManager class
├── get_token.py        # Token generation script
├── test.py            # Comprehensive test suite
├── demo_safe.py       # Safe demo (read-only operations)
├── demo.py           # Full demo with posting
├── config.json       # Configuration file (auto-generated)
└── README.md         # This file
```

## 🔑 Required Facebook Permissions

Your Facebook app needs these permissions (scopes):

- `pages_manage_posts` - Create/edit/delete Page posts
- `pages_manage_engagement` - Comment/like/reply/moderate as Page
- `pages_read_engagement` - Read comments/reactions
- `pages_show_list` - Fetch Page tokens

## 🛠️ Setup Instructions

### 1. Facebook App Configuration

1. Go to [Facebook Developers](https://developers.facebook.com/apps/)
2. Create a new app (Business type)
3. Add "Facebook Login" product
4. Configure OAuth redirect URIs: `https://localhost/`
5. Update `APP_ID` and `APP_SECRET` in `get_token.py`

### 2. Generate Page Access Token

```bash
python get_token.py
```

This will:
- Open Facebook authorization page
- Guide you through OAuth flow
- Generate and save Page Access Token to `config.json`
- Verify token works correctly

### 3. Validate Setup

```bash
python test.py
```

This comprehensive test will check:
- ✅ Token type (Page vs User token)
- ✅ Required permissions/scopes
- ✅ Basic API operations
- ✅ Comment/engagement capabilities
- ✅ Error handling

## 📖 Usage Examples

### Basic Usage

```python
from faceClass import FacebookPageManager

# Initialize (loads from config.json)
fb = FacebookPageManager()

# Get page info
page_info = fb.get_page_info()
print(f"Page: {page_info['name']}")

# Post text
post_id = fb.post_text("Hello from Python! 🐍")

# Post photo
photo_id = fb.post_photo("image.jpg", "Check out this photo!")

# Add comment
comment_id = fb.write_comment(post_id, "Great post!")

# Get recent posts
posts = fb.get_page_posts(limit=10)

# Review activity
fb.print_activity_summary(days=7)
```

### Safe Demo

```bash
python demo_safe.py
```

Runs read-only operations to test your setup without posting.

### Full Demo

```bash
python demo.py
```

Demonstrates all features including posting (uncomment posting lines to enable).

## 🔧 FacebookPageManager Class

### Core Methods

#### Posting
- `post_text(message, link=None)` - Create text posts
- `post_photo(image_path, caption="")` - Post local images
- `post_photo_url(image_url, caption="")` - Post from URL

#### Comments
- `write_comment(post_id, message)` - Write comments
- `get_post_comments(post_id, limit=25)` - Get post comments
- `reply_to_comment(comment_id, message)` - Reply to comments
- `delete_comment(comment_id)` - Delete comments

#### Engagement
- `like_post(post_id)` - Like posts
- `delete_post(post_id)` - Delete posts

#### Analytics
- `get_page_posts(limit=25)` - Get recent posts
- `get_post_insights(post_id)` - Get post analytics
- `review_recent_activity(days=7)` - Activity summary
- `print_activity_summary(days=7)` - Formatted activity report

#### Info
- `get_page_info()` - Get page details

## 🚨 Troubleshooting

### Common Issues

1. **"User token instead of Page token"**
   ```bash
   python get_token.py  # Regenerate proper Page token
   ```

2. **"Missing permissions"**
   - Check `get_token.py` has all required scopes
   - Regenerate User token with missing permissions
   - Re-fetch Page token via `me/accounts`

3. **"Comment operations fail"**
   - Verify Page role includes MODERATE task
   - Check Page settings > Page roles

4. **"Token expired"**
   ```bash
   python get_token.py  # Generate new tokens
   ```

### Validation Checklist

Run `python test.py` and ensure:
- ✅ Using Page Access Token (not User token)
- ✅ All required scopes present
- ✅ MODERATE permission available
- ✅ Basic operations work
- ✅ No critical errors

### Debug Token Issues

The test suite includes Facebook's recommended validation:

```python
# Check token type and permissions
fb = FacebookPageManager()
tester = FacebookPageTester()
tester.assert_page_token()  # Validates token type
tester.check_required_permissions()  # Validates scopes
```

## 🔒 Security Notes

- Keep `config.json` private (contains access tokens)
- Tokens are long-lived but may expire
- Never commit tokens to version control
- Use environment variables in production

## 📋 Test Results

The test suite generates `test_results.json` with detailed validation:

```json
{
  "token_validation": {
    "is_page_token": true,
    "has_moderate": true,
    "token_name": "Your Page Name"
  },
  "permissions_check": {
    "has_all_required": true,
    "missing_scopes": []
  },
  "basic_operations": {
    "page_info": "PASSED",
    "get_posts": "PASSED"
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## 📚 References

- [Facebook Graph API Documentation](https://developers.facebook.com/docs/graph-api/)
- [Pages API Reference](https://developers.facebook.com/docs/pages-api/)
- [Facebook App Development](https://developers.facebook.com/docs/apps/)

## ⚖️ License

This project is for educational purposes. Follow Facebook's Terms of Service and API usage policies.

---

**Need Help?** Run `python test.py` for comprehensive diagnostics or check the troubleshooting section above.
