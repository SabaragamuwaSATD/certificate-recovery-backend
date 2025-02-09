from flask import Blueprint
from app.utils.decorators import token_required
from app.services.certificates import CertificateService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/requests', methods=['GET'])
@token_required(roles=['admin'])
def get_requests(current_user):
    return CertificateService.get_all_requests()

@admin_bp.route('/approve/<request_id>', methods=['POST'])
@token_required(roles=['admin'])
def approve_request(current_user, request_id):
    return CertificateService.approve_request(request_id)