from flask import Blueprint

# Create a simple database blueprint for now
# This was referenced in flask_app.py but didn't exist
db_bp = Blueprint('database', __name__, url_prefix='/database')

@db_bp.route('/health')
def health_check():
    """Simple health check endpoint"""
    return {'status': 'ok', 'message': 'Database routes are working'}
