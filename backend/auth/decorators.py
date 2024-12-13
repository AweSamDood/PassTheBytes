from functools import wraps
from flask import session, redirect, url_for, flash, g
from backend.models import User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.api_login'))

        user = User.query.get(session['user_id'])
        if user is None:
            # Clear the session and redirect to login
            session.clear()
            return redirect(url_for('auth.api_login'))

        g.user = user
        return f(*args, **kwargs)

    return decorated_function
