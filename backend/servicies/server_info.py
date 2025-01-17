import threading
import time
from backend.auth.decorators import admin_required
import requests
from flask import jsonify, current_app

from backend.helpers import log_error
from backend.servicies.upload_clean_up import services_bp

lock = threading.Lock()

@services_bp.route('/server_info', methods=['GET'])
@admin_required
def server_info():
    with lock:  # Ensure thread-safe access to the shared data
        app = current_app
        server_info_data = app.server_info_data.copy() if app.server_info_data else None

    if server_info_data:
        return jsonify(server_info_data), 200
    else:
        return jsonify({'error': 'Server info not available'}), 503

@services_bp.record
def on_load(state):
    app = state.app
    app.server_info = get_server_info(app)
    app.server_info_data = None
    app.server_info_last_update = 0

    def update_server_info():
        while True:
            with app.app_context():
                try:
                    new_data = app.server_info()  # Fetch new server data
                    if new_data:
                        with lock:  # Ensure thread-safe update of the shared data
                            app.server_info_data = new_data
                            app.server_info_last_update = time.time()
                except Exception as e:
                    log_error(None, "ServerInfo", f"Error updating server info: {e}")
            time.sleep(1)  # Wait for 1 second before the next update

    update_thread = threading.Thread(target=update_server_info, daemon=True)
    update_thread.start()

def get_server_info(app):
    def get_info():
        url = app.config['MONITOR_SERVICE_URL']
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            # Log the exception (optional)
            print(f"RequestException: {e}")
            return None

    return get_info
