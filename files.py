from flask import Blueprint, render_template, request, redirect, url_for, flash, g, current_app, send_from_directory
from werkzeug.utils import secure_filename

from decorators import login_required
from models import db, User, File
from helpers import allowed_file
import os

files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = g.user
    if request.method == 'POST':
        current_app.logger.info(f'User {user.username} ({user.id}) is uploading a file.')
        file = request.files.get('file')
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

            # Check user's quota
            if user.used_space + file_size > user.quota:
                os.remove(temp_file_path)
                current_app.logger.warning(f'User {user.username} ({user.id}) exceeded their storage quota.')
                flash('Storage quota exceeded.', 'error')
                return redirect(url_for('files.upload'))

            os.rename(temp_file_path, file_path)

            user.used_space += file_size
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
            flash('Invalid file or no file selected.', 'error')
            return redirect(url_for('files.upload'))

    return render_template('upload.html')


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
