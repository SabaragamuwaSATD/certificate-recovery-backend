from flask import Blueprint
from app.utils.decorators import token_required
from app.services.certificates import CertificateService
# In certificates.py and auth.py
from app.services.firebase import FirebaseService

cert_bp = Blueprint('certificates', __name__)

#Create request
@cert_bp.route('/request', methods=['POST'])
@token_required(roles=['athlete'])
def create_request(current_user):
    return CertificateService.create_request(current_user)

#Get status of the request
@cert_bp.route('/status', methods=['GET'])
@token_required(roles=['athlete'])
def get_status(current_user):
    return CertificateService.get_status(current_user)

#Download certificate
@cert_bp.route('/download/<request_id>', methods=['GET'])
@token_required(roles=['athlete'])
def download_certificate(current_user, request_id):
    return CertificateService.download_certificate(current_user, request_id)

#get specific user requests
@cert_bp.route('/request/<request_id>', methods=['DELETE'])
@token_required(roles=['athlete'])
def delete_request(current_user, request_id):
    return CertificateService.delete_request(current_user, request_id)


#Get specific user certificates
@cert_bp.route('/certificates', methods=['GET'])
@token_required(roles=['athlete'])
def get_certificates(current_user):
    return CertificateService.get_certificates(current_user)


