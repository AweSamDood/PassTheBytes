import flask
from flask import Blueprint, session, request, current_app, jsonify
from requests_oauthlib import OAuth2Session

from backend.auth.jwt_utils import generate_access_token, generate_refresh_token, decode_token
from backend.helpers import log_error, log_info
from backend.models import db, User

jwt_auth_bp = Blueprint('jwt_auth', __name__)

authorization_base_url = 'https://discord.com/api/oauth2/authorize'
token_url = 'https://discord.com/api/oauth2/token'


@jwt_auth_bp.route('/login', methods=['GET'])
def api_login():
    if 'oauth_state' in session:
        # If a valid state already exists, reuse it
        log_info(None, "Login", "Reusing existing OAuth state.")
        discord = OAuth2Session(current_app.config['CLIENT_ID'], redirect_uri=current_app.config['REDIRECT_URI'],
                                scope=['identify', 'email'])
        authorization_url = discord.authorization_url(authorization_base_url, state=session['oauth_state'])[0]
    else:
        # Generate a new state
        session.pop('oauth_state', None)
        session.pop('oauth_token', None)
        session.pop('discord_user', None)
        redirect_uri = current_app.config['REDIRECT_URI']
        discord = OAuth2Session(current_app.config['CLIENT_ID'], redirect_uri=redirect_uri, scope=['identify', 'email'])
        authorization_url, state = discord.authorization_url(authorization_base_url)
        session['oauth_state'] = state
        log_info(None, "Login", f"User initiated login process. {state}")

    return jsonify({'authorization_url': authorization_url}), 200


@jwt_auth_bp.route('/callback', methods=['GET'])  # Make sure this matches your REDIRECT_URI
def api_callback():
    if 'oauth_state' not in session:
        log_error(None, "Callback", "OAuth state missing from session. Please restart the login process.")
        return jsonify({'error': 'OAuth state missing from session. Please restart the login process.'}), 400

    if request.args.get('state') != session['oauth_state']:
        log_error(None, "Callback", "OAuth state mismatch. Please restart the login process.")
        # log the state and oauth state
        log_error(None, "Callback",
                  f"Request state: {request.args.get('state')}, Session state: {session['oauth_state']}")
        return jsonify({'error': 'OAuth state mismatch. Please restart the login process.'}), 400

    # Log the OAuth configuration for debugging
    log_info(None, "Callback", f"CLIENT_ID: {current_app.config['CLIENT_ID']}")
    log_info(None, "Callback", f"REDIRECT_URI: {current_app.config['REDIRECT_URI']}")
    log_info(None, "Callback", f"REQUEST_URL: {request.url}")

    redirect_uri = current_app.config['REDIRECT_URI']
    discord = OAuth2Session(current_app.config['CLIENT_ID'], state=session['oauth_state'], redirect_uri=redirect_uri,
                            scope=['identify', 'email'])

    try:
        token = discord.fetch_token(token_url, client_secret=current_app.config['CLIENT_SECRET'],
                                    authorization_response=request.url)
        session['oauth_token'] = token
    except Exception as e:
        log_error(None, "Callback", f"OAuth token fetch error: {str(e)}")
        # Check for specific errors
        if 'invalid_client' in str(e).lower():
            log_error(None, "Callback", "This usually means your CLIENT_ID or CLIENT_SECRET is incorrect, " +
                      "or the redirect URI doesn't match what's registered on Discord.")
        return jsonify({'error': f'OAuth error: {str(e)}'}), 400

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

    # Generate JWT tokens
    access_token = generate_access_token(user.id, user.is_admin)
    refresh_token = generate_refresh_token(user.id)

    log_info(user, "Login", "User logged in successfully.")

    # Clean up session
    session.pop('oauth_state', None)
    session.pop('oauth_token', None)
    session.pop('discord_user', None)

    # Redirect to the frontend with tokens in URL parameters
    redirect_uri = f"{current_app.config['FRONTEND_URI']}/auth?access_token={access_token}&refresh_token={refresh_token}"
    return flask.redirect(redirect_uri)


@jwt_auth_bp.route('/refresh', methods=['POST'])
def api_refresh_token():
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'Refresh token is required'}), 400

    payload = decode_token(refresh_token)
    if 'error' in payload:
        return jsonify({'error': payload['error']}), 401

    if payload['token_type'] != 'refresh':
        return jsonify({'error': 'Invalid token type'}), 401

    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate new access token
    access_token = generate_access_token(user.id, user.is_admin)
    log_info(user, "Token", "Access token refreshed successfully.")

    return jsonify({'access_token': access_token}), 200


@jwt_auth_bp.route('/validate', methods=['GET'])
def api_validate_token():
    token = None
    auth_header = request.headers.get('Authorization')

    if auth_header:
        try:
            token = auth_header.split(' ')[1]  # Extract token from "Bearer <token>"
        except IndexError:
            return jsonify({'isAuthenticated': False, 'error': 'Invalid token format'}), 401

    if not token:
        return jsonify({'isAuthenticated': False}), 200

    payload = decode_token(token)
    if 'error' in payload:
        return jsonify({'isAuthenticated': False, 'error': payload['error']}), 401

    if payload['token_type'] != 'access':
        return jsonify({'isAuthenticated': False, 'error': 'Invalid token type'}), 401

    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'isAuthenticated': False, 'error': 'User not found'}), 404

    return jsonify({
        'isAuthenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'admin': user.is_admin  # Changed is_admin to admin to match frontend expectation
        }
    }), 200