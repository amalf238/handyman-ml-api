"""
Handyman ML API - entrypoint for Gunicorn (run:app) and local dev.
Initializes ML once (lazy) and exposes /health and /reload.
"""
import os, sys, threading, traceback
from typing import Tuple, Optional

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.api_server import app as _app, init_ml_system
from src.utils import setup_logging

_ml_ready = False
_ml_lock = threading.Lock()
_ml_error: Optional[Tuple[str, str]] = None  # (message, traceback)

def _ensure_ml_ready(force: bool = False):
    global _ml_ready, _ml_error
    if _ml_ready and not force:
        return
    with _ml_lock:
        if _ml_ready and not force:
            return
        try:
            setup_logging()
            init_ml_system(force=force)
            _ml_ready = True
            _ml_error = None
            print("✅ ML system initialized")
        except Exception as e:
            _ml_ready = False
            _ml_error = (str(e), traceback.format_exc())
            print("❌ Failed to initialize ML system:", e)
            print(_ml_error[1])

# Optional eager warmup
if os.getenv("WARMUP_ON_START", "false").lower() == "true":
    threading.Thread(target=_ensure_ml_ready, name="ml-warmup", daemon=True).start()

# System endpoints layered here
from flask import jsonify, request

@_app.get("/health")
def _health():
    status = {"ok": True, "ml_ready": _ml_ready}
    if _ml_error:
        status["ml_error"] = _ml_error[0]
    return jsonify(status), 200

@_app.post("/reload")
def _reload():
    _ensure_ml_ready(force=True)
    return jsonify({"reloaded": True, "ml_ready": _ml_ready, "error": _ml_error[0] if _ml_error else None})

@_app.before_request
def _lazy_init():
    if request.path in ("/health", "/reload"):
        return
    if not _ml_ready:
        _ensure_ml_ready()

# Expose for Gunicorn
app = _app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    print(f"🚀 Starting Handyman ML API on port {port} (debug={debug})")
    if os.getenv("WARMUP_ON_START", "true").lower() == "true":
        _ensure_ml_ready()
    app.run(host="0.0.0.0", port=port, debug=debug)