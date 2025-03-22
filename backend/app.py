import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, flash, current_app, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.exceptions import RequestEntityTooLarge, HTTPException

from backend.auth.auth import auth_bp
from backend.config import Config
from backend.core.view import files_bp
from backend.helpers import print_loaded_config
from backend.models import db
from backend.servicies import services_bp
from backend.share.shareFile import share_bp
from backend.user import user_bp
from backend.auth.jwt_auth import jwt_auth_bp
from backend.security import init_security
from backend.auth.oauth_check import oauth_check_bp
from backend.auth.discord_test import discord_test_bp


app = Flask(__name__)
limiter = init_security(app)

CORS(
    app,
    supports_credentials=True,
    resources={r"/*": {
        "origins": [
            "https://localhost:3000",
            "https://passthebytes.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }},
)

app.config.from_object(Config)

print_loaded_config(app)

db.init_app(app)
migrate = Migrate(app, db)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/PassTheBytes.log', maxBytes=10240, backupCount=10)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('PassTheBytes startup')

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(share_bp, url_prefix='/api/share')
app.register_blueprint(files_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(services_bp, url_prefix='/api/services')
app.register_blueprint(jwt_auth_bp, url_prefix='/api/jwt')
# REMOVE IN PRODUCTION
# app.register_blueprint(oauth_check_bp, url_prefix='/api/debug')
# app.register_blueprint(discord_test_bp, url_prefix='/api/test')

if limiter:
    # Apply rate limits to sensitive endpoints
    limiter.limit("5 per minute")(app.view_functions["jwt_auth.api_login"])
    limiter.limit("5 per minute")(app.view_functions["jwt_auth.api_callback"])
    limiter.limit("20 per minute")(app.view_functions["jwt_auth.api_refresh_token"])


print(app.url_map)
with app.app_context():
    db.create_all()

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    flash('File is too large. Maximum file size is {} bytes.'.format(current_app.config['MAX_CONTENT_LENGTH']), 'error')
    current_app.logger.warning(f'File is too large: {request.url}')
    return jsonify({'error': 'File is too large.'}), 413


@app.errorhandler(404)
def page_not_found(error):
    current_app.logger.warning(f'Not found: {request.url}')
    return jsonify({'error': 'Not found.'}), 404


@app.errorhandler(403)
def forbidden(error):
    current_app.logger.warning(f'Access denied: {request.url}')
    return jsonify({'error': 'Access denied.'}), 403


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    app.logger.error(f'Unhandled Exception: {e}, route: {request.url}')
    return jsonify({'error': 'Internal Server Error'}), 500


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error(f'Server Error: {error}, route: {request.url}')
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
