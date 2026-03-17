from .errors import StrategyRuntimeError


def _assert_type(param_def, value):
    ptype = param_def.get('type')
    key = param_def.get('key', 'unknown')

    if ptype == 'integer':
        if isinstance(value, bool) or not isinstance(value, int):
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "type_integer"})
    elif ptype == 'number':
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "type_number"})
    elif ptype == 'string':
        if not isinstance(value, str):
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "type_string"})
    elif ptype == 'boolean':
        if not isinstance(value, bool):
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "type_boolean"})
    elif ptype == 'enum':
        options = param_def.get('enum') or []
        if value not in options:
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "enum"})


def _assert_range(param_def, value):
    key = param_def.get('key', 'unknown')
    if isinstance(value, bool):
        return
    if not isinstance(value, (int, float)):
        return
    minimum = param_def.get('min')
    maximum = param_def.get('max')
    if minimum is not None and value < minimum:
        raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "min"})
    if maximum is not None and value > maximum:
        raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "max"})


def validate_and_merge_params(param_defs, overrides):
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise StrategyRuntimeError('invalid_strategy_params', {"reason": "params_not_object"})

    definitions = param_defs or []
    if not definitions:
        return dict(overrides)

    result = {}
    known_keys = set()

    for item in definitions:
        if not isinstance(item, dict) or not item.get('key'):
            continue
        key = item['key']
        known_keys.add(key)

        if key in overrides:
            value = overrides[key]
        elif 'default' in item:
            value = item.get('default')
        elif item.get('required'):
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "required"})
        else:
            continue

        _assert_type(item, value)
        _assert_range(item, value)
        result[key] = value

    for key in overrides.keys():
        if key not in known_keys:
            raise StrategyRuntimeError('invalid_strategy_params', {"key": key, "reason": "unknown"})

    return result

