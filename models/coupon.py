import secrets
from datetime import datetime, timezone
from models import db


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    coupon_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    secure_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='UNUSED')  # UNUSED, USED, CANCELLED
    requester_name = db.Column(db.String(120), nullable=True)  # who requested this batch (optional)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    redeemed_at = db.Column(db.DateTime, nullable=True)
    redeemed_by = db.Column(db.String(120), nullable=True)

    @staticmethod
    def generate_secure_token():
        return secrets.token_urlsafe(32)

    def to_dict(self, include_token=False):
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'coupon_code': self.coupon_code,
            'status': self.status,
            'requester_name': self.requester_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'redeemed_at': self.redeemed_at.isoformat() if self.redeemed_at else None,
            'redeemed_by': self.redeemed_by
        }
        if include_token:
            data['secure_token'] = self.secure_token
        return data