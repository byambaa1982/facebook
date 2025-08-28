from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import markdown as md
from db import db
from datetime import datetime
import os
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from db.models import User, Role, GeneratedContent
from werkzeug.security import generate_password_hash
import time
from flask_babel import Babel
from flask_login import LoginManager, current_user, login_required

# Add CORS support for local development
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Flask-CORS not installed. Installing for local development...")

# Use 'db' as 'database' for compatibility with legacy code
database = db



app = Flask(__name__)
# Set a secret key for session management and flashing
app.config['SECRET_KEY'] = 'your-very-secret-key'  # Change this to a random value in production

# Create instance directory if it doesn't exist
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add missing DEBUG configuration and local development settings
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
app.config['SESSION_COOKIE_SECURE'] = False  # Allow non-HTTPS for local development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Enable CORS for local development if available
if CORS_AVAILABLE:
    CORS(app, supports_credentials=True)

db.init_app(app)
babel = Babel(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

from db.models import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Template filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML line breaks"""
    if text:
        return text.replace('\n', '<br>')
    return text


from routes.post import bp_post
from routes.auth import auth_bp
from routes.home import home_bp
from routes.database import db_bp
from routes.admin import admin_bp
from routes.comment import bp_comment

app.register_blueprint(bp_post)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(db_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(bp_comment)
# Create tables if they do not exist
with app.app_context():
    db.create_all()


# Helper function to check if current user is admin

def is_admin():
    return current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role.name == 'admin'


# Custom Admin Home View
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        # Only allow access if user is authenticated and has admin role
        return is_admin()

    def inaccessible_callback(self, name, **kwargs):
        # Redirect to home page if user is not admin
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('auth.login') if 'user_id' not in session else '/')


# Add more ModelViews as needed for other tables
admin = Admin(app, name='Admin Panel', template_mode='bootstrap4', index_view=MyAdminIndexView(), url='/flask-admin')


class RoleModelView(ModelView):
    """Admin view for managing roles."""
    column_list = ('id', 'name')  # Displayed columns
    form_columns = ('name',)

    def is_accessible(self):
        return is_admin()

    def inaccessible_callback(self, name, **kwargs):
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('auth.login') if 'user_id' not in session else '/')



class UserModelView(ModelView):
    """Admin view for managing users."""
    column_list = ('id', 'username', 'email', 'role_id')
    column_exclude_list = ['password']  # Don't show password in list view
    form_excluded_columns = ['password']  # Don't show password field in forms
    can_create = True
    can_edit = True
    can_delete = True

    def is_accessible(self):
        return is_admin()

    def inaccessible_callback(self, name, **kwargs):
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('auth.login') if 'user_id' not in session else '/')
    
    def on_model_change(self, form, model, is_created):
        """Handle password hashing when creating/updating users"""
        if is_created and hasattr(form, 'password') and form.password.data:
            model.set_password(form.password.data)





class GeneratedContentModelView(ModelView):
    """Admin view for managing generated content."""
    column_list = ('id', 'topic', 'content_preview', 'image_url', 
    'posted', 'image_prompt', 'user_name', 'when_post', 'posted_at', 
    'code', 'input_data', 'output_data', 'twitter_id', 'is_reposted', 'reposted_at'
                   )
    column_labels = {
        'content_preview': 'Content Preview',
        'image_url': 'Image URL',
        'posted': 'Posted',
        'image_prompt': 'Image Prompt',
        'user_name': 'User Name',
        'when_post': 'When Post',
    }
    form_columns = ('topic', 'content', 'image_url',
                    'image_prompt', 'user_name', 'when_post', 'code', 
                    'input_data', 'posted', 'output_data',
                    'is_reposted')
    column_searchable_list = ['topic', 'content']
    column_filters = ['posted', 'created_at', 'posted_at']
    column_default_sort = ('created_at', True)  # Sort by created_at descending
    can_create = True
    can_edit = True
    can_delete = True
    
    # Custom column formatters
    def _format_datetime(self, context, model, name):
        """Format datetime fields"""
        value = getattr(model, name)
        if value:
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    
    def _format_boolean(self, context, model, name):
        """Format boolean fields"""
        value = getattr(model, name)
        return '✓' if value else '✗'
    
    def _format_content_preview(self, context, model, name):
        """Show content preview (first 100 characters)"""
        if model.content:
            return model.content[:100] + '...' if len(model.content) > 100 else model.content
        return '-'
    
    column_formatters = {
        'created_at': _format_datetime,
        'posted_at': _format_datetime,
        'posted': _format_boolean,
        'content_preview': _format_content_preview
    }

    def is_accessible(self):
        return is_admin()

    def inaccessible_callback(self, name, **kwargs):
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('auth.login') if 'user_id' not in session else '/')
    
    def on_model_change(self, form, model, is_created):
        """Handle model changes"""
        if model.posted and not model.posted_at:
            model.posted_at = datetime.utcnow()
        elif not model.posted:
            model.posted_at = None


admin.add_view(UserModelView(User, database.session))
admin.add_view(RoleModelView(Role, database.session))
admin.add_view(GeneratedContentModelView(GeneratedContent, database.session))   


if __name__ == '__main__':
    # Remove SSH tunnel dependency for local development
    # time.sleep(2)  # Only needed for production SSH tunnel
    
    with app.app_context():
        print("Creating database tables...")
        # Method 1: Drop a specific table using the model's metadata
        # Tutorial.__table__.drop(database.engine, checkfirst=True)
        # Section.__table__.drop(database.engine, checkfirst=True)
        database.create_all() 

        # Add default roles if not present
        if not Role.query.first():
            roles = [
                Role(id=1, name='viewer'),
                Role(id=2, name='editor'),
                Role(id=3, name='admin')
            ]
            database.session.bulk_save_objects(roles)
            database.session.commit()

        # Add an admin user for testing (if not present)
        if not User.query.filter_by(email='admin@example.com').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                role_id=3  # Assign admin role
            )
            database.session.add(admin_user)
            database.session.commit()

    # Proper local development configuration
    app.run(
        host='127.0.0.1',  # Explicitly bind to localhost
        port=5000,
        debug=app.config['DEBUG'],
        threaded=True
    )