from flask import Blueprint, render_template
from flask_login import current_user

# Blueprint for home routes
home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    """Home page with Facebook posting tutorial"""
    return render_template('home.html')


@home_bp.route('/tutorial')
def tutorial():
    """Detailed tutorial page"""
    return render_template('home.html')
