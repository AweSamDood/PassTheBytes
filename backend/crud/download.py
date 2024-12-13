from flask import g, send_file, jsonify, make_response

from backend.auth.decorators import login_required
from backend.crud.files import files_bp
from ..helpers import log_warning, log_info, log_error
from ..models import File


@files_bp.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)

    if file.user_id != user.id:
        log_warning(user, "Download; Access denied", f"{file.filename} ({file_id})")
        return jsonify({'success': False, 'error': 'Access denied.'}), 403

    try:
        response = make_response(send_file(file.filepath, as_attachment=True))
        # Set Content-Disposition and custom filename header
        response.headers['Content-Disposition'] = f'attachment; filename="{file.filename}"'
        response.headers['x-filename'] = file.filename
        log_info(user, "Download; File downloaded", f"{file.filename} ({file_id})")
        return response
    except Exception as e:
        log_error(user, "Download; Failed to download file", f"{file.filename} ({file_id})")
        return jsonify({'success': False, 'error': 'Failed to download file.'}), 500
