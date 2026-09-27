from datetime import datetime, timezone
from models import db


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(200), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(20), nullable=True)
    end_time = db.Column(db.String(20), nullable=True)
    food_item = db.Column(db.String(200), nullable=True)
    attendee_count = db.Column(db.Integer, nullable=False, default=0)  # total coupon capacity
    coupons_requested = db.Column(db.Integer, nullable=False, default=0)  # coupons claimed so far
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    coupons = db.relationship('Coupon', backref='session', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_stats=False):
        remaining = max(self.attendee_count - self.coupons_requested, 0)
        data = {
            'id': self.id,
            'session_name': self.session_name,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'food_item': self.food_item,
            'attendee_count': self.attendee_count,
            'coupons_requested': self.coupons_requested,
            'remaining': remaining,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_stats:
            total = len(self.coupons)
            used = sum(1 for c in self.coupons if c.status == 'USED')
            data['stats'] = {
                'total_coupons': total,
                'used_coupons': used,
                'unused_coupons': total - used
            }
        return data