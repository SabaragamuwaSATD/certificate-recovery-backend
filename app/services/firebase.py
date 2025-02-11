from io import BytesIO

from firebase_admin import credentials, firestore, storage, initialize_app
import requests

from app.config import Config

# Initialize Firebase once
cred = credentials.Certificate("serviceAccountKey.json")
firebase_app = initialize_app(cred, {
    'storageBucket': Config.FIREBASE_CONFIG['storageBucket']
})

class FirebaseService:
    db = firestore.client()
    bucket = storage.bucket(Config.FIREBASE_CONFIG['storageBucket'])


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

    @staticmethod
    def create_document(collection, data):
        doc_ref = FirebaseService.db.collection(collection).document()
        doc_ref.set(data)
        return doc_ref.id

    @staticmethod
    def get_user_requests(user_id):
        docs = FirebaseService.db.collection('certificate_requests') \
            .where('user_id', '==', user_id) \
            .stream()
        return [doc.to_dict() for doc in docs]

    @staticmethod
    def get_user_certificates(user_id):
        docs = FirebaseService.db.collection('certificates') \
            .where('user_id', '==', user_id) \
            .stream()
        return [doc.to_dict() for doc in docs]