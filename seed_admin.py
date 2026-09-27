"""
Run this once to create a demo admin account.
Usage: python seed_admin.py
"""
from app import create_app
from models import db
from models.admin import Admin

app = create_app()

with app.app_context():
    existing = Admin.query.filter_by(email='admin@example.com').first()
    if existing:
        print("Demo admin already exists: admin@example.com")
    else:
        admin = Admin(name='Demo Admin', email='admin@example.com', password='Admin@123')
        db.session.add(admin)
        db.session.commit()
        print("Demo admin created!")
        print("Email: admin@example.com")
        print("Password: Admin@123")