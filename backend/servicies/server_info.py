import threading
import time
from backend.auth.decorators import admin_required
import requests
from flask import jsonify, current_app
from backend.servicies.upload_clean_up import services_bp

@services_bp.route('/server_info', methods=['GET'])
@admin_required
def server_info():
    url = current_app.config['MONITOR_SERVICE_URL']
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            quicklook = data.get('quicklook', {})
            fs = data.get('fs', [])
            processlist = data.get('processlist', [])
            uptime = data.get('uptime', '')
            network = next((iface for iface in data.get('network', []) if iface.get('interface') == 'w3p3s0'), {})
            server_time = data.get('now', '')
            system = data.get('system', {})
            core = data.get('core', {})

            result = {
                'quicklook': quicklook,
                'fs': fs,
                'processlist': processlist,
                'uptime': uptime,
                'network': network,
                'server_time': server_time,
                'system': system,
                'core': core
            }
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Failed to fetch server info'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'RequestException occurred', 'message': str(e)}), 500



@services_bp.record
def on_load(state):
    app = state.app
    app.server_info = get_server_info(app)
    app.server_info_data = None
    app.server_info_last_update = 0

    def update_server_info():
        while True:
            with app.app_context():
                app.server_info_data = app.server_info()
                app.server_info_last_update = time.time()
            time.sleep(5)

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
            return None

    return get_info

