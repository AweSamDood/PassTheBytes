import json
import os
import shutil

from flask import request, g, current_app, jsonify

from backend.auth.decorators import login_required
from backend.core.view import files_bp
from backend.helpers import log_info, log_error, log_warning
from backend.models import db, File, Directory
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
    log_info(user, "Upload chunk", f"{file_name} ({upload_id}) - {chunk_index}/{total_chunks}")

    # Basic validations
    if not all([chunk, chunk_index, total_chunks, file_name, upload_id, file_size]):
        return jsonify({"success": False, "error": "Missing required upload parameters."}), 400

    try:
        chunk_index = int(chunk_index)
        total_chunks = int(total_chunks)
        file_size = int(file_size)
        directory_id = int(directory_id) if directory_id else None
    except ValueError:
        return jsonify({"success": False, "error": "Invalid parameter value."}), 400

    file_name = secure_filename(file_name)

    # Validate directory
    if directory_id:
        directory = Directory.query.filter_by(id=directory_id, user_id=user.id).first()
        if not directory:
            return jsonify({"success": False, "error": "Invalid directory ID."}), 400
        directory_path = directory.path
    else:
        directory_path = ""

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    temp_dir = os.path.join(user_folder, f'{upload_id}_temp')
    os.makedirs(temp_dir, exist_ok=True)

    tracking_file = os.path.join(temp_dir, 'tracking.json')

    # -------------------------------------------------------
    # 1) Handle chunk 0 (the "start" of the upload)
    # -------------------------------------------------------
    if chunk_index == 0:
        # If tracking.json for this upload_id already exists, it suggests chunk 0 was *already* handled
        if os.path.exists(tracking_file):
            # Option A: treat it as an error (client might be re-sending chunk 0 again)
            # return jsonify({"success": False, "error": "Chunk 0 has already been processed."}), 400

            # Option B: return success so the client doesn't keep retrying
            return jsonify({"success": True, "message": "Chunk 0 was already processed."}), 200

        # If tracking.json doesn't exist, proceed to DB check for existing file
        existing_file = File.query.filter_by(
            user_id=user.id,
            directory_id=directory_id,
            filename=file_name
        ).first()
        if existing_file:
            return jsonify({
                "success": False,
                "error": "A file with this name already exists in this directory.",
                "filename": file_name
            }), 409

        # Now create brand-new tracking.json
        tracking_data = {
            'uploaded_chunks': [0],
            'file_size': file_size,
            'directory_id': directory_id,
            'file_name': file_name
        }
        with open(tracking_file, 'w') as tf:
            json.dump(tracking_data, tf)

    # -------------------------------------------------------
    # 2) Handle subsequent chunks (1..total_chunks-1)
    # -------------------------------------------------------
    else:
        # If there's no tracking.json at this point, chunk 0 never properly got through
        if not os.path.exists(tracking_file):
            return jsonify({
                "success": False,
                "error": "Out-of-order chunk. Missing tracking.json (chunk 0 not processed)."
            }), 400

        # Load existing tracking data
        with open(tracking_file, 'r') as tf:
            tracking_data = json.load(tf)

        # If the chunk to be uploaded is not exactly last_uploaded+1, handle as an out-of-order
        uploaded_chunks = tracking_data.get('uploaded_chunks', [])
        last_chunk = max(uploaded_chunks)
        if chunk_index != last_chunk + 1:
            return jsonify({
                "success": False,
                "error": f"Out-of-order chunk. Expected {last_chunk + 1}, got {chunk_index}."
            }), 400

        # Append this chunk index to the list
        uploaded_chunks.append(chunk_index)
        tracking_data['uploaded_chunks'] = uploaded_chunks
        with open(tracking_file, 'w') as tf:
            json.dump(tracking_data, tf)

    # -------------------------------------------------------
    # 3) Save chunk to disk
    # -------------------------------------------------------
    chunk_filename = f'chunk_{chunk_index}'
    chunk_path = os.path.join(temp_dir, chunk_filename)
    try:
        chunk.save(chunk_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save chunk. {e}"}), 500

    # -------------------------------------------------------
    # 4) If this was the last chunk, assemble the file
    # -------------------------------------------------------
    if chunk_index + 1 == total_chunks:
        with open(tracking_file, 'r') as tf:
            tracking_data = json.load(tf)
        # confirm we have all the chunks
        if len(tracking_data['uploaded_chunks']) < total_chunks:
            missing = set(range(total_chunks)) - set(tracking_data['uploaded_chunks'])
            return jsonify({
                "success": False,
                "error": f"Missing chunks: {missing}"
            }), 400

        # Combine chunks
        target_folder = os.path.join(user_folder, directory_path) if directory_path else user_folder
        os.makedirs(target_folder, exist_ok=True)
        final_file_path = os.path.join(target_folder, file_name)

        try:
            with open(final_file_path, 'wb') as final_file:
                for i in range(total_chunks):
                    with open(os.path.join(temp_dir, f'chunk_{i}'), 'rb') as cf:
                        shutil.copyfileobj(cf, final_file)

            # Clean up
            shutil.rmtree(temp_dir)

            # Update user used_space
            final_size = os.path.getsize(final_file_path)
            user.used_space += final_size
            db.session.commit()

            # Create new File record in DB
            new_file = File(
                filename=file_name,
                filepath=final_file_path,
                filesize=final_size,
                user_id=user.id,
                directory_id=directory_id
            )
            db.session.add(new_file)

            try:
                db.session.commit()
                log_info(user, "Upload chunk", f"{file_name} ({upload_id}) - File assembled")
            except Exception:
                # If there's a race condition and another record got in first,
                # handle the unique constraint error (already existing file).
                # Example:
                # db.session.rollback()
                # return jsonify({ "success": False, "error": "...some message..." }), 409
                raise

            return jsonify({"success": True, "message": "File upload completed successfully."}), 200
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to assemble file: {e}"}), 500

    # For intermediate chunks
    return jsonify({
        "success": True,
        "message": f"Chunk {chunk_index}/{total_chunks} uploaded successfully."
    }), 200


@files_bp.route('/cancel_upload', methods=['POST'])
@login_required
def cancel_upload():
    user = g.user
    data = request.get_json()
    upload_id = data.get('upload_id')

    if not upload_id:
        log_warning(user, "Cancel upload", "Missing upload_id")
        return jsonify({"success": False, "error": "Missing upload_id."}), 400

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user.id))
    temp_dir = os.path.join(user_folder, f'{upload_id}_temp')

    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            log_info(user, "Cancel upload", f"{upload_id} - Removed temp files")
            return jsonify({"success": True, "message": "Upload cancelled and temporary files removed."}), 200
        except Exception as e:
            log_error(user, "Cancel upload", f"{upload_id} - Failed to remove temp files: {e}")
            return jsonify({"success": False, "error": "Failed to remove temporary files."}), 500
    else:
        log_warning(user, "Cancel upload", f"{upload_id} - Temp directory not found")
        return jsonify({"success": False, "error": "Upload session not found."}), 404
