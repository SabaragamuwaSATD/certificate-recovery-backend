from flask import Blueprint, request, jsonify
from app.services.auth import AuthService
from app.utils.decorators import validate_credentials
# In certificates.py and auth.py
from app.services.firebase import FirebaseService

auth_bp = Blueprint('auth', __name__)

# Login route
@auth_bp.route('/login', methods=['POST'])
@validate_credentials
def login():
    data = request.get_json()
    return AuthService.login_user(data)

# Register route
@auth_bp.route('/register', methods=['POST'])
@validate_credentials
def register():
    data = request.get_json()
    return AuthService.register_user(data)