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

# --- Modus Operandi Vector Search Engine ---
_mo_engine = None


def get_mo_engine():
    """Lazy-load the MOVectorEngine singleton."""
    global _mo_engine
    if _mo_engine is None:
        from mo_vector_service import MOVectorEngine
        _mo_engine = MOVectorEngine()
    return _mo_engine


@app.route('/api/search-mo', methods=['POST'])
def search_mo():
    """
    Search for cases with similar Modus Operandi using dense vector embeddings.
    Accepts 'query' or 'query_text' and optional 'top_k' in JSON body or form data.
    """
    data = request.get_json(silent=True) or {}
    query_text = (
        data.get('query')
        or data.get('query_text')
        or request.form.get('query')
        or request.form.get('query_text')
        or request.args.get('query')
        or ''
    ).strip()

    if not query_text:
        return jsonify({
            'status': 'error',
            'message': 'Query string is required (use "query" or "query_text").'
        }), 400

    try:
        top_k = int(data.get('top_k') or request.form.get('top_k') or request.args.get('top_k') or 5)
    except (ValueError, TypeError):
        top_k = 5

    try:
        engine = get_mo_engine()
        results = engine.search_similar_cases(query_text=query_text, top_k=top_k)
        return jsonify({
            'status': 'success',
            'query': query_text,
            'top_k': top_k,
            'count': len(results),
            'results': results
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)