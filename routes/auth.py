from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from db.models import User, Role
from db import db

# Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/user/status', methods=['GET'])
def get_user_status():
    """Check if user is logged in and return their info"""
    try:
        if current_user.is_authenticated:
            return jsonify({
                'logged_in': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'role': {'name': current_user.role.name}
                }
            }), 200
        return jsonify({'logged_in': False}), 200
    except Exception as e:
        print(f"Error in get_user_status: {e}")
        return jsonify({'logged_in': False, 'error': 'Server error'}), 500


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password required'}), 400

    # Check if user with same username or email exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'User already exists'}), 409

    # Assign default role
    role = Role.query.filter_by(name='viewer').first()
    if not role:
        role = Role(name='viewer')
        db.session.add(role)
        db.session.commit()

    user = User(username=username, email=email, role_id=role.id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    login_user(user)  # Use Flask-Login
    return jsonify({'message': 'Logged in successfully'}), 200


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    logout_user()  # Use Flask-Login
    return jsonify({'message': 'Logged out successfully'}), 200