import os
import zipfile
from io import BytesIO

from flask import g, send_file, jsonify, make_response, request

from backend.auth.decorators import login_required
from backend.core.view import files_bp
from backend.helpers import log_warning, log_info, log_error
from backend.models import File, Directory


@files_bp.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)

    if file.user_id != user.id:
        log_warning(user, "Download; Access denied", f"{file.filename} ({file_id})")
        return jsonify({'success': False, 'error': 'Access denied.'}), 403

    if not os.path.exists(file.filepath):
        log_error(user, "Download; File not found", f"{file.filename} ({file_id})")
        return jsonify({'success': False, 'error': 'File not found on server.'}), 404

    try:
        response = make_response(send_file(file.filepath, as_attachment=True))
        response.headers['Content-Disposition'] = f'attachment; filename="{file.filename}"'
        response.headers['X-Filename'] = file.filename
        response.headers['Access-Control-Expose-Headers'] = 'X-Filename'
        log_info(user, "Download; File downloaded", f"{file.filename} ({file_id})")
        return response
    except Exception as e:
        log_error(user, "Download; Failed to download file", f"{file.filename} ({file_id})", e)
        return jsonify({'success': False, 'error': 'Failed to download file.'}), 500

@files_bp.route('/download_multiple_items', methods=['POST'])
@login_required
def download_multiple_items():
    user = g.user
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    dir_ids = data.get('dir_ids', [])

    # Get files
    files = File.query.filter(File.id.in_(file_ids), File.user_id == user.id).all()
    if len(files) != len(file_ids):
        log_warning(user, "Download Multiple; Invalid files", f"File IDs: {file_ids}")
        return jsonify({"success": False, "error": "Some files are invalid or not owned by the user."}), 400

    # Get directories
    directories = Directory.query.filter(Directory.id.in_(dir_ids), Directory.user_id == user.id).all()
    if len(directories) != len(dir_ids):
        log_warning(user, "Download Multiple; Invalid directories", f"Directory IDs: {dir_ids}")
        return jsonify({"success": False, "error": "Some directories are invalid or not owned by the user."}), 400

    # Gather all files from directories recursively
    def gather_files_from_directory(dir_obj, all_files, base_path=""):
        relative_dir_path = os.path.join(base_path, dir_obj.name)
        for f in dir_obj.files:
            all_files.append((f, relative_dir_path))
        for child_dir in dir_obj.child_dirs:
            gather_files_from_directory(child_dir, all_files, relative_dir_path)

    all_files_to_zip = [(f, "") for f in files]
    for d in directories:
        gather_files_from_directory(d, all_files_to_zip)

    # Create in-memory ZIP file
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_obj, relative_path in all_files_to_zip:
            if os.path.exists(file_obj.filepath):
                arcname = os.path.join(relative_path, file_obj.filename)  # Include relative path
                zf.write(file_obj.filepath, arcname)
            else:
                log_warning(user, "Download Multiple; File not found", f"{file_obj.filename} ({file_obj.id})")
                return jsonify({"success": False, "error": f"File {file_obj.filename} not found on server."}), 404

    memory_file.seek(0)

    try:
        response = make_response(
            send_file(memory_file, as_attachment=True, download_name="selected_items.zip")
        )
        response.headers['X-Filename'] = 'selected_items.zip'
        response.headers['Access-Control-Expose-Headers'] = 'X-Filename'
        log_info(user, "Download Multiple; Files downloaded", f"{len(all_files_to_zip)} items zipped.")
        return response
    except Exception as e:
        log_error(user, "Download Multiple; Failed to create ZIP file", str(e))
        return jsonify({"success": False, "error": "Failed to create ZIP file."}), 500

