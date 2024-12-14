from typing import Optional

from flask import Blueprint, request, g, jsonify

from backend.auth.decorators import login_required
from backend.models import File, Directory

files_bp = Blueprint('files', __name__)

@files_bp.route('/files', methods=['GET'])
@login_required
def files():
    user = g.user
    dir_id : Optional[int] = request.args.get('dir_id', default=None, type=int)

    if dir_id is None:
        # Root-level files and directories
        files = File.query.filter_by(user_id=user.id, directory_id=None).all()
        directories = Directory.query.filter_by(user_id=user.id, parent_dir_id=None).all()
    else:
        # Files and directories in a specific directory
        files = File.query.filter_by(user_id=user.id, directory_id=dir_id).all()
        directories = Directory.query.filter_by(user_id=user.id, parent_dir_id=dir_id).all()

    files_data = [
        {
            'id': file.id,
            'filename': file.filename,
            'filesize': file.filesize,
            'is_public': file.is_public,
            'is_expired': file.is_expired,
            'share_url': file.share_url
        }
        for file in files
    ]

    dirs_data = [
        {
            'id': directory.id,
            'name': directory.name,
        }
        for directory in directories
    ]

    # Include user's storage information
    user_data = {
        'id': user.id,
        'username': user.username,
        'used_space': user.used_space,
        'quota': user.quota
    }

    return jsonify({'files': files_data, 'directories': dirs_data, 'user': user_data}), 200


