from flask import request, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

limiter = None

def init_security(app):
    """Initialize security features for the application"""
    global limiter

    # 1. Initialize rate limiter
    # Use Redis in production if available
    storage_uri = os.getenv('REDIS_URL', 'memory://')
    if app.config.get('FLASK_ENV') == 'production':
        # Stricter limits in production
        default_limits = ["100 per day", "30 per hour"]
    else:
        # More lenient limits in development
        default_limits = ["200 per day", "50 per hour"]

    # Create the limiter with updated initialization syntax
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=default_limits,
        storage_uri=storage_uri,
    )

    # 2. Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        # HSTS: Force HTTPS for a year
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Prevent browsers from interpreting files as a different MIME type
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking by forbidding embedding in frames
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Enable browser XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Content Security Policy - can be customized based on your needs
        # More permissive to allow proper functionality
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self' https://discord.com;"
        )

        return response

    # 3. Log all requests in production
    @app.before_request
    def log_request_info():
        if not app.debug:
            current_app.logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')

    return limiter