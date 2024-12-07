import os
from flask import Flask, flash, current_app, redirect, url_for, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge, HTTPException

from config import Config
from files import files_bp
from helpers import print_loaded_config
from home import home_bp
from models import db
from auth import auth_bp
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler

from share import share_bp

app = Flask(__name__)
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
app.register_blueprint(auth_bp)
app.register_blueprint(share_bp)
app.register_blueprint(files_bp)
app.register_blueprint(home_bp)




@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    flash('File is too large. Maximum file size is {} bytes.'.format(current_app.config['MAX_CONTENT_LENGTH']), 'error')
    return redirect(url_for('files.files')), 413


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    app.logger.error(f'Unhandled Exception: {e}, route: {request.url}')
    # TODO better handling
    return render_template('errors/500.html'), 500


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error(f'Server Error: {error}, route: {request.url}')
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, use_reloader=False)
