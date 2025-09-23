"""
Gunicorn entry + health endpoint (Railway-friendly).
"""
import os, sys, threading, traceback
from typing import Optional, Tuple

# make src/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from flask import jsonify, request
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
            init_ml_system()  # loads dataset, warms model lazily later
            _ml_ready = True
            _ml_error = None
            print("✅ ML system initialized")
        except Exception as e:
            _ml_ready = False
            _ml_error = (str(e), traceback.format_exc())
            print("❌ Failed to initialize ML system:", e)
            print(_ml_error[1])

# ---------- Health + reload here (only here) ----------
@_app.get("/health")
def _health():
    # ALWAYS return 200 so the platform marks us healthy
    return jsonify({"ok": True, "ml_ready": _ml_ready, "error": (_ml_error[0] if _ml_error else None)}), 200

@_app.post("/reload")
def _reload():
    _ensure_ml_ready(force=True)
    return jsonify({"reloaded": True, "ml_ready": _ml_ready, "error": _ml_error[0] if _ml_error else None}), 200

# Lazy init on first real request (skip health/reload)
@_app.before_request
def _lazy_init():
    p = request.path
    if p in ("/health", "/reload"):
        return
    if not _ml_ready:
        _ensure_ml_ready()

# Expose for gunicorn
app = _app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    _ensure_ml_ready()
    app.run(host="0.0.0.0", port=port, debug=False)
