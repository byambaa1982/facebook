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

bp_post = Blueprint('post', __name__, template_folder='../templates', static_folder='../static')

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

def get_content_by_id(content_id):
    """Get content by ID from database"""
    db = get_unqlite_db()
    try:
        key = f'content:{content_id}'
        value = db[key]
        content_data = json.loads(value.decode('utf-8'))
        
        # Add filename for easier access
        if content_data.get('file_path'):
            content_data['filename'] = os.path.basename(content_data['file_path'])
        
        return content_data
    except KeyError:
        return None
    except Exception as e:
        print(f"Error getting content: {e}")
        return None
    finally:
        db.close()

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

def post_text_to_facebook(page_id, access_token, message):
    """Post text to Facebook page"""
    graph_url = "https://graph.facebook.com/v21.0"
    url = f"{graph_url}/{page_id}/feed"
    
    response = requests.post(url, data={
        "message": message,
        "access_token": access_token
    })
    
    return _handle_facebook_response(response)

def post_photo_to_facebook(page_id, access_token, image_path, caption=""):
    """Post photo to Facebook page"""
    graph_url = "https://graph.facebook.com/v21.0"
    url = f"{graph_url}/{page_id}/photos"
    
    try:
        with open(image_path, "rb") as img_file:
            response = requests.post(
                url,
                data={
                    "caption": caption,
                    "access_token": access_token
                },
                files={"source": img_file}
            )
        
        return _handle_facebook_response(response)
    except FileNotFoundError:
        return {'error': {'message': f'Image file not found: {image_path}'}}
    except Exception as e:
        return {'error': {'message': f'Error posting photo: {str(e)}'}}

@bp_post.route('/admin-panel/api/content/<content_id>/post', methods=['POST'])
@login_required
@admin_required
def post_content_to_facebook(content_id):
    """API endpoint to post content to Facebook"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        page_id = data.get('page_id')
        if not page_id:
            return jsonify({'success': False, 'error': 'Page ID is required'}), 400
        
        # Get content from database
        content = get_content_by_id(content_id)
        if not content:
            return jsonify({'success': False, 'error': 'Content not found'}), 404
        
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
        
        # Prepare post message
        post_message = f"{content['title']}\n\n{content['description']}"
        if content.get('tags'):
            tags = content['tags'].split(',')
            hashtags = ' '.join([f'#{tag.strip()}' for tag in tags if tag.strip()])
            post_message += f"\n\n{hashtags}"
        
        # Post based on content type
        result = None
        if content['content_type'] == 'text':
            result = post_text_to_facebook(page_id, access_token, post_message)
        elif content['content_type'] == 'image' and content.get('file_path'):
            result = post_photo_to_facebook(page_id, access_token, content['file_path'], post_message)
        else:
            return jsonify({'success': False, 'error': 'Unsupported content type or missing file'}), 400
        
        # Check if posting was successful
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            return jsonify({'success': False, 'error': f'Facebook API error: {error_msg}'}), 400
        
        # Update content with post information
        db = get_unqlite_db()
        try:
            content['posted_to_facebook'] = True
            content['facebook_post_id'] = result.get('id') or result.get('post_id')
            content['posted_at'] = datetime.now().isoformat()
            content['posted_by'] = current_user.username
            content['posted_to_page'] = page_id
            
            key = f'content:{content_id}'
            db[key] = json.dumps(content)
            db.commit()
        finally:
            db.close()
        
        return jsonify({
            'success': True, 
            'message': 'Content posted to Facebook successfully!',
            'post_id': result.get('id') or result.get('post_id'),
            'page_name': selected_app.get('username', 'Unknown Page')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_post.route('/admin-panel/api/facebook-apps/list', methods=['GET'])
@login_required
@admin_required
def list_facebook_apps():
    """API endpoint to list available Facebook apps/pages"""
    try:
        apps = get_facebook_apps()
        # Don't include the full access token for security
        safe_apps = []
        for app in apps:
            safe_app = {
                'page_id': app.get('page_id'),
                'username': app.get('username', 'Unknown Page'),
                'has_token': bool(app.get('password'))
            }
            safe_apps.append(safe_app)
        
        return jsonify({'success': True, 'apps': safe_apps})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500