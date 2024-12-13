import os

from flask import Blueprint, g, current_app, jsonify

from backend.auth.decorators import login_required
from ..helpers import log_warning, log_error, log_info
from ..models import db, File
from backend.crud.files import files_bp

@files_bp.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)

    if file.user_id != user.id:
        log_warning(user,"Delete; Access denied",f"{file.filename} ({file_id})")
        return jsonify({'success': False, 'error': 'Access denied.'}), 403

    # Delete the file from the filesystem
    if os.path.exists(file.filepath):
        os.remove(file.filepath)
    else:
        log_error(user,"Delete; File not found",f"{file.filepath}")
        return jsonify({'success': False, 'error': 'File not found on the filesystem.'}), 404

    # Update user's used space
    user.used_space -= file.filesize
    db.session.commit()

    # Delete the file record from the database
    db.session.delete(file)
    db.session.commit()

    log_info(user,"Delete; File deleted",f"{file.filename} ({file_id})")
    return jsonify({'success': True, 'message': 'File deleted successfully.'}), 200
