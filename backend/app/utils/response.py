from flask import g


def ok(data=None, message='ok', code=0):
    payload = {"code": code, "message": message, "data": data}
    if getattr(g, 'request_id', None):
        payload['request_id'] = g.request_id
    return payload
