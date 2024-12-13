import json
import os
import shutil
import threading
import time

from flask import Blueprint

from backend.helpers import log_info, log_error

files_bp = Blueprint('files', __name__)

CLEANUP_INTERVAL = 5*60  # 5 minutes
STALE_THRESHOLD = 10*60  # 10 minutes

cleanup_lock = threading.Lock()


# Start the cleanup thread when the blueprint is registered
@files_bp.record
def on_load(state):
    app = state.app
    cleanup_thread = threading.Thread(target=cleanup_stale_temp_dirs, args=(app,), daemon=True)
    cleanup_thread.start()


def cleanup_stale_temp_dirs(app):
    while True:
        with app.app_context():
            with cleanup_lock:
                upload_folders = [
                    f for f in os.listdir(app.config['UPLOAD_FOLDER'])
                    if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], f))
                ]
                for folder in upload_folders:
                    if folder.endswith('_temp'):
                        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder)
                        tracking_file = os.path.join(temp_dir, 'tracking.json')
                        if os.path.exists(tracking_file):
                            try:
                                with open(tracking_file, 'r') as tf:
                                    tracking_data = json.load(tf)
                                    last_updated = tracking_data.get('last_updated', 0)
                                    if time.time() - last_updated > STALE_THRESHOLD:
                                        shutil.rmtree(temp_dir, ignore_errors=True)
                                        log_info(None, "CleanThread", f'Removed stale temp directory: {temp_dir}')
                            except Exception as e:
                                log_error(None, "CleanThread", f'Error reading tracking file {tracking_file}: {e}')
                                shutil.rmtree(temp_dir, ignore_errors=True)
                                log_info(None, "CleanThread", f'Removed corrupted temp directory: {temp_dir}')
        time.sleep(CLEANUP_INTERVAL)
