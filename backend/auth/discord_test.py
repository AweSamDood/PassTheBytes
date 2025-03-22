from flask import Blueprint, current_app, jsonify
from requests_oauthlib import OAuth2Session

discord_test_bp = Blueprint('discord_test', __name__)

@discord_test_bp.route('/oauth_config', methods=['GET'])
def oauth_config():
    """Show the current Discord OAuth configuration (without sensitive data)"""
    config = {
        'client_id': current_app.config.get('CLIENT_ID'),
        'has_client_secret': bool(current_app.config.get('CLIENT_SECRET')),
        'redirect_uri': current_app.config.get('REDIRECT_URI'),
        'frontend_uri': current_app.config.get('FRONTEND_URI')
    }
    return jsonify(config)

@discord_test_bp.route('/test_generate_login_url', methods=['GET'])
def test_generate_login_url():
    """Test generating a Discord OAuth URL"""
    redirect_uri = current_app.config['REDIRECT_URI']
    client_id = current_app.config['CLIENT_ID']

    # Create the OAuth2Session
    discord = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=['identify', 'email'])

    # Generate the authorization URL
    authorization_base_url = 'https://discord.com/api/oauth2/authorize'
    login_url, state = discord.authorization_url(authorization_base_url)

    return jsonify({
        'login_url': login_url,
        'state': state,
        'client_id': client_id,
        'redirect_uri': redirect_uri
    })