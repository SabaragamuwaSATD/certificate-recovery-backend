import jwt
from datetime import datetime, timedelta
from firebase_admin import auth
from app.config import Config
from app.utils.exceptions import AuthError
from flask import jsonify


class AuthService:

#login_user method
    @staticmethod
    def login_user(data):
        try:
            user = auth.get_user_by_email(data['email'])
            token = jwt.encode({
                'uid': user.uid,
                'email': user.email,
                'role': user.custom_claims.get('role', 'athlete'),
                'exp': datetime.utcnow() + timedelta(hours=2)
            }, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

            return jsonify({'token': token, 'role': user.custom_claims.get('role', 'athlete')}), 200

        except auth.UserNotFoundError:
            raise AuthError('User not found', 404)
        except Exception as e:
            raise AuthError(str(e))

#register_user method
    @staticmethod
    def register_user(data):
        try:
            email = data.get('email')
            password = data.get('password')
            if not email or not password:
                raise AuthError('Missing email or password', 400)

            user = auth.create_user(
                email=email,
                password=password
            )
            auth.set_custom_user_claims(user.uid, {'role': 'athlete'})
            return jsonify({'message': 'User created successfully'}), 201
        except auth.EmailAlreadyExistsError:
            raise AuthError('Email already exists', 409)
        except Exception as e:
            raise AuthError(str(e))