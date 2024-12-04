import os
import shutil
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, current_app, send_from_directory, \
    jsonify
from werkzeug.utils import secure_filename

from decorators import login_required
from helpers import allowed_file
from models import db, User, File

files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = g.user
    if request.method == 'POST':
        current_app.logger.info(f'User {user.username} ({user.id}) is uploading a file.')
        current_app.logger.info(f'user.quota type: {type(user.quota)}, user.used_space type: {type(user.used_space)}')
        current_app.logger.info('Attempting to retrieve file from request...')
        file = request.files.get('file')
        current_app.logger.info(f'File retrieved: {file}')

        current_app.logger.info(f'file: {file}')

        file = request.files.get('file')
        if not file or file.filename == '':
            current_app.logger.warning('No file selected for upload.')
            flash('No file selected. Please choose a file to upload.', 'error')
            return redirect(url_for('files.upload'))

        if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(file.filename)
            user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
            os.makedirs(user_folder, exist_ok=True)
            file_path = os.path.join(user_folder, filename)

            # Check if file with same name exists
            if File.query.filter_by(filename=filename, user_id=user.id).first():
                current_app.logger.warning(
                    f'User {user.username} ({user.id}) attempted to upload a file with the same name, {filename}')
                flash('File with the same name already exists.', 'error')
                return redirect(url_for('files.upload'))

            # Save the file to a temporary location
            temp_file_path = file_path + '.tmp'
            try:
                file.save(temp_file_path)
            except Exception as e:
                current_app.logger.error(f'Error saving file for user {user.username} ({user.id}): {e}')
                flash('Error saving file.', 'error')
                return redirect(url_for('files.upload'))

            file_size = os.path.getsize(temp_file_path)

            # Ensure correct types for comparison
            try:
                user_quota = int(user.quota)
                user_used_space = int(user.used_space)
            except ValueError as e:
                current_app.logger.error(f"Error converting quota or used space to integer: {e}")
                flash('Internal server error. Please contact support.', 'error')
                return redirect(url_for('files.upload'))

            # Check user's quota
            if user_used_space + file_size > user_quota:
                os.remove(temp_file_path)
                current_app.logger.warning(f'User {user.username} ({user.id}) exceeded their storage quota.')
                flash('Storage quota exceeded.', 'error')
                return redirect(url_for('files.upload'))

            os.rename(temp_file_path, file_path)

            user.used_space = user_used_space + file_size
            db.session.commit()

            new_file = File(
                filename=filename,
                filepath=file_path,
                filesize=file_size,
                user_id=user.id
            )
            db.session.add(new_file)
            db.session.commit()

            flash('File uploaded successfully.', 'success')
            current_app.logger.info(
                f'User {user.username} ({user.id}) uploaded file {filename} ({file_size / 1024 / 1024:.2f} MB)')
            return redirect(url_for('files.upload'))
        else:
            flash('Invalid file type or no file selected.', 'error')
            return redirect(url_for('files.upload'))

    return render_template('upload.html')



@files_bp.route('/upload_chunk', methods=['POST'])
@login_required
def upload_chunk():
    user = g.user

    # Retrieve metadata and chunk from the request
    chunk = request.files.get('chunk')
    chunk_index = int(request.form.get('chunkIndex'))
    total_chunks = int(request.form.get('totalChunks'))
    file_name = request.form.get('fileName')
    chunk_size = 50 * 1024 * 1024

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    temp_dir = os.path.join(user_folder, f'{secure_filename(file_name)}_temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Calculate total expected size of the file
    total_file_size = chunk_size * total_chunks
    estimated_new_space_usage = user.used_space + total_file_size

    # Check if user quota is exceeded
    if estimated_new_space_usage > user.quota:
        current_app.logger.warning(
            f"User {user.username} ({user.id}) exceeded quota. Used: {user.used_space}, "
            f"New File: {total_file_size}, Quota: {user.quota}"
        )
        # Cleanup the temporary directory if this is the first chunk
        if chunk_index == 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": "Storage quota exceeded"}), 403

    # Save the chunk to a temporary directory
    chunk_path = os.path.join(temp_dir, f'chunk_{chunk_index}')
    try:
        with open(chunk_path, 'wb') as f:
            f.write(chunk.read())
    except Exception as e:
        current_app.logger.error(f"Error saving chunk {chunk_index} for file {file_name}: {e}")
        return jsonify({"error": "Failed to save chunk"}), 500

    # Check if all chunks are received
    if len(os.listdir(temp_dir)) == total_chunks:
        final_file_path = os.path.join(user_folder, secure_filename(file_name))
        try:
            with open(final_file_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_file_path = os.path.join(temp_dir, f'chunk_{i}')
                    with open(chunk_file_path, 'rb') as chunk_file:
                        shutil.copyfileobj(chunk_file, final_file)
            # Cleanup
            shutil.rmtree(temp_dir)
        except Exception as e:
            current_app.logger.error(f"Error assembling file {file_name}: {e}")
            return jsonify({"error": "Failed to assemble file"}), 500

        # Update user storage and save the file record in the database
        file_size = os.path.getsize(final_file_path)
        user.used_space += file_size
        db.session.commit()

        new_file = File(
            filename=secure_filename(file_name),
            filepath=final_file_path,
            filesize=file_size,
            user_id=user.id,
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({"success": True, "message": "File upload completed"})

    return jsonify({"success": True, "message": "Chunk uploaded successfully"})




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
        return 'Access denied.'

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
