from flask import (
    Blueprint,
    redirect,
    url_for,
    flash,
    g, current_app
)

from backend.auth.decorators import login_required
from backend.helpers import log_warning, log_info
from backend.models import db, File

share_bp = Blueprint('share', __name__)



@share_bp.route('/revoke_share/<int:file_id>')
@login_required
def revoke_share(file_id):
    user = g.user
    file = File.query.get_or_404(file_id)

    if file.user_id != user.id:
        log_warning(user, "Revoke sharing; Access denied", f"{file.filename} ({file_id})")
        return redirect(url_for('files.files'))

    file.is_public = False
    file.share_url = None
    file.password = None
    file.expiration_time = None
    db.session.commit()

    log_info(user, "Revoke sharing; File sharing revoked", f"{file.filename} ({file_id})")
    return redirect(url_for('files.files'))
