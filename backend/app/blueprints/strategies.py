import hashlib
import json
import os
import uuid
import zipfile

from flask import request
from flask_smorest import Blueprint
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import File, Strategy, StrategyVersion
from ..schemas import StrategySchema
from ..utils.response import ok
from ..utils.time import now_ms

bp = Blueprint('strategies', __name__, url_prefix='/api/strategies')

ALLOWED_IMPORT_EXT = {'.qys', '.zip'}
MAX_IMPORT_SIZE = 20 * 1024 * 1024
STRATEGY_STORE_DIR = 'backend/strategy_store'


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(8192), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_manifest(manifest):
    if not isinstance(manifest, dict):
        return 'manifest_invalid'
    required = ['schemaVersion', 'kind', 'id', 'name', 'version', 'language', 'runtime', 'entrypoint']
    for key in required:
        if not manifest.get(key):
            return f'missing_{key}'
    if manifest.get('schemaVersion') != '1.0':
        return 'unsupported_schema'
    if manifest.get('kind') != 'QYStrategy':
        return 'invalid_kind'
    runtime = manifest.get('runtime') or {}
    if not runtime.get('name') or not runtime.get('version'):
        return 'invalid_runtime'
    entrypoint = manifest.get('entrypoint') or {}
    if not entrypoint.get('path') or not entrypoint.get('callable'):
        return 'invalid_entrypoint'
    return None


def _validate_integrity(zf, manifest):
    files = (manifest.get('integrity') or {}).get('files')
    if not files:
        return None
    for item in files:
        path = item.get('path')
        sha256 = item.get('sha256')
        size = item.get('size')
        if not path or not sha256:
            return 'integrity_missing'
        try:
            data = zf.read(path)
        except KeyError:
            return f'integrity_missing_{path}'
        if size is not None and size != len(data):
            return f'integrity_size_{path}'
        if hashlib.sha256(data).hexdigest() != sha256:
            return f'integrity_hash_{path}'
    return None


def _safe_symbol(manifest):
    universe = manifest.get('universe') or {}
    symbols = universe.get('symbols') or []
    if symbols:
        return symbols[0]
    dataset = (manifest.get('performance') or {}).get('backtest') or {}
    symbol = (dataset.get('dataset') or {}).get('symbol')
    return symbol or 'N/A'


@bp.post('')
def create_strategy():
    payload = request.get_json() or {}
    name = (payload.get('name') or '').strip()
    symbol = (payload.get('symbol') or '').strip()
    if not name:
        return {"code": 40000, "message": "name_required", "details": None}, 400
    if not symbol:
        return {"code": 40000, "message": "symbol_required", "details": None}, 400
    tags = payload.get('tags', [])
    if not isinstance(tags, list):
        tags = []
    status = payload.get('status') or 'draft'
    if status not in {'draft', 'running', 'paused', 'stopped', 'completed'}:
        status = 'draft'
    strategy = Strategy(
        name=name,
        symbol=symbol,
        status=status,
        returns=0,
        win_rate=0,
        max_drawdown=0,
        tags=tags,
        last_update=now_ms(),
        trades=0,
    )
    db.session.add(strategy)
    db.session.commit()
    return ok(StrategySchema().dump(strategy))


@bp.post('/import')
def import_strategy():
    if request.content_length and request.content_length > MAX_IMPORT_SIZE:
        return {"code": 40000, "message": "file_too_large", "details": None}, 400
    incoming = request.files.get('file')
    if not incoming:
        return {"code": 40000, "message": "file_required", "details": None}, 400
    original_name = incoming.filename or ''
    safe_name = secure_filename(original_name)
    original_ext = os.path.splitext(original_name)[1].lower()
    ext = original_ext or os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_IMPORT_EXT:
        return {"code": 40000, "message": "invalid_file_type", "details": None}, 400

    os.makedirs(STRATEGY_STORE_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(STRATEGY_STORE_DIR, stored_name)
    incoming.save(stored_path)

    try:
        with zipfile.ZipFile(stored_path) as zf:
            try:
                manifest_raw = zf.read('strategy.json')
            except KeyError:
                raise ValueError('missing_manifest')
            try:
                manifest = json.loads(manifest_raw.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValueError('invalid_manifest')
            error = _validate_manifest(manifest)
            if error:
                raise ValueError(error)
            entrypoint_path = (manifest.get('entrypoint') or {}).get('path')
            if entrypoint_path:
                entrypoint_path = entrypoint_path.replace('\\', '/').lstrip('./')
            if entrypoint_path and entrypoint_path not in zf.namelist():
                raise ValueError('entrypoint_missing')
            integrity_error = _validate_integrity(zf, manifest)
            if integrity_error:
                raise ValueError(integrity_error)
    except (zipfile.BadZipFile, ValueError) as exc:
        os.remove(stored_path)
        message = str(exc) if isinstance(exc, ValueError) else 'invalid_archive'
        return {"code": 40000, "message": message, "details": None}, 400

    checksum = _sha256_file(stored_path)
    file_size = os.path.getsize(stored_path)
    stored_path_db = stored_path.replace('\\', '/')

    strategy = None
    manifest_id = manifest.get('id')
    if manifest_id:
        strategy = Strategy.query.get(manifest_id)

    tags = manifest.get('tags')
    if not isinstance(tags, list):
        tags = []
    if strategy:
        strategy.name = manifest.get('name', strategy.name)
        strategy.symbol = _safe_symbol(manifest)
        strategy.tags = tags or strategy.tags
        strategy.last_update = now_ms()
    else:
        strategy = Strategy(
            id=manifest_id or None,
            name=manifest.get('name'),
            symbol=_safe_symbol(manifest),
            status='draft',
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=tags,
            last_update=now_ms(),
            trades=0,
        )
        db.session.add(strategy)
        db.session.flush()

    display_name = safe_name or original_name or stored_name
    file_record = File(
        owner_id=None,
        filename=display_name,
        content_type=incoming.mimetype or 'application/zip',
        size=file_size,
        path=stored_path_db,
    )
    db.session.add(file_record)
    db.session.flush()

    version = StrategyVersion(
        strategy_id=strategy.id,
        version=manifest.get('version'),
        file_id=file_record.id,
        checksum=checksum,
    )
    db.session.add(version)
    db.session.commit()

    return ok({
        "strategy": StrategySchema().dump(strategy),
        "version": {
            "id": version.id,
            "version": version.version,
            "checksum": version.checksum,
            "fileId": file_record.id,
        },
        "file": {
            "id": file_record.id,
            "filename": file_record.filename,
            "size": file_record.size,
            "path": file_record.path,
        }
    })


@bp.get('/recent')
def recent():
    items = Strategy.query.order_by(Strategy.last_update.desc()).limit(10).all()
    return ok(StrategySchema(many=True).dump(items))
