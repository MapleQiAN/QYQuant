import os
import uuid

from flask import current_app, request, send_file, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import File
from ..utils.response import ok

bp = Blueprint('files', __name__, url_prefix='/api/files')

DOCUMENT_EXTENSIONS = {'.py', '.zip', '.txt'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
ALLOWED_EXT = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS
MAX_SIZE = 5 * 1024 * 1024


def _storage_dir():
    configured = current_app.config.get('FILE_STORAGE_DIR')
    if configured:
        return configured
    return os.path.join(current_app.root_path, '..', 'storage', 'files')


def _error(message, status):
    return {"code": status * 100, "message": message, "details": None}, status


def _is_public_image(meta):
    ext = os.path.splitext(meta.filename or '')[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return True
    return (meta.content_type or '').startswith('image/')


@bp.post('')
@jwt_required()
def upload():
    f = request.files.get('file')
    if not f:
        return _error('file_required', 400)

    original_name = secure_filename(f.filename or '')
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXT:
        return _error('invalid_file_type', 400)

    storage_dir = os.path.abspath(_storage_dir())
    os.makedirs(storage_dir, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(storage_dir, stored_name)
    f.save(path)
    size = os.path.getsize(path)
    if size > MAX_SIZE:
        os.remove(path)
        return _error('file_too_large', 400)

    meta = File(
        owner_id=get_jwt_identity(),
        filename=original_name or stored_name,
        content_type=f.mimetype or 'application/octet-stream',
        size=size,
        path=path,
    )
    db.session.add(meta)
    db.session.commit()

    payload = {"id": meta.id}
    if _is_public_image(meta):
        payload["url"] = url_for('files.public_content', file_id=meta.id)
    return ok(payload)


@bp.get('/<file_id>')
@jwt_required()
def download(file_id):
    meta = db.session.get(File, file_id)
    if not meta:
        return _error('not_found', 404)
    if meta.owner_id != get_jwt_identity():
        return _error('forbidden', 403)
    return send_file(meta.path, as_attachment=True, download_name=meta.filename)


@bp.get('/<file_id>/content')
def public_content(file_id):
    meta = db.session.get(File, file_id)
    if not meta:
        return _error('not_found', 404)
    if not _is_public_image(meta):
        return _error('forbidden', 403)
    return send_file(meta.path, mimetype=meta.content_type, as_attachment=False)
