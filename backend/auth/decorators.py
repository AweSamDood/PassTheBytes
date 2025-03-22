from functools import wraps
from flask import request, g, jsonify
from backend.models import User
from backend.auth.jwt_utils import decode_token


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Extract token from "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        payload = decode_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401

        if payload['token_type'] != 'access':
            return jsonify({'error': 'Invalid token type'}), 401

        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        g.user = user
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Extract token from "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        payload = decode_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401

        if payload['token_type'] != 'access':
            return jsonify({'error': 'Invalid token type'}), 401

        if not payload.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403

        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403

        g.user = user
        return f(*args, **kwargs)

    return decorated_function