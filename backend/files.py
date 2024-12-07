import os
import shutil
import threading
import time
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, current_app, send_from_directory, \
    jsonify
from werkzeug.utils import secure_filename

from decorators import login_required
from helpers import allowed_file
from models import db, User, File

files_bp = Blueprint('files', __name__)
CLEANUP_INTERVAL = 3600  # 1 hour
STALE_THRESHOLD = 7200    # 2 hours

cleanup_lock = threading.Lock()

active_uploads = {}

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

    if not all([chunk, chunk_index, total_chunks, file_name, upload_id, file_size]):
        current_app.logger.warning('Missing required upload parameters.')
        return jsonify({"success": False, "error": "Missing required upload parameters."}), 400

    try:
        chunk_index = int(chunk_index)
        total_chunks = int(total_chunks)
        file_size = int(file_size)
    except ValueError:
        current_app.logger.warning('Invalid chunkIndex, totalChunks, or fileSize value.')
        return jsonify({"success": False, "error": "Invalid chunkIndex, totalChunks, or fileSize value."}), 400

    if not allowed_file(file_name, current_app.config['ALLOWED_EXTENSIONS']):
        current_app.logger.warning(f'File type not allowed: {file_name}')
        return jsonify({"success": False, "error": "File type not allowed."}), 400

    filename = secure_filename(file_name)
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    os.makedirs(user_folder, exist_ok=True)

    if user.id not in active_uploads:
        active_uploads[user.id] = {}

    if upload_id not in active_uploads[user.id]:
        # Before starting the upload, check if adding this file would exceed the quota
        projected_used_space = user.used_space + file_size
        # Additionally, add the sizes of other active uploads
        for uid, info in active_uploads[user.id].items():
            projected_used_space += info.get('file_size', 0)
        if projected_used_space > user.quota:
            current_app.logger.warning(
                f'User {user.username} ({user.id}) attempted to upload a file that exceeds their quota.')
            return jsonify({"success": False, "error": "Uploading this file would exceed your storage quota."}), 403

        # Reserve space for this upload
        active_uploads[user.id][upload_id] = {'file_size': file_size}

    temp_dir = os.path.join(user_folder, f'{upload_id}_temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Save the chunk to the temporary directory
    chunk_filename = f'chunk_{chunk_index}'
    chunk_path = os.path.join(temp_dir, chunk_filename)

    try:
        chunk.save(chunk_path)
        # Log at every 25% of chunks uploaded
        if total_chunks >= 4 and (chunk_index + 1) % (total_chunks // 4) == 0:
            current_app.logger.info(f'Chunk {chunk_index + 1}/{total_chunks} saved for upload ID {upload_id}.')
    except Exception as e:
        current_app.logger.error(f'Error saving chunk {chunk_index + 1} for upload ID {upload_id}: {e}')
        return jsonify({"success": False, "error": "Failed to save chunk."}), 500

    # Update or create a tracking file to monitor upload progress
    tracking_file = os.path.join(temp_dir, 'tracking.json')
    try:
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as tf:
                tracking_data = json.load(tf)
        else:
            tracking_data = {
                'uploaded_chunks': [],
                'last_updated': time.time(),
                'file_size': file_size
            }

        if chunk_index not in tracking_data['uploaded_chunks']:
            tracking_data['uploaded_chunks'].append(chunk_index)
            tracking_data['last_updated'] = time.time()

        with open(tracking_file, 'w') as tf:
            json.dump(tracking_data, tf)
    except Exception as e:
        current_app.logger.error(f'Error updating tracking file for upload ID {upload_id}: {e}')
        return jsonify({"success": False, "error": "Failed to update tracking data."}), 500

    # Check if all chunks have been uploaded
    if len(tracking_data['uploaded_chunks']) >= total_chunks:
        final_file_path = os.path.join(user_folder, filename)
        try:
            with open(final_file_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_file_path = os.path.join(temp_dir, f'chunk_{i}')
                    if not os.path.exists(chunk_file_path):
                        current_app.logger.error(f'Missing chunk {i} for upload ID {upload_id}.')
                        return jsonify({"success": False, "error": f"Missing chunk {i}."}), 400
                    with open(chunk_file_path, 'rb') as chunk_file:
                        shutil.copyfileobj(chunk_file, final_file)
            # Cleanup: Remove the temporary directory
            shutil.rmtree(temp_dir)
            current_app.logger.info(f'Upload ID {upload_id} assembled successfully into {final_file_path}.')

            # Update user storage and save the file record in the database
            file_size = os.path.getsize(final_file_path)
            user.used_space += file_size
            db.session.commit()

            new_file = File(
                filename=filename,
                filepath=final_file_path,
                filesize=file_size,
                user_id=user.id
            )
            db.session.add(new_file)
            db.session.commit()

            current_app.logger.info(f'User {user.username} ({user.id}) uploaded file {filename} ({file_size / 1024 / 1024:.2f} MB)')

            # Remove the upload from active_uploads
            if user.id in active_uploads and upload_id in active_uploads[user.id]:
                del active_uploads[user.id][upload_id]

            return jsonify({"success": True, "message": "File upload completed successfully."}), 200
        except Exception as e:
            current_app.logger.error(f'Error assembling file for upload ID {upload_id}: {e}')
            return jsonify({"success": False, "error": "Failed to assemble file."}), 500

    return jsonify({"success": True, "message": "Chunk uploaded successfully."}), 200

@files_bp.route('/cancel_upload', methods=['POST'])
@login_required
def cancel_upload():
    user = g.user
    data = request.get_json()
    upload_id = data.get('upload_id')

    if not upload_id:
        current_app.logger.warning('Cancellation request missing upload_id.')
        return jsonify({"success": False, "error": "Missing upload_id."}), 400

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    temp_dir = os.path.join(user_folder, f'{upload_id}_temp')

    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            current_app.logger.info(f'Cancelled and removed temporary files for upload ID {upload_id}.')

            # Remove the upload from active_uploads
            if user.id in active_uploads and upload_id in active_uploads[user.id]:
                del active_uploads[user.id][upload_id]

            return jsonify({"success": True, "message": "Upload cancelled and temporary files removed."}), 200
        except Exception as e:
            current_app.logger.error(f'Error removing temp directory for upload ID {upload_id}: {e}')
            return jsonify({"success": False, "error": "Failed to remove temporary files."}), 500
    else:
        current_app.logger.warning(f'Temp directory for upload ID {upload_id} does not exist.')
        return jsonify({"success": False, "error": "Upload session not found."}), 404

def cleanup_stale_temp_dirs(app):
    while True:
        with app.app_context():
            with cleanup_lock:
                upload_folders = [
                    f for f in os.listdir(app.config['UPLOAD_FOLDER'])
                    if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], f))
                ]
                for folder in upload_folders:
                    if folder.endswith('_temp'):
                        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder)
                        tracking_file = os.path.join(temp_dir, 'tracking.json')
                        if os.path.exists(tracking_file):
                            try:
                                with open(tracking_file, 'r') as tf:
                                    tracking_data = json.load(tf)
                                    last_updated = tracking_data.get('last_updated', 0)
                                    if time.time() - last_updated > STALE_THRESHOLD:
                                        shutil.rmtree(temp_dir, ignore_errors=True)
                                        app.logger.info(f'Removed stale temp directory: {temp_dir}')
                            except Exception as e:
                                app.logger.error(f'Error reading tracking file {tracking_file}: {e}')
                                shutil.rmtree(temp_dir, ignore_errors=True)
                                app.logger.info(f'Removed corrupted temp directory: {temp_dir}')
        time.sleep(CLEANUP_INTERVAL)


# Start the cleanup thread when the blueprint is registered
@files_bp.record
def on_load(state):
    app = state.app
    cleanup_thread = threading.Thread(target=cleanup_stale_temp_dirs, args=(app,), daemon=True)
    cleanup_thread.start()


@files_bp.route('/files')
@login_required
def files():
    user = g.user
    files = user.files

    # Check for expired shared files
    for file in files:
        if file.is_public and file.is_expired:
            # Update the file's sharing status
            file.is_public = False
            file.share_url = None
            file.password = None
            file.expiration_time = None
            db.session.commit()
            current_app.logger.info(f'File {file.filename} ({file.id}) sharing expired and was updated.')

    return render_template('files.html', files=files, user=user)


@files_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)
    if file.user_id != user.id:
        current_app.logger.warning(
            f'User {user.username} ({user.id}) attempted to download file {file.filename} ({file_id})')
        return 'Access denied.', 403

    return send_from_directory(os.path.dirname(file.filepath), os.path.basename(file.filepath), as_attachment=True)


@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)
    if file.user_id != user.id:
        current_app.logger.warning(
            f'User {user.username} ({user.id}) attempted to delete file {file.filename} ({file_id})')
        flash('Access denied.', 'error')
        return redirect(url_for('files.files'))

    # Delete the file from the filesystem
    if os.path.exists(file.filepath):
        os.remove(file.filepath)
    else:
        current_app.logger.error(f'File {file.filepath} not found on the filesystem.')

    # Update used space
    user = User.query.get(user.id)
    user.used_space -= file.filesize
    db.session.commit()

    # Delete the file record from the database
    db.session.delete(file)
    db.session.commit()

    current_app.logger.info(f'User {user.username} ({user.id}) deleted file {file.filename} ({file_id})')
    flash('File deleted successfully.', 'success')
    return redirect(url_for('files.files'))
