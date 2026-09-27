from functools import wraps
from flask import redirect, url_for
from flask_jwt_extended import verify_jwt_in_request


def admin_page_required(f):
    """Protects HTML page routes - redirects to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated