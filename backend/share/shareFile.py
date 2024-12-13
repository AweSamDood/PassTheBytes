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

from backend.auth.decorators import login_required
from backend.helpers import log_warning, log_error, log_info
from backend.models import db, File

share_bp = Blueprint('share', __name__)

#
# @share_bp.route('/share/<int:file_id>', methods=['GET', 'POST'])
# @login_required
# def share_file(file_id):
#     user = g.user
#     file = File.query.get_or_404(file_id)
#     if file.user_id != user.id:
#         log_warning(user, "Share file; Access denied", f"{file.filename} ({file_id})")
#         return redirect(url_for('files.files'))
#
#     if request.method == 'POST':
#         # Generate a unique share URL
#         file.share_url = str(uuid.uuid4())
#         file.is_public = True
#
#         # Optional password protection
#         password = request.form.get('password')
#         if password:
#             file.password = password
#
#         # Optional expiration time
#         expiration = request.form.get('expiration')
#         if expiration:
#             try:
#                 hours = int(expiration)
#                 file.expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=hours)
#             except ValueError:
#                 log_error(user, "Share file; Invalid expiration time", f"{file.filename} ({file_id})")
#                 return redirect(url_for('share.share_file', file_id=file.id))
#
#         db.session.commit()
#         log_info(user, "Share file; File shared", f"{file.filename} ({file_id})")
#         return redirect(url_for('files.files'))
#
#     return render_template('share_file.html', file=file)
# @share_bp.route('/shared/<share_url>', methods=['GET', 'POST'])
# def access_shared_file(share_url):
#     file = File.query.filter_by(share_url=share_url, is_public=True).first_or_404()
#
#     # Check if the file has expired
#     utcnow = datetime.datetime.utcnow()
#     if file.expiration_time and utcnow > file.expiration_time:
#         log_warning(None, "Access shared file; File expired", f"{file.filename} ({file.id})")
#         return redirect(url_for('home.home'))
#
#     # Check for password protection
#     if file.password:
#         if request.method == 'POST':
#             password = request.form.get('password')
#             if password == file.password:
#                 return send_from_directory(os.path.dirname(file.filepath), os.path.basename(file.filepath),
#                                            as_attachment=True)
#             else:
#                 flash('Incorrect password.', 'error')
#         return render_template('access_shared_file.html', file=file)
#     else:
#         # No password, proceed to download
#         return send_from_directory(os.path.dirname(file.filepath), os.path.basename(file.filepath), as_attachment=True)


