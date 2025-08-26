from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from functools import wraps
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from unqlite import UnQLite

# Blueprint for admin routes
admin_bp = Blueprint('custom_admin', __name__, url_prefix='/admin-panel')

def admin_required(f):
    """Decorator to ensure user has admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not hasattr(current_user, 'role') or current_user.role.name != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('home.home'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_unqlite_db():
    """Get UnQLite database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'data.db')
    return UnQLite(db_path)

@admin_bp.route('/')
@login_required
@admin_required
def admin_index():
    """Admin panel home page"""
    try:
        db = get_unqlite_db()
        stats = get_admin_stats(db)
        recent_activities = get_recent_activities(db)
        db.close()
        return render_template('admin/dashboard.html', stats=stats, recent_activities=recent_activities)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('home.home'))

def get_admin_stats(db):
    """Get statistics for admin dashboard"""
    stats = {
        'facebook_apps_count': 0,
        'total_content_count': 0,
        'recent_content_count': 0
    }
    
    try:
        # Count Facebook apps and content
        for key, value in db.items():
            # Handle both string and bytes keys
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = str(key)
                
            if key_str.startswith('user:'):
                stats['facebook_apps_count'] += 1
            elif key_str.startswith('content:'):
                stats['total_content_count'] += 1
                # Check if content is from last 7 days
                try:
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8')
                    else:
                        value_str = str(value)
                    content_data = json.loads(value_str)
                    if 'created_at' in content_data:
                        created_at = datetime.fromisoformat(content_data['created_at'])
                        if (datetime.now() - created_at).days <= 7:
                            stats['recent_content_count'] += 1
                except:
                    pass
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    return stats

def get_recent_activities(db, limit=5):
    """Get recent activities for admin dashboard"""
    activities = []
    
    try:
        for key, value in db.items():
            # Handle both string and bytes keys
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = str(key)
                
            if key_str.startswith('content:'):
                try:
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8')
                    else:
                        value_str = str(value)
                    content_data = json.loads(value_str)
                    if 'created_at' in content_data:
                        activities.append({
                            'title': content_data.get('title', 'Untitled'),
                            'description': f"Content added: {content_data.get('content_type', 'unknown').title()}",
                            'timestamp': datetime.fromisoformat(content_data['created_at']),
                            'type': 'Content',
                            'type_color': 'success'
                        })
                except:
                    pass
    except Exception as e:
        print(f"Error getting activities: {e}")
    
    # Sort by timestamp and return recent ones
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]

@admin_bp.route('/facebook-apps')
@login_required
@admin_required
def facebook_apps():
    """Display Facebook apps management page"""
    try:
        db = get_unqlite_db()
        apps = []
        
        # Iterate through all keys in the database
        for key, value in db.items():
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = str(key)
                
            if key_str.startswith('user:'):
                try:
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8')
                    else:
                        value_str = str(value)
                    app_data = json.loads(value_str)
                    app_data['key'] = key_str
                    apps.append(app_data)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error decoding data for key {key_str}: {e}")
                    continue
        
        db.close()
        return render_template('admin/facebook_apps.html', apps=apps)
        
    except Exception as e:
        flash(f'Error loading Facebook apps: {str(e)}', 'error')
        return redirect(url_for('home.home'))

@admin_bp.route('/api/facebook-apps', methods=['GET'])
@login_required
@admin_required
def get_facebook_apps():
    """API endpoint to get all Facebook apps"""
    try:
        db = get_unqlite_db()
        apps = []
        
        # Iterate through all keys in the database
        for key in db:
            if key.decode('utf-8').startswith('user:'):
                try:
                    value = db[key]
                    app_data = json.loads(value.decode('utf-8'))
                    app_data['key'] = key.decode('utf-8')
                    # Don't include the full access token in the list view for security
                    if 'password' in app_data:
                        app_data['password'] = app_data['password'][:20] + '...' if len(app_data['password']) > 20 else app_data['password']
                    apps.append(app_data)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error decoding data for key {key}: {e}")
                    continue
        
        db.close()
        return jsonify({'success': True, 'apps': apps})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/facebook-apps/<page_id>', methods=['GET'])
@login_required
@admin_required
def get_facebook_app(page_id):
    """API endpoint to get a specific Facebook app"""
    try:
        db = get_unqlite_db()
        key = f'user:{page_id}'
        
        try:
            value = db[key]
            app_data = json.loads(value.decode('utf-8'))
            app_data['key'] = key
            db.close()
            return jsonify({'success': True, 'app': app_data})
        except KeyError:
            db.close()
            return jsonify({'success': False, 'error': 'App not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/facebook-apps', methods=['POST'])
@login_required
@admin_required
def create_facebook_app():
    """API endpoint to create a new Facebook app"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['page_id', 'name', 'access_token']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        page_id = data['page_id']
        key = f'user:{page_id}'
        
        # Create app data structure
        app_data = {
            'username': data['name'],
            'password': data['access_token'],  # Using password field for access_token
            'page_id': page_id,
            'category': data.get('category', ''),
            'tasks': data.get('tasks', [])
        }
        
        # Check if app already exists
        db = get_unqlite_db()
        try:
            existing = db[key]
            db.close()
            return jsonify({'success': False, 'error': 'App with this page ID already exists'}), 409
        except KeyError:
            # App doesn't exist, create it
            db[key] = json.dumps(app_data)
            db.commit()
            db.close()
            
            return jsonify({'success': True, 'message': 'Facebook app created successfully', 'app': app_data})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/facebook-apps/<page_id>', methods=['PUT'])
@login_required
@admin_required
def update_facebook_app(page_id):
    """API endpoint to update a Facebook app"""
    try:
        data = request.get_json()
        key = f'user:{page_id}'
        
        db = get_unqlite_db()
        
        try:
            # Get existing app data
            existing_value = db[key]
            existing_app = json.loads(existing_value.decode('utf-8'))
            
            # Update fields if provided
            if 'name' in data:
                existing_app['username'] = data['name']
            if 'access_token' in data:
                existing_app['password'] = data['access_token']
            if 'category' in data:
                existing_app['category'] = data['category']
            if 'tasks' in data:
                existing_app['tasks'] = data['tasks']
            
            # Save updated data
            db[key] = json.dumps(existing_app)
            db.commit()
            db.close()
            
            return jsonify({'success': True, 'message': 'Facebook app updated successfully', 'app': existing_app})
            
        except KeyError:
            db.close()
            return jsonify({'success': False, 'error': 'App not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/facebook-apps/<page_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_facebook_app(page_id):
    """API endpoint to delete a Facebook app"""
    try:
        key = f'user:{page_id}'
        
        db = get_unqlite_db()
        
        try:
            # Check if app exists
            existing_value = db[key]
            
            # Delete the app
            del db[key]
            db.commit()
            db.close()
            
            return jsonify({'success': True, 'message': 'Facebook app deleted successfully'})
            
        except KeyError:
            db.close()
            return jsonify({'success': False, 'error': 'App not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/facebook-apps/new')
@login_required
@admin_required
def new_facebook_app():
    """Display form to create a new Facebook app"""
    return render_template('admin/facebook_app_form.html', app=None, action='create')

@admin_bp.route('/facebook-apps/<page_id>/edit')
@login_required
@admin_required
def edit_facebook_app(page_id):
    """Display form to edit a Facebook app"""
    try:
        db = get_unqlite_db()
        key = f'user:{page_id}'
        
        try:
            value = db[key]
            app_data = json.loads(value.decode('utf-8'))
            app_data['key'] = key
            db.close()
            return render_template('admin/facebook_app_form.html', app=app_data, action='edit')
        except KeyError:
            db.close()
            flash('App not found', 'error')
            return redirect(url_for('custom_admin.facebook_apps'))
            
    except Exception as e:
        flash(f'Error loading app: {str(e)}', 'error')
        return redirect(url_for('custom_admin.facebook_apps'))

# Content Management Routes
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'instance', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'webm'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_dir():
    """Ensure upload directory exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@admin_bp.route('/content')
@login_required
@admin_required
def content_list():
    """Display content list page"""
    try:
        db = get_unqlite_db()
        contents = get_recent_contents(db, limit=10)
        db.close()
        return render_template('admin/content_list.html', contents=contents)
    except Exception as e:
        flash(f'Error loading contents: {str(e)}', 'error')
        return redirect(url_for('custom_admin.admin_index'))

@admin_bp.route('/content/all')
@login_required
@admin_required
def content_list_all():
    """Display all content"""
    try:
        db = get_unqlite_db()
        contents = get_recent_contents(db, limit=None)
        db.close()
        return render_template('admin/content_list.html', contents=contents)
    except Exception as e:
        flash(f'Error loading contents: {str(e)}', 'error')
        return redirect(url_for('custom_admin.admin_index'))

@admin_bp.route('/content/ingest', methods=['GET', 'POST'])
@login_required
@admin_required
def content_ingest():
    """Content ingestion form and handler"""
    if request.method == 'GET':
        return render_template('admin/content_form.html')
    
    try:
        # Get form data
        content_type = request.form.get('content_type')
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '')
        is_public = request.form.get('is_public') == 'on'
        
        # Validate required fields
        if not all([content_type, title, description]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin/content_form.html')
        
        # Handle file upload for image/video content
        file_path = None
        if content_type in ['image', 'video']:
            if 'media_file' not in request.files:
                flash('Please upload a file for this content type.', 'error')
                return render_template('admin/content_form.html')
            
            file = request.files['media_file']
            if file.filename == '':
                flash('Please select a file to upload.', 'error')
                return render_template('admin/content_form.html')
            
            if file and allowed_file(file.filename):
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    flash('File size exceeds 10MB limit.', 'error')
                    return render_template('admin/content_form.html')
                
                # Save file
                ensure_upload_dir()
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
            else:
                flash('Invalid file type. Please upload a valid image or video file.', 'error')
                return render_template('admin/content_form.html')
        
        # Create content data
        content_id = str(uuid.uuid4())
        content_data = {
            'id': content_id,
            'title': title,
            'description': description,
            'content_type': content_type,
            'tags': tags,
            'is_public': is_public,
            'file_path': file_path,
            'created_by': current_user.username,
            'created_at': datetime.now().isoformat()
        }
        
        # Save to database
        db = get_unqlite_db()
        key = f'content:{content_id}'
        db[key] = json.dumps(content_data)
        db.commit()
        db.close()
        
        flash('Content ingested successfully!', 'success')
        return redirect(url_for('custom_admin.content_list'))
        
    except Exception as e:
        flash(f'Error ingesting content: {str(e)}', 'error')
        return render_template('admin/content_form.html')

@admin_bp.route('/content/<content_id>/view')
@login_required
@admin_required
def content_view(content_id):
    """View specific content"""
    try:
        db = get_unqlite_db()
        key = f'content:{content_id}'
        
        try:
            value = db[key]
            content_data = json.loads(value.decode('utf-8'))
            content_data['created_at'] = datetime.fromisoformat(content_data['created_at'])
            db.close()
            return render_template('admin/content_view.html', content=content_data)
        except KeyError:
            db.close()
            flash('Content not found', 'error')
            return redirect(url_for('custom_admin.content_list'))
            
    except Exception as e:
        flash(f'Error loading content: {str(e)}', 'error')
        return redirect(url_for('custom_admin.content_list'))

@admin_bp.route('/api/content/<content_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_content(content_id):
    """API endpoint to delete content"""
    try:
        db = get_unqlite_db()
        key = f'content:{content_id}'
        
        try:
            # Get content data to check for file
            value = db[key]
            content_data = json.loads(value.decode('utf-8'))
            
            # Delete file if exists
            if content_data.get('file_path') and os.path.exists(content_data['file_path']):
                os.remove(content_data['file_path'])
            
            # Delete from database
            del db[key]
            db.commit()
            db.close()
            
            return jsonify({'success': True, 'message': 'Content deleted successfully'})
            
        except KeyError:
            db.close()
            return jsonify({'success': False, 'message': 'Content not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/uploads/<filename>')
@login_required
@admin_required
def serve_content_file(filename):
    """Serve uploaded content files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

def get_recent_contents(db, limit=10):
    """Get recent contents from database"""
    contents = []
    
    try:
        for key, value in db.items():
            # Handle both string and bytes keys
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = str(key)
                
            if key_str.startswith('content:'):
                try:
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8')
                    else:
                        value_str = str(value)
                    content_data = json.loads(value_str)
                    content_data['created_at'] = datetime.fromisoformat(content_data['created_at'])
                    contents.append(content_data)
                except Exception as e:
                    print(f"Error parsing content {key_str}: {e}")
    except Exception as e:
        print(f"Error getting contents: {e}")
    
    # Sort by creation date (newest first)
    contents.sort(key=lambda x: x['created_at'], reverse=True)
    
    if limit:
        return contents[:limit]
    return contents
