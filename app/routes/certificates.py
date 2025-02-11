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

@cert_bp.route('/download/<request_id>', methods=['GET'])
@token_required(roles=['athlete'])
def download_certificate(current_user, request_id):
    return CertificateService.download_certificate(current_user, request_id)

@cert_bp.route('/request/<request_id>', methods=['DELETE'])
@token_required(roles=['athlete'])
def delete_request(current_user, request_id):
    return CertificateService.delete_request(current_user, request_id)