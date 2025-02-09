from flask import jsonify

class AuthError(Exception):
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code

class CertificateError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code

def handle_exceptions(error):
    response = jsonify({
        'error': error.message,
        'status': 'error'
    })
    response.status_code = error.status_code
    return response