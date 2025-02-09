import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-key')
    JWT_ALGORITHM = 'HS256'
    FIREBASE_CONFIG = {
        'storageBucket': 'wastenet-59699.appspot.com',  # From Firebase console
        'projectId': 'wastenet-59699'                   # From Firebase console
    }