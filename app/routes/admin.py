from flask import Blueprint, request, jsonify

from app.services.auth import AuthService
from app.services.firebase import FirebaseService
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

#--------------------------------------------------------------------------------------
# Get all non-admin users
@admin_bp.route('/users', methods=['GET'])
@token_required(roles=['admin'])
def view_users(payload):
    users = FirebaseService.get_all_users()
    return jsonify({'users': users}), 200

# Get all admins
@admin_bp.route('/admins', methods=['GET'])
@token_required(roles=['admin'])
def view_admins(payload):
    admins = FirebaseService.get_all_admins()
    return jsonify({'admins': admins}), 200

# Create admin by admin
@admin_bp.route('/create', methods=['POST'])
@token_required(roles=['admin'])
def create_admin(payload):
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    contact_number = data.get('contact_number')
    admin_id = data.get('admin_id')

    if not email or not password or not full_name or not contact_number or not admin_id:
        return jsonify({'message': 'Missing required fields'}), 400

    hashed_password = AuthService.hash_password(password)
    admin_data = {
        'email': email,
        'password': hashed_password,
        'full_name': full_name,
        'contact_number': contact_number,
        'admin_id': admin_id,
        'role': 'admin'
    }

    FirebaseService.create_user(admin_data)
    return jsonify({'message': 'Admin created successfully'}), 201