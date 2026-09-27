from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.session import Session
from models.coupon import Coupon
from utils.qr_generator import generate_qr_code
from utils.pdf_generator import generate_coupons_pdf

coupons_bp = Blueprint('coupons', __name__, url_prefix='/api/coupons')

MAX_COUPONS_PER_REQUEST = 20


@coupons_bp.route('/request/<int:session_id>', methods=['POST'])
def request_coupons(session_id):
    """
    Public endpoint - no login required. A user submits how many coupons they need
    (e.g. family size). Claims that many slots from the session's capacity atomically,
    in FIFO order - first submitters get the first available slots.
    """
    data = request.get_json(silent=True) or {}
    requester_name = (data.get('requester_name') or '').strip() or None

    try:
        count = int(data.get('count'))
        if count <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Please enter a valid number of coupons'}), 400

    if count > MAX_COUPONS_PER_REQUEST:
        return jsonify({'success': False, 'message': f'Maximum {MAX_COUPONS_PER_REQUEST} coupons per request'}), 400

    session = Session.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404

    # Atomic FIFO capacity claim - only succeeds if enough slots remain,
    # evaluated entirely at the database level so concurrent requests can't overbook.
    rows_updated = db.session.query(Session).filter(
        Session.id == session_id,
        (Session.coupons_requested + count) <= Session.attendee_count
    ).update({'coupons_requested': Session.coupons_requested + count}, synchronize_session=False)
    db.session.commit()

    if rows_updated != 1:
        db.session.refresh(session)
        remaining = max(session.attendee_count - session.coupons_requested, 0)
        return jsonify({
            'success': False,
            'message': f'Not enough coupons left for this session. Only {remaining} remaining.'
        }), 409

    db.session.refresh(session)
    start_number = session.coupons_requested - count + 1
    date_str = session.session_date.strftime('%d%m%y')

    created = []
    for i in range(start_number, start_number + count):
        coupon = Coupon(
            session_id=session.id,
            coupon_code=f"FOOD-{date_str}-{i:03d}",
            secure_token=Coupon.generate_secure_token(),
            status='UNUSED',
            requester_name=requester_name
        )
        db.session.add(coupon)
        created.append(coupon)
    db.session.commit()

    for c in created:
        generate_qr_code(c.secure_token, f"{c.secure_token}.png")

    return jsonify({
        'success': True,
        'message': f'{count} coupon(s) generated successfully.',
        'coupons': [c.to_dict(include_token=True) for c in created],
        'session': session.to_dict()
    }), 201


@coupons_bp.route('', methods=['GET'])
@jwt_required()
def list_coupons():
    session_id = request.args.get('session_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search')

    query = Coupon.query
    if session_id:
        query = query.filter_by(session_id=session_id)
    if status:
        query = query.filter_by(status=status.upper())
    if search:
        query = query.filter(Coupon.coupon_code.ilike(f'%{search}%'))

    coupons = query.order_by(Coupon.created_at.desc()).all()
    return jsonify({'success': True, 'coupons': [c.to_dict() for c in coupons]})


@coupons_bp.route('/detailed', methods=['GET'])
@jwt_required()
def list_coupons_detailed():
    session_id = request.args.get('session_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search')

    query = Coupon.query
    if session_id:
        query = query.filter_by(session_id=session_id)
    if status:
        query = query.filter_by(status=status.upper())
    if search:
        query = query.filter(Coupon.coupon_code.ilike(f'%{search}%'))

    coupons = query.order_by(Coupon.created_at.desc()).all()

    result = []
    for c in coupons:
        session = Session.query.get(c.session_id)
        d = c.to_dict()
        d['session_name'] = session.session_name if session else None
        d['session_date'] = session.session_date.isoformat() if session else None
        d['food_item'] = session.food_item if session else None
        result.append(d)

    return jsonify({'success': True, 'coupons': result})


@coupons_bp.route('/<token>', methods=['GET'])
def get_coupon_by_token(token):
    coupon = Coupon.query.filter_by(secure_token=token).first()
    if not coupon:
        return jsonify({'success': False, 'message': 'Coupon not found'}), 404

    session = Session.query.get(coupon.session_id)
    return jsonify({
        'success': True,
        'coupon': {
            'coupon_code': coupon.coupon_code,
            'status': coupon.status,
            'secure_token': coupon.secure_token
        },
        'session': {
            'session_name': session.session_name,
            'session_date': session.session_date.isoformat(),
            'food_item': session.food_item
        }
    })


@coupons_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_coupon():
    data = request.get_json(silent=True) or {}
    token = (data.get('token') or '').strip()
    session_id = data.get('session_id')

    if not token:
        return jsonify({'success': False, 'result': 'INVALID', 'message': 'No token provided'}), 400

    coupon = Coupon.query.filter_by(secure_token=token).first()
    if not coupon:
        return jsonify({'success': False, 'result': 'INVALID', 'message': 'This coupon does not exist or is not valid.'}), 404

    session = Session.query.get(coupon.session_id)

    if session_id and coupon.session_id != int(session_id):
        return jsonify({
            'success': False, 'result': 'WRONG_SESSION',
            'message': 'This coupon belongs to another session/date.',
            'coupon': coupon.to_dict()
        }), 409

    if coupon.status == 'USED':
        return jsonify({
            'success': False, 'result': 'ALREADY_USED',
            'message': 'This coupon has already been redeemed.',
            'coupon': coupon.to_dict(), 'session': session.to_dict() if session else None
        }), 409

    return jsonify({
        'success': True, 'result': 'VALID', 'message': 'Coupon is valid and unused.',
        'coupon': coupon.to_dict(), 'session': session.to_dict() if session else None
    })


@coupons_bp.route('/redeem', methods=['POST'])
@jwt_required()
def redeem_coupon():
    data = request.get_json(silent=True) or {}
    token = (data.get('token') or '').strip()
    session_id = data.get('session_id')
    admin_id = get_jwt_identity()

    if not token:
        return jsonify({'success': False, 'result': 'INVALID', 'message': 'No token provided'}), 400

    coupon = Coupon.query.filter_by(secure_token=token).first()
    if not coupon:
        return jsonify({'success': False, 'result': 'INVALID', 'message': 'This coupon does not exist or is not valid.'}), 404

    session = Session.query.get(coupon.session_id)

    if session_id and coupon.session_id != int(session_id):
        return jsonify({
            'success': False, 'result': 'WRONG_SESSION',
            'message': 'This coupon belongs to another session/date.',
            'coupon': coupon.to_dict()
        }), 409

    rows_updated = db.session.query(Coupon).filter(
        Coupon.secure_token == token,
        Coupon.status == 'UNUSED'
    ).update({
        'status': 'USED',
        'redeemed_at': datetime.now(timezone.utc),
        'redeemed_by': admin_id
    })
    db.session.commit()

    if rows_updated == 1:
        db.session.refresh(coupon)
        return jsonify({
            'success': True, 'result': 'REDEEMED', 'message': 'Coupon Redeemed Successfully',
            'coupon': coupon.to_dict(), 'session': session.to_dict() if session else None
        })
    else:
        db.session.refresh(coupon)
        return jsonify({
            'success': False, 'result': 'ALREADY_USED', 'message': 'Coupon Already Used',
            'coupon': coupon.to_dict(), 'session': session.to_dict() if session else None
        }), 409


@coupons_bp.route('/pdf/<int:session_id>', methods=['GET'])
@jwt_required()
def download_pdf(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404

    coupons = Coupon.query.filter_by(session_id=session_id).order_by(Coupon.coupon_code).all()
    if not coupons:
        return jsonify({'success': False, 'message': 'No coupons generated for this session yet'}), 404

    filename = f"session-{session_id}-coupons.pdf"
    filepath = generate_coupons_pdf(session, coupons, filename)

    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/pdf')