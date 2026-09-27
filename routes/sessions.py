from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db
from models.session import Session

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')


@sessions_bp.route('', methods=['POST'])
@jwt_required()
def create_session():
    data = request.get_json(silent=True) or {}

    session_name = (data.get('session_name') or '').strip()
    session_date_str = (data.get('session_date') or '').strip()
    start_time = (data.get('start_time') or '').strip()
    end_time = (data.get('end_time') or '').strip()
    food_item = (data.get('food_item') or '').strip()
    attendee_count = data.get('attendee_count')

    if not session_name:
        return jsonify({'success': False, 'message': 'Session name is required'}), 400
    if not session_date_str:
        return jsonify({'success': False, 'message': 'Session date is required'}), 400

    try:
        session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Session date must be in YYYY-MM-DD format'}), 400

    try:
        attendee_count = int(attendee_count)
        if attendee_count <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Coupon capacity must be a positive number'}), 400

    new_session = Session(
        session_name=session_name,
        session_date=session_date,
        start_time=start_time,
        end_time=end_time,
        food_item=food_item,
        attendee_count=attendee_count
    )
    db.session.add(new_session)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Session created successfully', 'session': new_session.to_dict()}), 201


@sessions_bp.route('', methods=['GET'])
@jwt_required()
def list_sessions():
    all_sessions = Session.query.order_by(Session.created_at.desc()).all()
    return jsonify({'success': True, 'sessions': [s.to_dict(include_stats=True) for s in all_sessions]})


@sessions_bp.route('/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    return jsonify({'success': True, 'session': session.to_dict(include_stats=True)})


@sessions_bp.route('/<int:session_id>/public', methods=['GET'])
def get_session_public(session_id):
    """No login required - powers the user-facing 'request coupons' page."""
    session = Session.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    return jsonify({'success': True, 'session': session.to_dict()})