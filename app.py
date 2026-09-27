from flask import Flask, render_template
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from models.admin import Admin
from models.session import Session
from models.coupon import Coupon

from routes.auth import auth_bp
from routes.sessions import sessions_bp
from routes.coupons import coupons_bp
from routes.dashboard import dashboard_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(coupons_bp)
    app.register_blueprint(dashboard_bp)

    @app.route('/')
    def index():
        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.route('/sessions')
    def sessions_page():
        return render_template('sessions.html')

    @app.route('/coupons')
    def coupons_page():
        return render_template('coupons.html')

    @app.route('/coupon/<token>')
    def coupon_page(token):
        return render_template('coupon.html')

    @app.route('/scan')
    def scanner_page():
        return render_template('scanner.html')

    @app.route('/history')
    def history_page():
        return render_template('history.html')

    @app.route('/apply/<int:session_id>')
    def apply_page(session_id):
        return render_template('request_coupons.html')

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)