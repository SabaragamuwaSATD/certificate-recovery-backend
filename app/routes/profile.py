# In `app/routes/profile.py`
from flask import Blueprint, request, jsonify
from app.services.auth import AuthService
from app.utils.decorators import admin_required, token_required
from app.services.firebase import FirebaseService

profile_bp = Blueprint('profile', __name__)

# update profile admin and as well as normal user its based on user_id send with form data
@profile_bp.route('/update', methods=['POST'])
@admin_required
def update_profile(payload):
    data = request.form
    files = request.files

    user_id = data.get('user_id')
    user = FirebaseService.get_user(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if 'full_name' in data:
        user['full_name'] = data['full_name']
    if 'contact_number' in data:
        user['contact_number'] = data['contact_number']
    if 'admin_id' in data:
        user['admin_id'] = data['admin_id']
    if 'email' in data:
        user['email'] = data['email']
    if 'password' in data:
        user['password'] = AuthService.hash_password(data['password'])
    if 'profile_picture' in files:
        profile_picture_url = FirebaseService.upload_file(
            files['profile_picture'],
            f"profile_pictures/{user_id}_{files['profile_picture'].filename}"
        )
        user['profile_picture_url'] = profile_picture_url

    FirebaseService.update_user(user_id, user)
    return jsonify({'message': 'Profile updated successfully'}), 200


# get profile details of normal user based on user_id
@profile_bp.route('/athlete/<user_id>', methods=['GET'])
@token_required(roles=['admin'])
def get_athlete_details(current_user, user_id):
    athlete = FirebaseService.get_athlete(user_id)
    if not athlete:
        return jsonify({'message': 'Athlete not found'}), 404
    return jsonify(athlete), 200

# get profile details of admin user based on user_id
@profile_bp.route('/admin/<user_id>', methods=['GET'])
@token_required(roles=['admin'])
def get_admin_details(current_user, user_id):
    admin = FirebaseService.get_admin(user_id)
    if not admin:
        return jsonify({'message': 'Admin not found'}), 404
    return jsonify(admin), 200