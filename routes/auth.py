from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, unset_jwt_cookies, set_access_cookies, get_jwt_identity

from models.admin import Admin

auth_bp = Blueprint('auth', __name__, url_prefix='/api/admin')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    admin = Admin.query.filter_by(email=email).first()

    if not admin or not admin.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(admin.id))

    resp = make_response(jsonify({
        'success': True,
        'message': 'Login successful',
        'admin': admin.to_dict(),
        'access_token': access_token
    }))
    set_access_cookies(resp, access_token)
    return resp


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = make_response(jsonify({'success': True, 'message': 'Logged out successfully'}))
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    admin = Admin.query.get(get_jwt_identity())
    if not admin:
        return jsonify({'success': False, 'message': 'Admin not found'}), 404
    return jsonify({'success': True, 'admin': admin.to_dict()})