from flask import Blueprint, session, redirect, url_for

from models import User

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return redirect(url_for('files.files'))
        else:
            # Clear the session if the user no longer exists
            session.clear()
    return '<a href="/login">Login with Discord</a>'
