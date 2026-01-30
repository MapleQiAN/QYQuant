import os

from flask import request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import File
from ..utils.response import ok

bp = Blueprint('files', __name__, url_prefix='/api/files')

ALLOWED_EXT = {'.py', '.zip', '.txt'}
MAX_SIZE = 5 * 1024 * 1024
BASE_DIR = 'backend/storage'


@bp.post('')
@jwt_required()
def upload():
    f = request.files.get('file')
    if not f:
        return {"code": 40000, "message": "file_required", "details": None}, 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return {"code": 40000, "message": "invalid_file_type", "details": None}, 400
    os.makedirs(BASE_DIR, exist_ok=True)
    path = os.path.join(BASE_DIR, f.filename)
    f.save(path)
    meta = File(
        owner_id=get_jwt_identity(),
        filename=f.filename,
        content_type=f.mimetype,
        size=os.path.getsize(path),
        path=path,
    )
    db.session.add(meta)
    db.session.commit()
    return ok({"id": meta.id})


@bp.get('/<file_id>')
@jwt_required()
def download(file_id):
    meta = File.query.get(file_id)
    if not meta:
        return {"code": 40400, "message": "not_found", "details": None}, 404
    if meta.owner_id != get_jwt_identity():
        return {"code": 40300, "message": "forbidden", "details": None}, 403
    return send_file(meta.path, as_attachment=True)
