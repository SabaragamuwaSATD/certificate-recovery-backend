from flask import Blueprint
from app.utils.decorators import token_required
from app.services.certificates import CertificateService
# In certificates.py and auth.py
from app.services.firebase import FirebaseService

cert_bp = Blueprint('certificates', __name__)

@cert_bp.route('/request', methods=['POST'])
@token_required(roles=['athlete'])
def create_request(current_user):
    return CertificateService.create_request(current_user)

@cert_bp.route('/status', methods=['GET'])
@token_required(roles=['athlete'])
def get_status(current_user):
    return CertificateService.get_status(current_user)