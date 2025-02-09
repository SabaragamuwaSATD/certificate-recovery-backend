from firebase_admin import credentials, firestore, storage, initialize_app
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
        blob = FirebaseService.bucket.blob(path)
        blob.upload_from_file(file)
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