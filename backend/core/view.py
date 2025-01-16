from typing import Optional
from flask import Blueprint, request, g, jsonify
from backend.auth.decorators import login_required
from backend.models import File, Directory, Share

files_bp = Blueprint('files', __name__)
@files_bp.route('/files', methods=['GET'])
@login_required
def files():
    user = g.user
    dir_id: Optional[int] = request.args.get('dir_id', default=None, type=int)

    if dir_id is None:
        # Root-level files and directories
        files = File.query.filter_by(user_id=user.id, directory_id=None).all()
        directories = Directory.query.filter_by(user_id=user.id, parent_dir_id=None).all()
    else:
        # Files and directories in a specific directory
        files = File.query.filter_by(user_id=user.id, directory_id=dir_id).all()
        directories = Directory.query.filter_by(user_id=user.id, parent_dir_id=dir_id).all()

    files_data = []
    for file in files:
        share_key = get_share_key_for_file(file)
        files_data.append({
            'id': file.id,
            'filename': file.filename,
            'size': file.filesize,
            'share_key': share_key
        })

    dirs_data = [
        {
            'id': directory.id,
            'name': directory.name,
        }
        for directory in directories
    ]

    breadcrumbs = []
    current_dir = Directory.query.get(dir_id) if dir_id else None
    while current_dir:
        breadcrumbs.insert(0, {'id': current_dir.id, 'name': current_dir.name})
        current_dir = current_dir.parent_dir

    breadcrumbs.insert(0, {'id': None, 'name': 'Root'})  # Add Root as the starting point

    # Include user's storage information
    user_data = {
        'id': user.id,
        'username': user.username,
        'used_space': user.used_space,
        'quota': user.quota
    }

    return jsonify({
        'files': files_data,
        'directories': dirs_data,
        'user': user_data,
        'breadcrumbs': breadcrumbs
    }), 200

def get_share_key_for_file(file_obj):
    share = Share.query.filter_by(
        owner_id=file_obj.user_id,
        object_type='file',
        object_id=file_obj.id
    ).first()
    return share.share_key if share else None

