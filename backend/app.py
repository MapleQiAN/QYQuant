from __future__ import annotations

import os

from flask import Flask, jsonify
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__)

    # 生产环境可改为更严格的 allowlist；本地开发先放开即可
    CORS(app)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/hello")
    def hello():
        return jsonify({"message": "Hello from Flask!"})

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)

