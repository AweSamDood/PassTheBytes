import json
import os
import shutil
import time

from flask import request, g, current_app, jsonify

from backend.auth.decorators import login_required
from ..helpers import log_info, log_error, log_warning
from ..models import db, File, Directory
from backend.crud.files import files_bp
from werkzeug.utils import secure_filename

@files_bp.route('/upload_chunk', methods=['POST'])
@login_required
def upload_chunk():
    user = g.user

    chunk = request.files.get('chunk')
    chunk_index = request.form.get('chunkIndex')
    total_chunks = request.form.get('totalChunks')
    file_name = request.form.get('fileName')
    upload_id = request.form.get('uploadId')
    file_size = request.form.get('fileSize')
    directory_id = request.form.get('directoryId', None)
    log_info(user,"Upload chunk",f"{upload_id} - {file_name} - {chunk_index}/{total_chunks}")

    # Validate required parameters
    if not all([chunk, chunk_index, total_chunks, file_name, upload_id, file_size]):
        log_warning(user,"Upload chunk","Missing required upload parameters")
        return jsonify({"success": False, "error": "Missing required upload parameters."}), 400

    try:
        chunk_index = int(chunk_index)
        total_chunks = int(total_chunks)
        file_size = int(file_size)
        directory_id = int(directory_id) if directory_id else None
    except ValueError:
        return jsonify({"success": False, "error": "Invalid parameter value."}), 400

    # Validate directory_id
    if directory_id:
        directory = Directory.query.filter_by(id=directory_id, user_id=user.id).first()
        if not directory:
            return jsonify({"success": False, "error": "Invalid directory ID."}), 400
        # construct directory path for the file
        # reverse through directory tree to get the full path
        directory_path = directory.name
        parent = directory.parent
        while parent:
            directory_path = os.path.join(parent.name, directory_path)
            parent = parent.parent
    else:
        directory_path = "./"

    # Create user's folder structure if it doesn't exist
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    target_folder = os.path.join(user_folder, directory_path)
    os.makedirs(target_folder, exist_ok=True)

    # Ensure temp directory exists for chunked uploads
    temp_dir = os.path.join(user_folder, f'{upload_id}_temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Save the chunk to the temporary directory
    chunk_filename = f'chunk_{chunk_index}'
    chunk_path = os.path.join(temp_dir, chunk_filename)
    try:
        chunk.save(chunk_path)
    except Exception as e:
        log_error(user,"Upload chunk",f"{upload_id} - {file_name} - Failed to save chunk: {e}")
        return jsonify({"success": False, "error": "Failed to save chunk."}), 500

    # Update tracking data
    tracking_file = os.path.join(temp_dir, 'tracking.json')
    tracking_data = {
        'uploaded_chunks': [],
        'file_size': file_size,
        'directory_id': directory_id,
        'file_name': file_name,
        'last_updated': time.time()
    }

    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as tf:
            tracking_data = json.load(tf)

    if 'uploaded_chunks' not in tracking_data:
        tracking_data['uploaded_chunks'] = []
    if chunk_index not in tracking_data['uploaded_chunks']:
        tracking_data['uploaded_chunks'].append(chunk_index)

    # Update last_updated time
    tracking_data['last_updated'] = time.time()

    with open(tracking_file, 'w') as tf:
        json.dump(tracking_data, tf)

    # Check if all chunks have been uploaded
    if len(tracking_data['uploaded_chunks']) >= total_chunks:
        file_name = secure_filename(file_name)
        final_file_path = os.path.join(target_folder, file_name)
        try:
            with open(final_file_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_file_path = os.path.join(temp_dir, f'chunk_{i}')
                    if not os.path.exists(chunk_file_path):
                        return jsonify({"success": False, "error": f"Missing chunk {i}."}), 400
                    with open(chunk_file_path, 'rb') as chunk_file:
                        shutil.copyfileobj(chunk_file, final_file)
            shutil.rmtree(temp_dir)

            # Update user's used space and save the file metadata
            file_size = os.path.getsize(final_file_path)
            user.used_space += file_size
            db.session.commit()

            new_file = File(
                filename=file_name,
                filepath=final_file_path,
                filesize=file_size,
                user_id=user.id,
                directory_id=directory_id
            )
            db.session.add(new_file)
            db.session.commit()

            log_info(user,"Upload chunk",f"{upload_id} - {file_name} - Completed")
            return jsonify({"success": True, "message": "File upload completed successfully."}), 200
        except Exception as e:
            log_error(user,"Upload chunk",f"{upload_id} - {file_name} - Failed to assemble file: {e}")
            return jsonify({"success": False, "error": "Failed to assemble file."}), 500

    return jsonify({"success": True, "message": f"Chunk {chunk_index}/{total_chunks} uploaded successfully."}), 200


@files_bp.route('/cancel_upload', methods=['POST'])
@login_required
def cancel_upload():
    user = g.user
    data = request.get_json()
    upload_id = data.get('upload_id')

    if not upload_id:
        log_warning(user,"Cancel upload","Missing upload_id")
        return jsonify({"success": False, "error": "Missing upload_id."}), 400

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    temp_dir = os.path.join(user_folder, f'{upload_id}_temp')

    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            log_info(user,"Cancel upload",f"{upload_id} - Removed temp files")
            return jsonify({"success": True, "message": "Upload cancelled and temporary files removed."}), 200
        except Exception as e:
            log_error(user,"Cancel upload",f"{upload_id} - Failed to remove temp files: {e}")
            return jsonify({"success": False, "error": "Failed to remove temporary files."}), 500
    else:
        log_warning(user,"Cancel upload",f"{upload_id} - Temp directory not found")
        return jsonify({"success": False, "error": "Upload session not found."}), 404