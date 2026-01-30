import uuid

from flask import g, request


def register_request_id(app):
    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get('X-Request-Id') or str(uuid.uuid4())

    @app.after_request
    def attach_request_id(resp):
        resp.headers['X-Request-Id'] = g.request_id
        return resp
