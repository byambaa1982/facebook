# Instagram Posting Documentation

This directory contains standalone scripts for posting to Instagram Business accounts using the system user token from Facebook Graph API.

## Files Overview

### 1. `test_post_instagram.py`
Comprehensive test suite for Instagram posting functionality including:
- System user token validation
- Facebook page and Instagram account discovery
- API permissions checking
- Mocked posting tests
- Complete workflow testing

### 2. `instagram_post_standalone.py`
Production-ready standalone script for posting to Instagram with:
- Command-line interface
- Text and image posting support
- Multiple account management
- Dry run mode for safe testing
- Comprehensive error handling

## Prerequisites

### Required Permissions
Your Facebook app must have the following permissions:
- `instagram_basic` - Basic Instagram account access
- `instagram_content_publish` - Publish content to Instagram
- `pages_show_list` - List Facebook pages
- `pages_read_engagement` - Read page engagement data

### Instagram Business Account Setup
1. Have an Instagram Business Account
2. Connect it to a Facebook Page
3. Ensure the Facebook Page is managed by your Facebook app
4. Grant necessary permissions in Facebook Business Manager

## Installation

```bash
pip install requests
```

## Usage

### Running Tests

```bash
cd routes
python test_post_instagram.py
```

### List Available Instagram Accounts

```bash
python instagram_post_standalone.py --list
```

Example output:
```
============================================================
INSTAGRAM BUSINESS ACCOUNTS
============================================================
Found 1 Instagram business account(s):

[0] @byambadata
    Page: Эхлэл
    Instagram ID: 17841477161770672
    Followers: 7
```

### Post Text Content (Dry Run)

```bash
python instagram_post_standalone.py --caption "Your post text here"
```

### Post Text Content (Live)

```bash
python instagram_post_standalone.py --caption "Your post text here" --live
```

### Post Image with Caption

```bash
python instagram_post_standalone.py --caption "Check out this image!" --image "https://example.com/image.jpg" --live
```

### Use Specific Account (if multiple)

```bash
python instagram_post_standalone.py --caption "Post text" --account 1 --live
```

### Quick Test Post

```bash
python instagram_post_standalone.py --caption "test"
```
This will create a timestamped test post.

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--list` | List available Instagram accounts | `--list` |
| `--caption` | Post caption text (required) | `--caption "Hello World"` |
| `--image` | URL of image to post | `--image "https://example.com/pic.jpg"` |
| `--account` | Account index to use (default: 0) | `--account 1` |
| `--live` | Perform actual posting (default is dry run) | `--live` |

## API Workflow

### Text Post Workflow
1. Load system user token from `system_user.json`
2. Get Facebook pages using system user token
3. Find Instagram business accounts connected to pages
4. Create media container with caption
5. Publish media container to Instagram

### Image Post Workflow
1. Same as text post but includes image URL in media container
2. Instagram processes the image from the provided URL
3. Image must be publicly accessible and meet Instagram requirements

## Example Outputs

### Successful Dry Run
```
============================================================
INSTAGRAM POSTING
============================================================
Timestamp: 2025-09-01 13:16:45
Mode: DRY RUN

1. Loading system user token...
   ✓ Token loaded: EAAMU4HhUxE4BPa1l1rS...

2. Getting Instagram business accounts...
   ✓ Found 1 Instagram account(s):
     [0] @byambadata (7 followers)

3. Selected account: @byambadata
   Instagram ID: 17841477161770672

4. Preparing text post...
   Caption: Test post from automation script

5. DRY RUN - Simulating post creation...
   ✓ Would create media container
   ✓ Would publish media
   ⚠ No actual posting performed

✓ Success: Dry run completed successfully
```

### Successful Live Post
```
============================================================
INSTAGRAM POSTING
============================================================
Mode: LIVE POSTING

1. Loading system user token...
   ✓ Token loaded: EAAMU4HhUxE4BPa1l1rS...

5. Creating media container...
   ✓ Media container created: 18012345678901234

6. Publishing media...
   ✓ Media published successfully!
   Post ID: 18012345678901234_17841477161770672

✓ Success: Post published successfully
  Post ID: 18012345678901234_17841477161770672
  Account: @byambadata
```

## Test Results

The test suite validates:

✅ **System User Token Loading** - Loads token from JSON file with typo handling  
✅ **Facebook Pages Discovery** - Finds pages managed by the app  
✅ **Instagram Account Detection** - Identifies connected Instagram business accounts  
✅ **API Permissions Validation** - Checks required Instagram posting permissions  
✅ **Media Container Creation** - Tests container creation with mocked API  
✅ **Media Publishing** - Tests publishing with mocked API  
✅ **Complete Workflow** - End-to-end workflow testing  

All tests pass successfully with the current system user configuration.

## Current Setup Status

Based on test results:
- ✅ System user token is valid
- ✅ 1 Facebook page found: "Эхлэл"
- ✅ 1 Instagram business account connected: @byambadata
- ✅ All required permissions granted
- ✅ Ready for live posting

## Troubleshooting

### Common Issues

1. **No Instagram Business Accounts Found**
   ```
   No Instagram business accounts found
   ```
   **Solution:** Connect your Instagram Business Account to your Facebook Page in Facebook Business Manager

2. **Permission Errors**
   ```
   ✗ instagram_content_publish: missing
   ```
   **Solution:** Request additional permissions in Facebook App settings and get them approved

3. **Media Container Creation Failed**
   ```
   Media container creation failed: 400 - {"error":{"message":"Invalid image URL"}}
   ```
   **Solution:** Ensure image URL is publicly accessible and meets Instagram requirements:
   - HTTPS URL
   - JPG or PNG format
   - Maximum 8MB file size
   - Minimum 320px width

4. **Token Expired**
   ```
   Error getting pages: {"error":{"message":"Error validating access token"}}
   ```
   **Solution:** Generate a new system user token and update `system_user.json`

### Image Requirements

For image posts, ensure your images meet Instagram's requirements:
- **Format:** JPG or PNG
- **Size:** Maximum 8MB
- **Dimensions:** Minimum 320px width
- **Aspect Ratio:** Between 4:5 and 1.91:1
- **URL:** Must be publicly accessible via HTTPS

### Rate Limits

Instagram has rate limits for posting:
- **Per User:** 25 posts per day
- **Per App:** Varies based on app usage
- **Burst Posting:** Avoid posting multiple times quickly

## Security Notes

- Keep `system_user.json` secure and never commit to public repositories
- Use environment variables for production deployments
- Regularly monitor posting activity and token usage
- Be aware of Instagram's community guidelines and terms of service

## Integration Examples

### Python Script Integration
```python
from instagram_post_standalone import post_to_instagram

result = post_to_instagram(
    caption="Automated post from my application",
    image_url="https://myapp.com/images/post.jpg",
    dry_run=False
)

if result['success']:
    print(f"Posted successfully: {result['post_id']}")
else:
    print(f"Posting failed: {result['message']}")
```

### Scheduled Posting
Use with cron jobs or task schedulers for automated posting:
```bash
# Post daily at 9 AM
0 9 * * * cd /path/to/project && python instagram_post_standalone.py --caption "Daily update" --live
```

## Future Enhancements

Potential improvements for the scripts:
- Support for Instagram Stories
- Video posting capabilities
- Carousel (multiple image) posts
- Post scheduling functionality
- Analytics and insights retrieval
- Comment management features
