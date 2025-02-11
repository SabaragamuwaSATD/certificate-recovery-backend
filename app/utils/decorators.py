from functools import wraps
from flask import request, jsonify
import jwt
from app.config import Config
from app.utils.exceptions import AuthError
from app.services.auth import AuthService

def token_required(roles=[]):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                raise AuthError('Missing token', 401)

            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token.split("Bearer ")[1]

            try:
                payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
                if not set(roles).intersection([payload['role']]):
                    raise AuthError('Unauthorized access', 403)
                return f(payload, *args, **kwargs)
            except jwt.ExpiredSignatureError:
                raise AuthError('Token expired', 401)
            except jwt.InvalidTokenError:
                raise AuthError('Invalid token', 401)

        return wrapper

    return decorator

def validate_credentials(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json() or request.form
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing credentials'}), 400
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Missing token'}), 401

        if token.startswith("Bearer "):
            token = token.split("Bearer ")[1]

        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            user = AuthService.get_current_user(payload)
            if not user or user['role'] != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
            return f(payload,*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

    return decorated_function