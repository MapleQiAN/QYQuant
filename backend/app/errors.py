import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException


logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        status = err.code or 500
        payload = {
            "code": int(f"{status}00"),
            "message": err.name,
            "details": None,
        }
        return jsonify(payload), status

    @app.errorhandler(Exception)
    def handle_error(err):
        logger.exception("Unhandled application error", exc_info=err)
        payload = {"code": 50000, "message": "internal_error", "details": None}
        return jsonify(payload), 500
