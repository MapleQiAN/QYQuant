from flask import g


def ok(data=None, message='ok', code=0):
    payload = {"code": code, "message": message, "data": data}
    if getattr(g, 'request_id', None):
        payload['request_id'] = g.request_id
    return payload


def error_response(error_code, message, status, details=None):
    payload = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    if getattr(g, 'request_id', None):
        payload['request_id'] = g.request_id
    return payload, status
