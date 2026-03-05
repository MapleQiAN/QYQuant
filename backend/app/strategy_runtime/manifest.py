from .errors import StrategyRuntimeError


def normalize_zip_path(path):
    if not isinstance(path, str):
        raise StrategyRuntimeError('invalid_archive_path')
    normalized = path.replace('\\', '/').strip()
    if not normalized or normalized.startswith('/'):
        raise StrategyRuntimeError('invalid_archive_path')
    if '..' in normalized.split('/'):
        raise StrategyRuntimeError('invalid_archive_path')
    return normalized.lstrip('./')


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise StrategyRuntimeError('invalid_manifest')

    required = ['schemaVersion', 'kind', 'id', 'name', 'version', 'language', 'runtime', 'entrypoint']
    for key in required:
        if not manifest.get(key):
            raise StrategyRuntimeError(f'missing_{key}')

    if manifest.get('schemaVersion') != '1.0':
        raise StrategyRuntimeError('unsupported_schema')
    if manifest.get('kind') != 'QYStrategy':
        raise StrategyRuntimeError('invalid_kind')

    runtime = manifest.get('runtime') or {}
    if not runtime.get('name') or not runtime.get('version'):
        raise StrategyRuntimeError('invalid_runtime')

    entrypoint = manifest.get('entrypoint') or {}
    if not entrypoint.get('path') or not entrypoint.get('callable'):
        raise StrategyRuntimeError('invalid_entrypoint')

    entrypoint['path'] = normalize_zip_path(entrypoint.get('path'))
    manifest['entrypoint'] = entrypoint
    return manifest

