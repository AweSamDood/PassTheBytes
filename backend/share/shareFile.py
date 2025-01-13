import os
import uuid
from flask import Blueprint, request, g, jsonify, send_file, abort
from backend.auth.decorators import login_required
from backend.models import db, File, Share
from werkzeug.security import generate_password_hash, check_password_hash


share_bp = Blueprint('share_bp', __name__)

def generate_share_key():
    return str(uuid.uuid4())  # or any random string generator
@share_bp.route('/file/<int:file_id>', methods=['POST'])
@login_required
def toggle_share_file(file_id):
    """
    Toggle share state of a file.
    If not currently shared, create a new Share record.
    If already shared, revoke (delete) the share.

    Body can have: { "password": "...", "revoke": false }
    """
    user = g.user
    data = request.get_json() or {}
    password = data.get('password')  # optional
    revoke = data.get('revoke', False)

    # Check if file belongs to user
    file_obj = File.query.filter_by(id=file_id, user_id=user.id).first()
    if not file_obj:
        return jsonify({"error": "File not found or not owned by user"}), 404

    # Check if share already exists
    existing_share = Share.query.filter_by(
        owner_id=user.id,
        object_type='file',
        object_id=file_id
    ).first()

    if revoke:
        # Revoke (delete) existing share
        if existing_share:
            db.session.delete(existing_share)
            db.session.commit()
            return jsonify({"message": "Share revoked"}), 200
        else:
            return jsonify({"error": "File is not shared"}), 400
    else:
        # Create or update share
        if not existing_share:
            new_share = Share(
                owner_id=user.id,
                object_type='file',
                object_id=file_id,
                share_key=generate_share_key(),
                permission='read',
                # Store hashed password if provided
                password=generate_password_hash(password) if password else None
            )
            db.session.add(new_share)
            db.session.commit()
            return jsonify({
                "message": "File shared successfully",
                "share_key": new_share.share_key
            }), 201
        else:
            # If already shared, consider updating password
            existing_share.password = generate_password_hash(password) if password else None
            db.session.commit()
            return jsonify({
                "message": "Share already existed, password updated",
                "share_key": existing_share.share_key
            }), 200


@share_bp.route('/s/<share_key>', methods=['GET'])
def public_share_page(share_key):
    """
    Render or return data for the share page.
    This can be a minimal page or JSON response
    that your frontend uses to render the share page.
    """
    share = Share.query.filter_by(share_key=share_key).first()
    if not share:
        abort(404, "Invalid share key")
    if share.is_expired:
        abort(410, "Share link expired")

    # Confirm it's for a file
    if share.object_type != 'file':
        abort(400, "Currently only file shares are supported")

    # We can return a minimal HTML or JSON for your React app to handle
    file_id = share.object_id
    file_obj = File.query.filter_by(id=file_id).first()
    if not file_obj:
        abort(404, "File not found")

    # Return basic info, let front-end handle the password prompt if needed
    return jsonify({
        "filename": file_obj.filename,
        "needs_password": share.password is not None
    })
@share_bp.route('/s/<share_key>/download', methods=['POST'])
def public_share_download(share_key):
    """
    Attempt to download the file. If password is set, user must provide correct password.
    The request can have JSON body with {"password": "..."} if needed.
    """
    share = Share.query.filter_by(share_key=share_key).first()
    if not share:
        abort(404, "Invalid share key")
    if share.is_expired:
        abort(410, "Share link expired")

    data = request.get_json() or {}
    provided_password = data.get('password', None)

    # If the share has a hashed password, validate
    if share.password:
        if not provided_password or not check_password_hash(share.password, provided_password):
            abort(403, "Invalid or missing password")

    # All good, proceed with file download
    file_obj = File.query.filter_by(id=share.object_id).first()
    if not file_obj:
        abort(404, "File not found")

    if not os.path.exists(file_obj.filepath):
        abort(404, "File missing on server")

    return send_file(
        file_obj.filepath,
        as_attachment=True,
        download_name=file_obj.filename
    )

