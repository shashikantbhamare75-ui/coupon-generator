from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models.session import Session
from models.coupon import Coupon
from models.admin import Admin

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    total_sessions = Session.query.count()
    total_coupons = Coupon.query.count()
    used_coupons = Coupon.query.filter_by(status='USED').count()
    unused_coupons = Coupon.query.filter_by(status='UNUSED').count()

    today = date.today()
    todays_coupons = Coupon.query.filter(
        Coupon.created_at >= today
    ).count()
    todays_redemptions = Coupon.query.filter(
        Coupon.status == 'USED',
        Coupon.redeemed_at >= today
    ).count()

    return jsonify({
        'success': True,
        'stats': {
            'total_sessions': total_sessions,
            'total_coupons': total_coupons,
            'used_coupons': used_coupons,
            'unused_coupons': unused_coupons,
            'todays_coupons': todays_coupons,
            'todays_redemptions': todays_redemptions
        }
    })


@dashboard_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """Redemption history - only coupons that have actually been redeemed."""
    session_id = request.args.get('session_id', type=int)
    admin_id = request.args.get('admin_id', type=int)
    search = request.args.get('search')

    query = Coupon.query.filter(Coupon.status == 'USED')

    if session_id:
        query = query.filter_by(session_id=session_id)
    if admin_id:
        query = query.filter_by(redeemed_by=str(admin_id))
    if search:
        query = query.filter(Coupon.coupon_code.ilike(f'%{search}%'))

    coupons = query.order_by(Coupon.redeemed_at.desc()).all()

    result = []
    for c in coupons:
        session = Session.query.get(c.session_id)
        admin = Admin.query.get(int(c.redeemed_by)) if c.redeemed_by else None
        result.append({
            'coupon_code': c.coupon_code,
            'session_name': session.session_name if session else None,
            'session_date': session.session_date.isoformat() if session else None,
            'redeemed_at': c.redeemed_at.isoformat() if c.redeemed_at else None,
            'redeemed_by': admin.name if admin else 'Unknown',
            'status': c.status
        })

    return jsonify({'success': True, 'history': result})