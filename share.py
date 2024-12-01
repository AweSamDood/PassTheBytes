import datetime
import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    g, current_app
)

from decorators import login_required
from models import db, File

share_bp = Blueprint('share', __name__)


@share_bp.route('/share/<int:file_id>', methods=['GET', 'POST'])
@login_required
def share_file(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)
    if file.user_id != user.id:
        current_app.logger.warning(
            f'User {user.username} ({user.id}) attempted to share file {file.filename} ({file_id})')
        flash('Access denied.', 'error')
        return redirect(url_for('files.files'))

    if request.method == 'POST':
        # Generate a unique share URL
        file.share_url = str(uuid.uuid4())
        file.is_public = True

        # Optional password protection
        password = request.form.get('password')
        if password:
            file.password = password

        # Optional expiration time
        expiration = request.form.get('expiration')
        if expiration:
            try:
                hours = int(expiration)
                print(hours)
                now = datetime.datetime.now()
                file.expiration_time = now + datetime.timedelta(hours=hours)
                print(file.expiration_time)
            except ValueError:
                current_app.logger.error(f'Invalid expiration time: {expiration}')
                flash('Invalid expiration time.', 'error')
                return redirect(url_for('share.share_file', file_id=file.id))

        db.session.commit()
        flash('File shared successfully.', 'success')
        current_app.logger.info(
            f'User {user.username} ({user.id}) shared file {file.filename} ({file_id}), URL: {file.share_url}, Expiration: {file.expiration_time}')
        return redirect(url_for('files.files'))

    return render_template('share_file.html', file=file)


@share_bp.route('/shared/<share_url>', methods=['GET', 'POST'])
def access_shared_file(share_url):
    file = File.query.filter_by(share_url=share_url, is_public=True).first_or_404()

    # Check if the file has expired
    utcnow = datetime.datetime.utcnow()
    if file.expiration_time and utcnow > file.expiration_time:
        current_app.logger.warning(f'Shared file {file.filename} ({file.id}) has expired.')
        flash('This shared file has expired.', 'error')
        return redirect(url_for('home.home'))

    # Check for password protection
    if file.password:
        if request.method == 'POST':
            password = request.form.get('password')
            if password == file.password:
                return send_from_directory(os.path.dirname(file.filepath), os.path.basename(file.filepath),
                                           as_attachment=True)
            else:
                flash('Incorrect password.', 'error')
        return render_template('access_shared_file.html', file=file)
    else:
        # No password, proceed to download
        return send_from_directory(os.path.dirname(file.filepath), os.path.basename(file.filepath), as_attachment=True)


@share_bp.route('/revoke_share/<int:file_id>')
@login_required
def revoke_share(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)

    if file.user_id != user.id:
        current_app.logger.warning(
            f'User {user.username} ({user.id}) attempted to revoke sharing for file {file.filename} ({file_id})')
        flash('Access denied.', 'error')
        return redirect(url_for('files.files'))

    file.is_public = False
    file.share_url = None
    file.password = None
    file.expiration_time = None
    db.session.commit()

    current_app.logger.info(f'User {user.username} ({user.id}) revoked sharing for file {file.filename} ({file_id})')
    flash('Sharing revoked for the file.', 'success')
    return redirect(url_for('files.files'))
