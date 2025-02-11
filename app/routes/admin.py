from flask import Blueprint
from app.utils.decorators import token_required
from app.services.certificates import CertificateService

admin_bp = Blueprint('admin', __name__)

#Get all requests
@admin_bp.route('/requests', methods=['GET'])
@token_required(roles=['admin'])
def get_requests(current_user):
    return CertificateService.get_all_pending_requests()

#Approve request
@admin_bp.route('/approve/<request_id>', methods=['POST'])
@token_required(roles=['admin'])
def approve_request(current_user, request_id):
    return CertificateService.approve_request(request_id)

#Reject request
@admin_bp.route('/reject/<request_id>', methods=['POST'])
@token_required(roles=['admin'])
def reject_request(current_user, request_id):
    return CertificateService.reject_request(request_id)

#Get all certificates
@admin_bp.route('/certificates', methods=['GET'])
@token_required(roles=['admin'])
def get_all_certificates(current_user):
    return CertificateService.get_all_certificates()

#Get specific certificate
@admin_bp.route('/certificate/<certificate_id>', methods=['GET'])
@token_required(roles=['admin'])
def get_certificate(current_user, certificate_id):
    return CertificateService.get_certificate(certificate_id)