from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from db.models import  User
from db import db
from flask_login import current_user, login_required

bp_post = Blueprint('post', __name__, template_folder='../templates', static_folder='../static')