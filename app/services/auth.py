import jwt
from datetime import datetime, timedelta
from firebase_admin import auth, firestore
from app.config import Config
from app.utils.exceptions import AuthError
from flask import jsonify, request
import bcrypt

class AuthService:
    db = firestore.client()

#passowrd hashing
    @staticmethod
    def hash_password(password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

#login user
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

#register user
    @staticmethod
    def register_user(data):
        try:
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name')
            contact_number = data.get('contact_number')
            if not email or not password:
                raise AuthError('Missing email or password', 400)

            hashed_password = AuthService.hash_password(password)

            user = auth.create_user(
                email=email,
                password=hashed_password
            )
            auth.set_custom_user_claims(user.uid, {'role': 'athlete'})

            # Save user to Firestore
            user_data = {
                'email': email,
                'full_name': full_name,
                'contact_number': contact_number,
                'role': 'athlete',
                'user_id': user.uid
            }
            AuthService.db.collection('users').document(user.uid).set(user_data)

            return jsonify({'message': 'User created successfully'}), 201
        except auth.EmailAlreadyExistsError:
            raise AuthError('Email already exists', 409)
        except Exception as e:
            raise AuthError(str(e))

#get current user who is logged in
    @staticmethod
    def get_current_user(payload):
        token = request.headers.get('Authorization').split()[1]
        try:
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            user = auth.get_user(decoded_token['uid'])
            return {
                'uid': user.uid,
                'email': user.email,
                'role': user.custom_claims.get('role', 'athlete')
            }
        except Exception as e:
            raise AuthError('Invalid token', 401)