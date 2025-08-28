from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from db.models import User
from db import db
from flask_login import current_user, login_required
from functools import wraps
import json
import os
import requests
from datetime import datetime
from unqlite import UnQLite

bp_comment = Blueprint('comment', __name__, template_folder='../templates', static_folder='../static')

def admin_required(f):
    """Decorator to ensure user has admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        if not hasattr(current_user, 'role') or current_user.role.name != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def get_unqlite_db():
    """Get UnQLite database connection (for content storage)"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'data.db')
    return UnQLite(db_path)

def get_facebook_apps():
    """Get all Facebook apps from creds.json"""
    apps = []
    
    try:
        # Read from local creds.json file in routes directory
        creds_path = os.path.join(os.path.dirname(__file__), 'creds.json')
        
        if not os.path.exists(creds_path):
            print(f"Credentials file not found: {creds_path}")
            return apps
        
        with open(creds_path, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
        
        if 'data' in creds_data:
            for app in creds_data['data']:
                # Transform the data structure to match what the rest of the code expects
                app_data = {
                    'page_id': app.get('id'),  # Map 'id' to 'page_id'
                    'username': app.get('name'),  # Map 'name' to 'username'
                    'password': app.get('access_token'),  # Map 'access_token' to 'password'
                    'category': app.get('category'),
                    'tasks': app.get('tasks', [])
                }
                apps.append(app_data)
                
    except Exception as e:
        print(f"Error getting Facebook apps from creds.json: {e}")
    
    return apps

def get_posts_from_db():
    """Get all posts from the database"""
    db = get_unqlite_db()
    posts = []
    
    try:
        # Iterate through all keys to find content entries
        for key in db:
            key_str = key.decode('utf-8')
            if key_str.startswith('content:'):
                try:
                    value = db[key]
                    content_data = json.loads(value.decode('utf-8'))
                    
                    # Only include posts that have been posted to Facebook
                    if content_data.get('posted_to_facebook') and content_data.get('facebook_post_id'):
                        posts.append({
                            'id': key_str.replace('content:', ''),
                            'title': content_data.get('title', ''),
                            'description': content_data.get('description', ''),
                            'facebook_post_id': content_data.get('facebook_post_id'),
                            'posted_to_page': content_data.get('posted_to_page'),
                            'posted_at': content_data.get('posted_at'),
                            'content_type': content_data.get('content_type', 'text')
                        })
                except Exception as e:
                    print(f"Error parsing content data for key {key_str}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error getting posts from database: {e}")
    finally:
        db.close()
    
    return posts

def _handle_facebook_response(r):
    """Handle Facebook API response"""
    try:
        r.raise_for_status()
        return r.json()
    except requests.HTTPError:
        # Pretty-print Graph API error
        try:
            error_data = r.json()
            print("Facebook API ERROR:", error_data)
            return {'error': error_data}
        except Exception:
            print("Facebook API ERROR (raw):", r.text)
            return {'error': {'message': r.text}}

def get_post_comments_from_facebook(page_id, access_token, post_id, limit=25):
    """Get comments for a specific Facebook post"""
    graph_url = "https://graph.facebook.com/v21.0"
    url = f"{graph_url}/{post_id}/comments"
    
    params = {
        "fields": "id,message,created_time,from,like_count,comment_count,replies.limit(5){id,message,created_time,from,like_count}",
        "limit": limit,
        "access_token": access_token
    }
    
    response = requests.get(url, params=params)
    return _handle_facebook_response(response)

def delete_facebook_comment(access_token, comment_id):
    """Delete a Facebook comment"""
    graph_url = "https://graph.facebook.com/v21.0"
    url = f"{graph_url}/{comment_id}"
    
    response = requests.delete(url, params={"access_token": access_token})
    return _handle_facebook_response(response)

def reply_to_facebook_comment(access_token, comment_id, message):
    """Reply to a Facebook comment"""
    graph_url = "https://graph.facebook.com/v21.0"
    url = f"{graph_url}/{comment_id}/comments"
    
    data = {
        "message": message,
        "access_token": access_token
    }
    
    response = requests.post(url, data=data)
    return _handle_facebook_response(response)

def store_comments_in_db(post_id, content_id, comments_data):
    """Store comments data in the database"""
    db = get_unqlite_db()
    
    try:
        # Create a key for storing comments
        comments_key = f'comments:{content_id}:{post_id}'
        
        # Prepare comments data for storage
        comments_storage = {
            'post_id': post_id,
            'content_id': content_id,
            'comments': comments_data,
            'last_updated': datetime.now().isoformat(),
            'total_comments': len(comments_data)
        }
        
        # Store comments in database
        db[comments_key] = json.dumps(comments_storage)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"Error storing comments in database: {e}")
        return False
    finally:
        db.close()

def get_comments_from_db(content_id, post_id=None):
    """Get comments from the database"""
    db = get_unqlite_db()
    
    try:
        if post_id:
            # Get comments for specific post
            comments_key = f'comments:{content_id}:{post_id}'
            try:
                value = db[comments_key]
                return json.loads(value.decode('utf-8'))
            except KeyError:
                return None
        else:
            # Get all comments for content
            all_comments = []
            for key in db:
                key_str = key.decode('utf-8')
                if key_str.startswith(f'comments:{content_id}:'):
                    try:
                        value = db[key]
                        comment_data = json.loads(value.decode('utf-8'))
                        all_comments.append(comment_data)
                    except Exception as e:
                        print(f"Error parsing comment data for key {key_str}: {e}")
                        continue
            return all_comments
                        
    except Exception as e:
        print(f"Error getting comments from database: {e}")
        return None
    finally:
        db.close()

@bp_comment.route('/admin-panel/api/posts', methods=['GET'])
@login_required
@admin_required
def list_posted_content():
    """API endpoint to list all posted content"""
    try:
        posts = get_posts_from_db()
        return jsonify({'success': True, 'posts': posts})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/api/content/<content_id>/comments/fetch', methods=['POST'])
@login_required
@admin_required
def fetch_comments_from_facebook(content_id):
    """API endpoint to fetch comments from Facebook for a specific post"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        page_id = data.get('page_id')
        post_id = data.get('post_id')
        limit = data.get('limit', 25)
        
        if not page_id or not post_id:
            return jsonify({'success': False, 'error': 'Page ID and Post ID are required'}), 400
        
        # Get Facebook app data
        facebook_apps = get_facebook_apps()
        selected_app = None
        for app in facebook_apps:
            if app.get('page_id') == page_id:
                selected_app = app
                break
        
        if not selected_app:
            return jsonify({'success': False, 'error': 'Facebook app not found for this page'}), 404
        
        access_token = selected_app.get('password')  # Access token is stored in password field
        if not access_token:
            return jsonify({'success': False, 'error': 'Access token not found for this page'}), 400
        
        # Fetch comments from Facebook
        result = get_post_comments_from_facebook(page_id, access_token, post_id, limit)
        
        # Check if fetching was successful
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            return jsonify({'success': False, 'error': f'Facebook API error: {error_msg}'}), 400
        
        comments_data = result.get('data', [])
        
        # Store comments in database
        if comments_data:
            store_success = store_comments_in_db(post_id, content_id, comments_data)
            if not store_success:
                return jsonify({'success': False, 'error': 'Failed to store comments in database'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Fetched {len(comments_data)} comments successfully',
            'comments_count': len(comments_data),
            'comments': comments_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/api/content/<content_id>/comments', methods=['GET'])
@login_required
@admin_required
def get_stored_comments(content_id):
    """API endpoint to get stored comments for a specific content"""
    try:
        post_id = request.args.get('post_id')
        comments_data = get_comments_from_db(content_id, post_id)
        
        if comments_data is None:
            return jsonify({'success': False, 'error': 'No comments found'}), 404
        
        if isinstance(comments_data, list):
            # Multiple posts comments
            total_comments = sum(item.get('total_comments', 0) for item in comments_data)
            return jsonify({
                'success': True,
                'comments_data': comments_data,
                'total_posts': len(comments_data),
                'total_comments': total_comments
            })
        else:
            # Single post comments
            return jsonify({
                'success': True,
                'comments_data': comments_data,
                'total_comments': comments_data.get('total_comments', 0)
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/api/posts/<post_id>/comments/refresh', methods=['POST'])
@login_required
@admin_required
def refresh_post_comments(post_id):
    """API endpoint to refresh comments for a specific Facebook post"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        page_id = data.get('page_id')
        content_id = data.get('content_id')
        limit = data.get('limit', 50)
        
        if not page_id or not content_id:
            return jsonify({'success': False, 'error': 'Page ID and Content ID are required'}), 400
        
        # Get Facebook app data
        facebook_apps = get_facebook_apps()
        selected_app = None
        for app in facebook_apps:
            if app.get('page_id') == page_id:
                selected_app = app
                break
        
        if not selected_app:
            return jsonify({'success': False, 'error': 'Facebook app not found for this page'}), 404
        
        access_token = selected_app.get('password')
        if not access_token:
            return jsonify({'success': False, 'error': 'Access token not found for this page'}), 400
        
        # Fetch latest comments from Facebook
        result = get_post_comments_from_facebook(page_id, access_token, post_id, limit)
        
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            return jsonify({'success': False, 'error': f'Facebook API error: {error_msg}'}), 400
        
        comments_data = result.get('data', [])
        
        # Update stored comments
        if comments_data:
            store_success = store_comments_in_db(post_id, content_id, comments_data)
            if not store_success:
                return jsonify({'success': False, 'error': 'Failed to update comments in database'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Refreshed comments successfully',
            'comments_count': len(comments_data),
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/api/comments/bulk-fetch', methods=['POST'])
@login_required
@admin_required
def bulk_fetch_comments():
    """API endpoint to fetch comments for all posted content"""
    try:
        # Get all posted content
        posts = get_posts_from_db()
        
        if not posts:
            return jsonify({'success': False, 'error': 'No posted content found'}), 404
        
        # Get Facebook apps for access tokens
        facebook_apps = get_facebook_apps()
        apps_by_page_id = {app.get('page_id'): app for app in facebook_apps}
        
        results = []
        total_comments_fetched = 0
        
        for post in posts:
            page_id = post.get('posted_to_page')
            post_id = post.get('facebook_post_id')
            content_id = post.get('id')
            
            if not page_id or not post_id:
                continue
            
            # Get access token for this page
            app = apps_by_page_id.get(page_id)
            if not app:
                results.append({
                    'content_id': content_id,
                    'post_id': post_id,
                    'success': False,
                    'error': 'No access token found for page'
                })
                continue
            
            access_token = app.get('password')
            if not access_token:
                results.append({
                    'content_id': content_id,
                    'post_id': post_id,
                    'success': False,
                    'error': 'Invalid access token'
                })
                continue
            
            # Fetch comments for this post
            try:
                result = get_post_comments_from_facebook(page_id, access_token, post_id, 25)
                
                if 'error' in result:
                    results.append({
                        'content_id': content_id,
                        'post_id': post_id,
                        'success': False,
                        'error': result['error'].get('message', 'Unknown error')
                    })
                    continue
                
                comments_data = result.get('data', [])
                
                # Store comments
                if comments_data:
                    store_success = store_comments_in_db(post_id, content_id, comments_data)
                    if store_success:
                        total_comments_fetched += len(comments_data)
                        results.append({
                            'content_id': content_id,
                            'post_id': post_id,
                            'success': True,
                            'comments_count': len(comments_data)
                        })
                    else:
                        results.append({
                            'content_id': content_id,
                            'post_id': post_id,
                            'success': False,
                            'error': 'Failed to store comments'
                        })
                else:
                    results.append({
                        'content_id': content_id,
                        'post_id': post_id,
                        'success': True,
                        'comments_count': 0
                    })
                    
            except Exception as e:
                results.append({
                    'content_id': content_id,
                    'post_id': post_id,
                    'success': False,
                    'error': str(e)
                })
        
        successful_fetches = len([r for r in results if r.get('success')])
        
        return jsonify({
            'success': True,
            'message': f'Bulk fetch completed',
            'total_posts_processed': len(posts),
            'successful_fetches': successful_fetches,
            'total_comments_fetched': total_comments_fetched,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/api/comments/<comment_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_comment(comment_id):
    """API endpoint to delete a Facebook comment"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        page_id = data.get('page_id')
        if not page_id:
            return jsonify({'success': False, 'error': 'Page ID is required'}), 400
        
        # Get Facebook app data
        facebook_apps = get_facebook_apps()
        selected_app = None
        for app in facebook_apps:
            if app.get('page_id') == page_id:
                selected_app = app
                break
        
        if not selected_app:
            return jsonify({'success': False, 'error': 'Facebook app not found for this page'}), 404
        
        access_token = selected_app.get('password')
        if not access_token:
            return jsonify({'success': False, 'error': 'Access token not found for this page'}), 400
        
        # Delete comment from Facebook
        result = delete_facebook_comment(access_token, comment_id)
        
        # Check if deletion was successful
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            return jsonify({'success': False, 'error': f'Facebook API error: {error_msg}'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully',
            'comment_id': comment_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/api/comments/<comment_id>/reply', methods=['POST'])
@login_required
@admin_required
def reply_to_comment(comment_id):
    """API endpoint to reply to a Facebook comment"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        page_id = data.get('page_id')
        message = data.get('message')
        
        if not page_id or not message:
            return jsonify({'success': False, 'error': 'Page ID and message are required'}), 400
        
        # Get Facebook app data
        facebook_apps = get_facebook_apps()
        selected_app = None
        for app in facebook_apps:
            if app.get('page_id') == page_id:
                selected_app = app
                break
        
        if not selected_app:
            return jsonify({'success': False, 'error': 'Facebook app not found for this page'}), 404
        
        access_token = selected_app.get('password')
        if not access_token:
            return jsonify({'success': False, 'error': 'Access token not found for this page'}), 400
        
        # Reply to comment on Facebook
        result = reply_to_facebook_comment(access_token, comment_id, message)
        
        # Check if reply was successful
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            return jsonify({'success': False, 'error': f'Facebook API error: {error_msg}'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Reply posted successfully',
            'reply_id': result.get('id'),
            'comment_id': comment_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_comment.route('/admin-panel/comments')
@login_required
@admin_required
def comments_management():
    """Frontend page for managing Facebook comments"""
    return render_template('admin/comments_management.html')
