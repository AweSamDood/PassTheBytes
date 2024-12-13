import flask
from flask import Blueprint, session, request, g, current_app, jsonify
from requests_oauthlib import OAuth2Session

from backend.helpers import log_error, log_info
from backend.models import db, User

auth_bp = Blueprint('auth', __name__)

authorization_base_url = 'https://discord.com/api/oauth2/authorize'
token_url = 'https://discord.com/api/oauth2/token'


@auth_bp.route('/login', methods=['GET'])
def api_login():
    redirect_uri = current_app.config['REDIRECT_URI']
    discord = OAuth2Session(current_app.config['CLIENT_ID'], redirect_uri=redirect_uri, scope=['identify', 'email'])
    authorization_url, state = discord.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return jsonify({'authorization_url': authorization_url}), 200


@auth_bp.route('/callback', methods=['GET'])
def api_callback():
    if 'oauth_state' not in session:
        log_error(None,"Callback","OAuth state missing from session. Please restart the login process.")
        return jsonify({'error': 'OAuth state missing from session. Please restart the login process.'}), 400

    if request.args.get('state') != session['oauth_state']:
        log_error(None,"Callback","OAuth state mismatch. Please restart the login process.")
        return jsonify({'error': 'OAuth state mismatch. Please restart the login process.'}), 400

    redirect_uri = current_app.config['REDIRECT_URI']
    discord = OAuth2Session(current_app.config['CLIENT_ID'], state=session['oauth_state'], redirect_uri=redirect_uri,
                            scope=['identify', 'email'])
    token = discord.fetch_token(token_url, client_secret=current_app.config['CLIENT_SECRET'],
                                authorization_response=request.url)
    session['oauth_token'] = token

    # Fetch the user's profile information
    discord_user = discord.get('https://discord.com/api/users/@me').json()
    session['discord_user'] = discord_user

    # Check or create user
    user = User.query.filter_by(discord_id=discord_user['id']).first()
    if not user:
        admin = discord_user['id'] == current_app.config['ADMIN_DISCORD_USER_ID']
        premium_user = discord_user['id'] == current_app.config['PREMIUM_DISCORD_USER_ID']
        user_storage = 400 * 1024 * 1024 * 1024 if premium_user or admin else current_app.config['DEFAULT_QUOTA']
        user = User(
            discord_id=discord_user['id'],
            username=discord_user['username'],
            email=discord_user.get('email'),
            is_admin=admin,
            quota=user_storage
        )
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f'New user created: {user.username} ({user.id})')

    session['user_id'] = user.id
    g.user = user

    # Redirect to the files page
    log_info(user,"Login","User logged in successfully.")
    redirect_uri = current_app.config['FRONTEND_URI'] + f'/files'
    return flask.redirect(redirect_uri)


@auth_bp.route('/authenticated', methods=['GET'])
def api_authenticated():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            log_info(user,"Authenticated","User is authenticated.")
            return jsonify({'isAuthenticated': True, 'user': {'id': user.id, 'username': user.username}}), 200
    return jsonify({'isAuthenticated': False}), 200


@auth_bp.route('/logout', methods=['POST'])
def api_logout():
    if 'user_id' in session:
        log_info(g.user,"Logout","User logged out successfully.")
        session.clear()
        g.user = None
        return jsonify({'message': 'Logged out successfully.'}), 200
    return jsonify({'message': 'No active session found.'}), 400
