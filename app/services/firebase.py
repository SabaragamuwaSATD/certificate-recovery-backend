from io import BytesIO

from firebase_admin import credentials, firestore, storage, initialize_app, auth
import requests
import logging

from app.config import Config

# Initialize Firebase once
cred = credentials.Certificate("serviceAccountKey.json")
firebase_app = initialize_app(cred, {
    'storageBucket': Config.FIREBASE_CONFIG['storageBucket']
})

class FirebaseService:
    db = firestore.client()
    bucket = storage.bucket(Config.FIREBASE_CONFIG['storageBucket'])


# upload files to firebase
    @staticmethod
    def upload_file(file, path):
        # If the file is a URL, download it first
        if isinstance(file, str) and file.startswith('http'):
            file_response = requests.get(file)
            file = BytesIO(file_response.content)  # Convert the content to a file-like object

        # Check if the file is a file-like object, and if not, open it
        if not hasattr(file, 'read'):
            # If file is a path, open it as a binary stream
            with open(file, 'rb') as f:
                file = f  # Now file is a file-like object

        blob = FirebaseService.bucket.blob(path)
        blob.upload_from_file(file)  # Pass the file-like object
        blob.make_public()
        return blob.public_url

# create collection documents
    @staticmethod
    def create_document(collection, data):
        doc_ref = FirebaseService.db.collection(collection).document()
        doc_ref.set(data)
        return doc_ref.id

# get user certificate replacement requests
    @staticmethod
    def get_user_requests(user_id):
        docs = FirebaseService.db.collection('certificate_requests') \
            .where('user_id', '==', user_id) \
            .stream()
        return [doc.to_dict() for doc in docs]

# get user certificates
    @staticmethod
    def get_user_certificates(user_id):
        docs = FirebaseService.db.collection('certificates') \
            .where('user_id', '==', user_id) \
            .stream()
        return [doc.to_dict() for doc in docs]

#------------------------------------------------------------------------------

# get user data
    @staticmethod
    def get_user(user_id):
        try:
            user = auth.get_user(user_id)
            return {
                'uid': user.uid,
                'email': user.email,
                'full_name': user.display_name,
                'contact_number': user.phone_number,
                'admin_id': user.custom_claims.get('admin_id'),
                'role': user.custom_claims.get('role'),
                'profile_picture_url': user.photo_url
            }
        except auth.UserNotFoundError:
            return None

# update user data
    @staticmethod
    def update_user(user_id, user_data):
        try:
            user = auth.update_user(
                user_id,
                email=user_data.get('email'),
                phone_number=user_data.get('contact_number'),
                display_name=user_data.get('full_name'),
                photo_url=user_data.get('profile_picture_url'),
                password=user_data.get('password')
            )
            if 'role' in user_data or 'admin_id' in user_data:
                auth.set_custom_user_claims(user_id, {
                    'role': user_data.get('role', 'athlete'),
                    'admin_id': user_data.get('admin_id')
                })
            return user
        except auth.UserNotFoundError:
            return None

# get all users
    @staticmethod
    def get_all_users():
        users = auth.list_users().iterate_all()
        return [{'uid': user.uid, 'email': user.email, 'contact_number': user.phone_number, 'full_name': user.display_name,
             'role': user.custom_claims.get('role') if user.custom_claims else None} for user in users if
            user.custom_claims and user.custom_claims.get('role') == 'athlete']

# get all admins
    @staticmethod
    def get_all_admins():
        users = auth.list_users().iterate_all()
        return [{'uid': user.uid, 'email': user.email, 'contact_number': user.phone_number, 'full_name': user.display_name,
                 'role': user.custom_claims.get('role') if user.custom_claims else None} for user in users if
                user.custom_claims and user.custom_claims.get('role') == 'admin']

# create new Admin
    @staticmethod
    def create_user(user_data):
        user = auth.create_user(
            email=user_data['email'],
            password=user_data['password'],
            display_name=user_data['full_name'],
            phone_number=user_data['contact_number']
        )
        auth.set_custom_user_claims(user.uid, {
            'role': user_data.get('role', 'athlete'),
            'admin_id': user_data.get('admin_id')
        })
        # Save user data to Firestore
        FirebaseService.db.collection('users').document(user.uid).set({
            'email': user_data['email'],
            'full_name': user_data['full_name'],
            'contact_number': user_data['contact_number'],
            'admin_id': user_data.get('admin_id'),
            'role': user_data.get('role', 'athlete')
        })
        return user

# get individual athlete data
    @staticmethod
    def get_athlete(user_id):
        try:
            user = auth.get_user(user_id)
            user_data = FirebaseService.db.collection('users').document(user_id).get().to_dict()
            if user_data:
                user_data.update({
                    'uid': user.uid,
                    'email': user.email,
                    'full_name': user.display_name,
                    'contact_number': user.phone_number,
                    'profile_picture_url': user.photo_url,
                    'role': user.custom_claims.get('role')
                })
            return user_data
        except auth.UserNotFoundError:
            return None

# get individual admin data
    @staticmethod
    def get_admin(uid):
        try:
            user = auth.get_user(uid)
            user_data = FirebaseService.db.collection('users').document(uid).get().to_dict()
            if user_data:
                user_data.update({
                    'uid': user.uid,
                    'email': user.email,
                    'full_name': user.display_name,
                    'contact_number': user.phone_number,
                    'profile_picture_url': user.photo_url,
                    'role': user.custom_claims.get('role')
                })
                logging.info(f"Admin data found: {user_data}")
            else:
                logging.warning(f"No user data found in Firestore for uid: {uid}")
            return user_data
        except auth.UserNotFoundError:
            logging.error(f"User not found in Firebase Auth for uid: {uid}")
            return None