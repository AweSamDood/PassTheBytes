import os
from typing import Optional

from flask import request, g, jsonify

from backend.auth.decorators import login_required
from backend.core.view import files_bp
from backend.helpers import log_info
from backend.models import Directory, db


@files_bp.route('/create_directory', methods=['POST'])
@login_required
def create_directory():
    user = g.user
    data = request.get_json()
    name = data.get('name')
    parent_id = data.get('parent_id', None)

    if not name:
        return jsonify({"success": False, "error": "Directory name is required"}), 400

    if parent_id:
        parent_dir = Directory.query.filter_by(id=parent_id, user_id=user.id).first()
        if not parent_dir:
            return jsonify({"success": False, "error": "Invalid parent directory"}), 400

        # Check if directory with the same name already exists under this parent
        existing_dir = Directory.query.filter_by(
            user_id=user.id,
            parent_dir_id=parent_id,
            name=name
        ).first()
        if existing_dir:
            return jsonify({"success": False, "error": "A directory with this name already exists here."}), 400

        path = f"{parent_dir.path}/{name}"
        new_dir = Directory(name=name, user_id=user.id, parent_dir_id=parent_dir.id, path=path)

    else:
        # Root-level directory
        existing_dir = Directory.query.filter_by(
            user_id=user.id,
            parent_dir_id=None,
            name=name
        ).first()
        if existing_dir:
            return jsonify({"success": False, "error": "A directory with this name already exists at root."}), 400

        path = name
        new_dir = Directory(name=name, user_id=user.id, path=path)

    db.session.add(new_dir)
    db.session.commit()

    return jsonify({"success": True, "message": "Directory created"}), 201

@files_bp.route('/delete_directory/<int:directory_id>', methods=['DELETE'])
@login_required
def delete_directory(directory_id):
    user = g.user
    directory: Optional[Directory] = Directory.query.filter_by(id=directory_id, user_id=user.id).first()

    if not directory:
        return jsonify({"success": False, "error": "Directory not found"}), 404

    # Implement logic to delete all files and subdirectories within this directory
    # For simplicity:
    # 1. Delete files
    # 2. Recursively delete child dirs

    dir_deleted, files_deleted = [],[]
    def delete_dir_contents(dir_obj, dd , fd):
        for f in dir_obj.files:
            # delete file from disk
            if os.path.exists(f.filepath):
                os.remove(f.filepath)
            user.used_space -= f.filesize
            files_deleted.append(f.id)
            db.session.delete(f)
        for child in dir_obj.child_dirs:
            delete_dir_contents(child, dd, fd)
            # delete the directory itself
            os.path.exists(child.path) and os.rmdir(child.path)
            db.session.delete(child)
            dir_deleted.append(child.id)

    delete_dir_contents(directory, dir_deleted, files_deleted)
    # delete the directory itself
    os.path.exists(directory.path) and os.rmdir(directory.path)
    db.session.delete(directory)
    db.session.commit()

    log_info(user, "Delete directory", f"Directory {directory.name}({directory_id}) deleted along with {len(files_deleted)} files and {len(dir_deleted)} subdirectories.")
    return jsonify({"success": True, "message": "Directory deleted"}), 200

