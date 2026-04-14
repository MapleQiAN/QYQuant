import json
import os
import zipfile

from ..extensions import db
from ..models import File, Strategy, StrategyVersion
from ..utils.crypto import decrypt_strategy, hash_strategy_source
from .errors import StrategyRuntimeError
from .manifest import normalize_zip_path, validate_manifest


def _can_access_strategy(strategy, user_id):
    if user_id is not None and strategy.owner_id == user_id:
        return True
    return bool(strategy.is_public and strategy.review_status == 'approved')


def _resolve_runtime_strategy(strategy_id, user_id=None):
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        raise StrategyRuntimeError('strategy_not_found')
    if not _can_access_strategy(strategy, user_id):
        raise StrategyRuntimeError('strategy_not_found')

    source_strategy = strategy
    if strategy.source_strategy_id:
        source_strategy = db.session.get(Strategy, strategy.source_strategy_id)
        if source_strategy is None:
            raise StrategyRuntimeError('strategy_source_not_found')

    return strategy, source_strategy


def _find_strategy_version(strategy, source_strategy, version):
    query = StrategyVersion.query.filter_by(strategy_id=source_strategy.id)
    if version:
        query = query.filter_by(version=version)
    strategy_version = query.order_by(StrategyVersion.created_at.desc()).first()
    if not strategy_version:
        raise StrategyRuntimeError('strategy_version_not_found')
    return strategy_version


def load_strategy_package(strategy_id, version, user_id=None):
    if not strategy_id:
        raise StrategyRuntimeError('strategy_id_required')

    strategy, source_strategy = _resolve_runtime_strategy(strategy_id, user_id=user_id)
    strategy_version = _find_strategy_version(strategy, source_strategy, version)
    file_record = db.session.get(File, strategy_version.file_id)
    if not file_record:
        raise StrategyRuntimeError('strategy_file_not_found')

    archive_path = file_record.path
    if not archive_path or not os.path.exists(archive_path):
        raise StrategyRuntimeError('strategy_file_missing')

    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = [normalize_zip_path(name) for name in archive.namelist() if not name.endswith('/')]
            if 'strategy.json' not in names:
                raise StrategyRuntimeError('missing_manifest')

            try:
                manifest_raw = archive.read('strategy.json')
                manifest = json.loads(manifest_raw.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise StrategyRuntimeError('invalid_manifest')

            manifest = validate_manifest(manifest)

            if manifest.get('id') and manifest.get('id') != source_strategy.id:
                raise StrategyRuntimeError('manifest_strategy_mismatch')
            if manifest.get('version') and manifest.get('version') != strategy_version.version:
                raise StrategyRuntimeError('manifest_version_mismatch')

            entrypoint = manifest.get('entrypoint') or {}
            entrypoint_path = normalize_zip_path(entrypoint.get('path'))
            if entrypoint_path not in names:
                raise StrategyRuntimeError('entrypoint_missing')

            code_strategy = strategy if strategy.code_encrypted else source_strategy
            if code_strategy and code_strategy.code_encrypted:
                try:
                    source_bytes = decrypt_strategy(code_strategy.code_encrypted)
                except ValueError as exc:
                    raise StrategyRuntimeError('strategy_decrypt_error', {"reason": str(exc)}) from exc
                if code_strategy.code_hash and hash_strategy_source(source_bytes) != code_strategy.code_hash:
                    raise StrategyRuntimeError('strategy_code_integrity_error')
                source = source_bytes.decode('utf-8')
            else:
                try:
                    source = archive.read(entrypoint_path).decode('utf-8')
                except UnicodeDecodeError:
                    raise StrategyRuntimeError('entrypoint_not_utf8')
    except zipfile.BadZipFile:
        raise StrategyRuntimeError('invalid_archive')

    return {
        "strategy_id": strategy_id,
        "version": strategy_version.version,
        "manifest": manifest,
        "entrypoint_path": entrypoint_path,
        "entrypoint_callable": entrypoint.get('callable'),
        "source": source,
    }
