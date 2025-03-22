from flask import Blueprint, current_app, jsonify

oauth_check_bp = Blueprint('oauth_check', __name__)

@oauth_check_bp.route('/check_oauth_config', methods=['GET'])
def check_oauth_config():
    """
    Check if OAuth configuration is valid
    """
    errors = []

    # Check CLIENT_ID
    client_id = current_app.config.get('CLIENT_ID')
    if not client_id:
        errors.append("CLIENT_ID is missing")

    # Check CLIENT_SECRET
    client_secret = current_app.config.get('CLIENT_SECRET')
    if not client_secret:
        errors.append("CLIENT_SECRET is missing")

    # Check REDIRECT_URI
    redirect_uri = current_app.config.get('REDIRECT_URI')
    if not redirect_uri:
        errors.append("REDIRECT_URI is missing")
    else:
        # Check if REDIRECT_URI points to /api/jwt/callback for JWT mode
        if '/jwt/' in redirect_uri and '/jwt/callback' not in redirect_uri:
            errors.append("REDIRECT_URI should point to /api/jwt/callback for JWT authentication")
        # Check if REDIRECT_URI points to /api/callback for session mode
        elif '/jwt/' not in redirect_uri and '/api/callback' not in redirect_uri:
            errors.append("REDIRECT_URI should point to /api/callback for session authentication")

    return jsonify({
        "client_id": client_id,
        "client_secret_configured": bool(client_secret),
        "redirect_uri": redirect_uri,
        "errors": errors,
        "valid_config": len(errors) == 0
    })