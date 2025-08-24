from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import db



class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # Role name: viewer, editor, admin, owner
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f"<Role {self.name}>"

    
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_paid = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)  # Foreign key to roles table
    role = db.relationship('Role', backref=db.backref('users', lazy=True))  # Relationship to Role
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f"<User {self.username}, Role {self.role.name}>"

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Checks the provided password against the stored hash."""
        return check_password_hash(self.password, password)

    # The following methods are provided by UserMixin:
    # - is_authenticated
    # - is_active
    # - is_anonymous
    # - get_id

class GeneratedContent(db.Model):
    __tablename__ = 'generated_content'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    code = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(512), nullable=True)
    image_prompt = db.Column(db.Text, nullable=True)
    user_name = db.Column(db.Text, nullable=True)
    input_data = db.Column(db.Text, nullable=True)
    output_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    posted = db.Column(db.Boolean, default=False, nullable=False)
    posted_at = db.Column(db.DateTime, nullable=True)
    when_post = db.Column(db.Text, nullable=True)
    twitter_id = db.Column(db.String(255), nullable=True)  # Twitter/X tweet ID
    is_reposted = db.Column(db.Boolean, default=False, nullable=False)  # Track if content was reposted
    reposted_at = db.Column(db.DateTime, nullable=True)  # When it was reposted

    def __repr__(self):
        return f"<GeneratedContent id={self.id} topic={self.topic}>"





