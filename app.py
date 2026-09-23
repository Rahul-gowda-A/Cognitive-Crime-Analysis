from flask import Flask, render_template, request, url_for, jsonify, abort
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

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

# --- Canonical User Role Definitions ---
ROLE_PUBLIC = 'PUBLIC'
ROLE_FIELD_OFFICER = 'FIELD_OFFICER'
ROLE_SP_ADMIN = 'SP_ADMIN'


class RoleString(str):
    """Case-insensitive string wrapper ensuring backwards-compatibility with legacy lowercase checks."""
    def __eq__(self, other):
        if isinstance(other, str):
            return self.lower() == other.lower()
        return super().__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.lower())


class RoleType(db.TypeDecorator):
    """SQLAlchemy type decorator that returns RoleString for case-insensitive role checks."""
    impl = db.String(20)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value).upper()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return RoleString(value)
        return value


# --- User Model ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(80), unique=True, nullable=False)
    password_hash    = db.Column(db.String(256), nullable=False)
    role             = db.Column(RoleType, nullable=False, default='PUBLIC')
    # Roles: 'PUBLIC' | 'FIELD_OFFICER' | 'SP_ADMIN'
    assigned_district = db.Column(db.String(100), nullable=True)

    @property
    def normalized_role(self) -> str:
        return (self.role or '').upper().strip()

    def has_role(self, *roles) -> bool:
        current = self.normalized_role
        return current in [r.upper().strip() for r in roles]

    @property
    def is_field_officer(self) -> bool:
        return self.has_role(ROLE_FIELD_OFFICER)

    @property
    def is_sp_admin(self) -> bool:
        return self.has_role(ROLE_SP_ADMIN)

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
                'role':              'PUBLIC',
                'assigned_district': None,
            },
            {
                'username':          'field_officer',
                'password':          'officer123',
                'role':              'FIELD_OFFICER',
                'assigned_district': 'BANGALORE COMMR.',
            },
            {
                'username':          'sp_admin',
                'password':          'admin123',
                'role':              'SP_ADMIN',
                'assigned_district': 'STATE POLICE HQ',
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
            else:
                # Sync canonical role and assigned district
                existing.role = account['role']
                if account['assigned_district'] and not existing.assigned_district:
                    existing.assigned_district = account['assigned_district']

        db.session.commit()
        print('[init_db] Verified default user accounts.')


# Seed on startup before routes are registered
init_db()


# --- RBAC Role Verification Helpers ---
def verify_user_role(role_name: str, user=None) -> bool:
    """
    Verify if target user (or current_user) holds the specified role (case-insensitive).
    """
    u = user or current_user
    if not u or not getattr(u, 'is_authenticated', False):
        return False
    current = (getattr(u, 'role', '') or '').upper().strip()
    return current == role_name.upper().strip()


def role_required_api(*allowed_roles):
    """
    Decorator to restrict API endpoints to authenticated users with allowed roles.
    Supports current_user authentication and explicit X-User-Role / role payload for testing.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            req_data = request.get_json(silent=True) or {}
            explicit_role = request.headers.get('X-User-Role') or req_data.get('role') or request.args.get('role')
            if explicit_role:
                norm = explicit_role.upper().strip()
                if norm in [r.upper().strip() for r in allowed_roles]:
                    return f(*args, **kwargs)
            if current_user.is_authenticated:
                norm = (current_user.role or '').upper().strip()
                if norm in [r.upper().strip() for r in allowed_roles]:
                    return f(*args, **kwargs)
            return jsonify({'status': 'error', 'message': f'Unauthorized. Required role: {list(allowed_roles)}'}), 403
        return decorated_function
    return decorator

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


# --- Spatio-Temporal Beat Engine Route (Week 3) ---
@app.route('/api/patrol-route', methods=['POST'])
def api_patrol_route():
    """
    Generate an optimized, K-Means clustered high-risk patrol route for a police beat.
    Payload: { "beat_id": "BEAT_101", "shift": "night", "num_waypoints": 5 }
    """
    data = request.get_json(silent=True) or request.form or {}
    beat_id = str(data.get('beat_id') or 'BEAT_101').strip()
    shift = str(data.get('shift') or 'night').strip()
    try:
        num_waypoints = int(data.get('num_waypoints') or 5)
    except (ValueError, TypeError):
        num_waypoints = 5

    try:
        from spatial_beat_engine import generate_patrol_route
        waypoints = generate_patrol_route(beat_id=beat_id, shift=shift, num_waypoints=num_waypoints)
        return jsonify({
            'status': 'success',
            'beat_id': beat_id,
            'shift': shift,
            'algorithm_used': 'K-Means Spatial Downscaling & Nearest-Neighbor Route Sequencing',
            'total_waypoints': len(waypoints),
            'waypoints': waypoints
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# --- Generative Case Briefing Engine Route (Week 4) ---
@app.route('/api/case-briefing', methods=['POST'])
def api_case_briefing():
    """
    Generate structured case briefing dossier from FIR narrative and entities.
    Returns: Chronological Timeline, Missing Evidence Gaps, and Suggested Interrogation Questions.
    Payload: { "case_narrative": "...", "entities": { ... } }
    """
    data = request.get_json(silent=True) or request.form or {}
    narrative = data.get('case_narrative') or data.get('case_text') or data.get('narrative') or ''
    entities = data.get('entities') or data.get('entities_dict') or None

    if not narrative.strip():
        return jsonify({'status': 'error', 'message': 'case_narrative is required.'}), 400

    try:
        from case_briefing_copilot import generate_case_brief
        brief = generate_case_brief(case_narrative=narrative, entities_dict=entities)
        return jsonify({
            'status': 'success',
            'case_brief': brief
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# --- Role-Based Access Control & Dashboard Routing (Week 5) ---
@app.route('/api/role-dashboard', methods=['GET', 'POST'])
@app.route('/api/dashboard-payload', methods=['GET', 'POST'])
def api_role_dashboard():
    """
    Expose role-aware API payloads:
    - 'FIELD_OFFICER': Receives active beat alerts and tactical patrol route waypoints.
    - 'SP_ADMIN': Receives macro-level crime trend analytics, resource allocation, and strategic advisories.
    """
    data = request.get_json(silent=True) or request.form or {}
    requested_role = (
        request.headers.get('X-User-Role')
        or data.get('role')
        or request.args.get('role')
        or (current_user.role if current_user.is_authenticated else None)
        or ''
    ).upper().strip()

    if not requested_role:
        return jsonify({
            'status': 'error',
            'message': 'Authentication or explicit role is required (use header X-User-Role, query ?role=, or login).'
        }), 401

    if requested_role == ROLE_FIELD_OFFICER:
        beat_id = data.get('beat_id') or request.args.get('beat_id') or 'BEAT_101'
        shift = data.get('shift') or request.args.get('shift') or 'night'
        from spatial_beat_engine import SpatialBeatEngine
        engine = SpatialBeatEngine()
        payload = engine.get_field_officer_payload(beat_id=beat_id, shift=shift)
        return jsonify({
            'status': 'success',
            'role': ROLE_FIELD_OFFICER,
            'dashboard_type': 'OPERATIONAL_TACTICAL_FIELD',
            'payload': payload
        }), 200

    elif requested_role == ROLE_SP_ADMIN:
        state = data.get('state') or request.args.get('state') or 'KARNATAKA'
        from spatial_beat_engine import SpatialBeatEngine
        engine = SpatialBeatEngine()
        payload = engine.get_sp_admin_payload(state=state)
        return jsonify({
            'status': 'success',
            'role': ROLE_SP_ADMIN,
            'dashboard_type': 'STRATEGIC_MACRO_ANALYTICS',
            'payload': payload
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': f"Access forbidden for role '{requested_role}'. Must be 'FIELD_OFFICER' or 'SP_ADMIN'."
        }), 403


from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)