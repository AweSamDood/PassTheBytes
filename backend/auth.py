from flask import Blueprint, redirect, url_for, session, request, flash, g, current_app
from requests_oauthlib import OAuth2Session

from decorators import login_required
from models import db, User

auth_bp = Blueprint('auth', __name__)

authorization_base_url = 'https://discord.com/api/oauth2/authorize'
token_url = 'https://discord.com/api/oauth2/token'



@auth_bp.route('/login')
def login():
    redirect_uri = current_app.config['REDIRECT_URI']
    discord = OAuth2Session(current_app.config['CLIENT_ID'], redirect_uri=redirect_uri, scope=['identify', 'email'])
    authorization_url, state = discord.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)


@auth_bp.route('/callback')
def callback():
    if 'oauth_state' not in session:
        return "Error: OAuth state missing from session. Please start the login process again.", 400

    if request.args.get('state') != session['oauth_state']:
        return "Error: OAuth state mismatch. Please start the login process again.", 400

    redirect_uri = current_app.config['REDIRECT_URI']
    discord = OAuth2Session(current_app.config['CLIENT_ID'], state=session['oauth_state'], redirect_uri=redirect_uri,
                            scope=['identify', 'email'])
    token = discord.fetch_token(token_url, client_secret=current_app.config['CLIENT_SECRET'], authorization_response=request.url)
    session['oauth_token'] = token

    # Fetch the user's profile information
    discord_user = discord.get('https://discord.com/api/users/@me').json()
    session['discord_user'] = discord_user
    print(discord_user)

    # Check if the user exists in the database
    user = User.query.filter_by(discord_id=discord_user['id']).first()
    if not user:
        current_app.logger.info(f'User {discord_user["username"]} ({discord_user["id"]}) added to the database.')
        admin = discord_user['id'] == current_app.config['ADMIN_DISCORD_USER_ID']
        if admin:
            current_app.logger.info(f'User {discord_user["username"]} ({discord_user["id"]}) is an admin.')
        premium_user = discord_user['id'] == current_app.config['PREMIUM_DISCORD_USER_ID']
        # premium user has 400GB of storage
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

    session['user_id'] = user.id
    g.user = user
    current_app.logger.info(f'User {user.username} ({user.id}) logged in.')
    return redirect(url_for('files.files'))


@auth_bp.route('/logout')
@login_required
def logout():
    user = g.user
    current_app.logger.info(f'User {user.username} ({user.id}) logged out.')
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home.home'))
