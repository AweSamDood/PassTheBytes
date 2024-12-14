import os

from flask import request, g, jsonify, current_app

from backend.auth.decorators import login_required
from backend.core.view import files_bp
from backend.helpers import log_info
from backend.models import db, File, Directory


@files_bp.route('/delete_multiple_items', methods=['DELETE'])
@login_required
def delete_multiple_items():
    user = g.user
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    dir_ids = data.get('dir_ids', [])

    if not isinstance(file_ids, list) or not isinstance(dir_ids, list):
        return jsonify({"success": False, "error": "file_ids and dir_ids should be lists."}), 400

    # Fetch all files and directories
    files = File.query.filter(File.id.in_(file_ids), File.user_id == user.id).all()
    directories = Directory.query.filter(Directory.id.in_(dir_ids), Directory.user_id == user.id).all()

    # Validate all requested items are found and owned by the user
    if len(files) != len(file_ids):
        return jsonify({"success": False, "error": "Some file_ids are invalid or not owned by user."}), 400
    if len(directories) != len(dir_ids):
        return jsonify({"success": False, "error": "Some dir_ids are invalid or not owned by user."}), 400

    # Delete files
    for f in files:
        if os.path.exists(f.filepath):
            os.remove(f.filepath)
        else:
            return jsonify({"success": False, "error": f"File {f.filename} not found on the filesystem."}), 404
        user.used_space -= f.filesize
        db.session.delete(f)

    def delete_directory_contents(dir_obj):
        # Delete files in this directory
        for child_file in dir_obj.files:
            if os.path.exists(child_file.filepath):
                os.remove(child_file.filepath)
            else:
                return False, f"File {child_file.filename} not found on the filesystem."
            user.used_space -= child_file.filesize
            db.session.delete(child_file)

        # Recursively delete child directories
        for child_dir in dir_obj.child_dirs:
            success, error_msg = delete_directory_contents(child_dir)
            if not success:
                return False, error_msg
            # Attempt to remove the directory folder if it exists
            child_dir_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id), child_dir.path)
            if os.path.exists(child_dir_path):
                try:
                    os.rmdir(child_dir_path)  # remove if empty
                except OSError:
                    pass
            db.session.delete(child_dir)

        # Attempt to remove this directory's folder if it exists
        dir_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id), dir_obj.path)
        if os.path.exists(dir_path):
            try:
                os.rmdir(dir_path)
            except OSError:
                pass

        return True, ""

    # Delete directories
    for d in directories:
        success, error_msg = delete_directory_contents(d)
        if not success:
            return jsonify({"success": False, "error": error_msg}), 404
        db.session.delete(d)

    db.session.commit()

    log_info(user, "Delete multiple items",
             f"Deleted {len(files)} files and {len(directories)} directories successfully.")
    return jsonify({
        "success": True,
        "message": f"Deleted {len(files)} files and {len(directories)} directories successfully."
    }), 200
