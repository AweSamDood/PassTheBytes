from functools import wraps
from flask import session, redirect, url_for, flash, g
from models import User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.get(session['user_id'])
        if user is None:
            # Clear the session and redirect to login
            session.clear()
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('auth.login'))

        # Set the user in the global context for use in the route
        g.user = user
        return f(*args, **kwargs)

    return decorated_function
