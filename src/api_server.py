from __future__ import annotations
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

from .utils import (
    setup_logging,
    load_json_dataset,
    validate_query,
    format_worker_response,
    get_github_dataset_url,
    create_error_response,
    create_success_response,
)
from .ml_model import HandymanMLSystem

# ---------- setup ----------
setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ML system (created on init)
ml_system: HandymanMLSystem | None = None

# Config sources
ENV_WORKERS_URL = os.getenv("WORKERS_URL", "").strip()
LOCAL_PATH = os.getenv("LOCAL_DATA_PATH", "data/handyman_database_3000.json")
FALLBACK_GH_USER = os.getenv("GH_USER", "").strip()       # optional
FALLBACK_GH_REPO = os.getenv("GH_REPO", "").strip()       # optional
FALLBACK_GH_FILE = os.getenv("GH_FILE", "data/handyman_database_3000.json").strip()

def _resolve_dataset_source() -> str:
    """
    Priority:
      1) WORKERS_URL (env)
      2) Local file (if exists)
      3) GitHub raw URL built from GH_USER / GH_REPO / GH_FILE (if GH_USER+GH_REPO provided)
    """
    if ENV_WORKERS_URL:
        logger.info(f"Using dataset from WORKERS_URL: {ENV_WORKERS_URL}")
        return ENV_WORKERS_URL
    if os.path.exists(LOCAL_PATH):
        logger.info(f"Using dataset from local file: {LOCAL_PATH}")
        return LOCAL_PATH
    if FALLBACK_GH_USER and FALLBACK_GH_REPO:
        url = get_github_dataset_url(FALLBACK_GH_USER, FALLBACK_GH_REPO, FALLBACK_GH_FILE)
        logger.info(f"Using dataset from GitHub fallback: {url}")
        return url
    raise RuntimeError("No dataset source configured. Set WORKERS_URL or include local data file.")

def init_ml_system(force: bool = False) -> bool:
    """Initialize the ML system with the dataset (called by run.py)."""
    global ml_system
    logger.info("Initializing ML system...")

    source = _resolve_dataset_source()
    dataset = load_json_dataset(source)  # handles both local paths and URLs

    if not dataset:
        raise RuntimeError("Dataset could not be loaded")

    ml_system = HandymanMLSystem()
    ml_system.load_dataset_from_dict(dataset)
    ml_system.train_system()

    logger.info("✅ ML system initialized successfully")
    return True

# ---------- endpoints ----------
@app.get("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "ml_system_ready": bool(ml_system and ml_system.trained),
        "source": ("env" if ENV_WORKERS_URL else ("local" if os.path.exists(LOCAL_PATH) else "github")),
        "version": "1.0.0",
    })

@app.post("/reload")
def reload_dataset():
    try:
        init_ml_system(force=True)
        return jsonify({"reloaded": True}), 200
    except Exception as e:
        logger.exception("reload failed")
        return jsonify(create_error_response(str(e))), 500

@app.post("/api/search-workers")
def search_workers():
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response("ML system not ready")), 500

        data = request.get_json()
        is_valid, error_message = validate_query(data)
        if not is_valid:
            return jsonify(create_error_response(error_message)), 400

        query = data["query"].strip()
        max_results = data.get("max_results", 5)

        recs = ml_system.get_recommendations(query, max_results)

        formatted = [
            format_worker_response(
                worker=r["worker"],
                score=r["score"],
                distance=r["distance_km"],
                confidence=r["service_confidence"],
            ) for r in recs
        ]

        metadata = {
            "processing_time_ms": 0,
            "ai_analysis": {
                "detected_service": getattr(ml_system, "last_detected_service", None),
                "detected_location": getattr(ml_system, "last_detected_location", None),
            },
        }
        return jsonify(create_success_response(formatted, query, metadata))
    except Exception as e:
        logger.exception("search_workers failed")
        return jsonify(create_error_response(str(e))), 500

@app.post("/api/analyze-image-description")
def analyze_image_description():
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response("ML system not ready")), 500

        data = request.get_json() or {}
        if "description" not in data:
            return jsonify(create_error_response("Description parameter is required")), 400

        description = (data["description"] or "").strip()
        if not description:
            return jsonify(create_error_response("Description cannot be empty")), 400

        location = data.get("location", "colombo")
        max_results = data.get("max_results", 3)

        enhanced_query = f"Issue description: {description}. Location: {location}. Need professional help."
        recs = ml_system.get_recommendations(enhanced_query, max_results)

        simplified = [{
            "name": r["worker"].get("worker_name", ""),
            "service": r["worker"].get("service_category", ""),
            "rating": r["worker"].get("rating", 0),
            "phone": r["worker"].get("contact", {}).get("phone_number", ""),
            "daily_rate": r["worker"].get("pricing", {}).get("daily_wage_lkr", 0),
            "available_today": r["worker"].get("availability", {}).get("available_today", False),
            "distance_km": round(r["distance_km"], 1),
            "confidence": round(r["service_confidence"] * 100, 1),
        } for r in recs]

        return jsonify({
            "success": True,
            "analyzed_description": description,
            "recommended_workers": simplified,
            "total_found": len(simplified),
        })
    except Exception as e:
        logger.exception("analyze_image_description failed")
        return jsonify(create_error_response(str(e))), 500
