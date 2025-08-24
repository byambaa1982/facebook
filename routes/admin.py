from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
import json
import os
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
    return redirect(url_for('custom_admin.facebook_apps'))

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
