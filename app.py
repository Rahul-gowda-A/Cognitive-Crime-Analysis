from flask import Flask, render_template, request, url_for, jsonify
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize the Flask App
app = Flask(__name__)

# --- Security & Database Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'crime-analysis-dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Extension Initialization ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


# --- User Model ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(80), unique=True, nullable=False)
    password_hash    = db.Column(db.String(256), nullable=False)
    role             = db.Column(db.String(20), nullable=False, default='public')
    # Roles: 'public' | 'field_officer'
    assigned_district = db.Column(db.String(100), nullable=True)

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username!r} role={self.role!r}>'


@login_manager.user_loader
def load_user(user_id: str):
    """Flask-Login callback: load user by primary key."""
    return db.session.get(User, int(user_id))


# --- Database Initialization & Seeding ---
def init_db():
    """Create tables and seed default accounts if needed."""
    with app.app_context():
        db.create_all()

        seed_accounts = [
            {
                'username':          'public_user',
                'password':          'public123',
                'role':              'public',
                'assigned_district': None,
            },
            {
                'username':          'field_officer',
                'password':          'officer123',
                'role':              'field_officer',
                'assigned_district': None,
            },
        ]

        for account in seed_accounts:
            existing = User.query.filter_by(username=account['username']).first()
            if not existing:
                user = User(
                    username=account['username'],
                    role=account['role'],
                    assigned_district=account['assigned_district'],
                )
                user.set_password(account['password'])
                db.session.add(user)

        db.session.commit()
        print('[init_db] Verified default user accounts.')


# Seed on startup before routes are registered
init_db()

from routes import *

if __name__ == '__main__':
    app.run(debug=True)