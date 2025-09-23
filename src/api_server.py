from __future__ import annotations
import os, logging
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.utils import (
    setup_logging,
    load_json_dataset,
    validate_query,
    format_worker_response,
    get_github_dataset_url,
    create_error_response,
    create_success_response,
)
from src.ml_model import HandymanMLSystem

setup_logging()
log = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)

# ------- config -------
WORKERS_URL = os.getenv("WORKERS_URL", "").strip()
LOCAL_PATH = "data/handyman_database_3000.json"
GH_USER = os.getenv("GH_USER", "").strip()
GH_REPO = os.getenv("GH_REPO", "").strip()
GH_FILE = os.getenv("GH_FILE", "data/handyman_database_3000.json").strip()

ml_system: HandymanMLSystem | None = None

def _resolve_dataset_source() -> str:
    if WORKERS_URL:
        log.info(f"Using WORKERS_URL: {WORKERS_URL}")
        return WORKERS_URL
    if os.path.exists(LOCAL_PATH):
        log.info(f"Using local dataset: {LOCAL_PATH}")
        return LOCAL_PATH
    if GH_USER and GH_REPO:
        url = get_github_dataset_url(GH_USER, GH_REPO, GH_FILE)
        log.info(f"Using GitHub fallback: {url}")
        return url
    raise RuntimeError("No dataset found. Set WORKERS_URL or add local data file.")

def init_ml_system():
    global ml_system
    source = _resolve_dataset_source()
    dataset = load_json_dataset(source)  # handles local path and URL
    if not dataset:
        raise RuntimeError("Dataset could not be loaded")
    ml_system = HandymanMLSystem()
    ml_system.load_dataset_from_dict(dataset)
    ml_system.train_system()
    log.info("ML system ready.")

# --------- business endpoints ---------
@app.post("/api/search-workers")
def search_workers():
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response("ML system not ready")), 500

        data = request.get_json() or {}
        is_valid, error = validate_query(data)
        if not is_valid:
            return jsonify(create_error_response(error)), 400

        query = data["query"].strip()
        max_results = int(data.get("max_results", 5))
        recs = ml_system.get_recommendations(query, max_results)

        formatted = [
            format_worker_response(
                worker=r["worker"],
                score=r["score"],
                distance=r["distance_km"],
                confidence=r["service_confidence"],
            ) for r in recs
        ]
        return jsonify(create_success_response(formatted, query, {"processing_time_ms": 0}))
    except Exception as e:
        log.exception("search_workers failed")
        return jsonify(create_error_response(str(e))), 500

@app.post("/api/analyze-image-description")
def analyze_image_description():
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response("ML system not ready")), 500

        body = request.get_json() or {}
        desc = (body.get("description") or "").strip()
        if not desc:
            return jsonify(create_error_response("Description cannot be empty")), 400

        location = body.get("location", "colombo")
        topn = int(body.get("max_results", 5))
        enhanced = f"Issue description: {desc}. Location: {location}. Need professional help."
        recs = ml_system.get_recommendations(enhanced, topn)

        simplified = [{
            "name": r["worker"].get("worker_name", ""),
            "service": r["worker"].get("service_category", "") or r["worker"].get("service_type",""),
            "rating": r["worker"].get("rating", 0),
            "phone": r["worker"].get("contact", {}).get("phone_number", ""),
            "daily_rate": r["worker"].get("pricing", {}).get("daily_wage_lkr", 0),
            "available_today": r["worker"].get("availability", {}).get("available_today", False),
            "distance_km": round(r["distance_km"], 1),
            "confidence": round(r["service_confidence"] * 100, 1),
        } for r in recs]

        return jsonify({
            "success": True,
            "analyzed_description": desc,
            "recommended_workers": simplified,
            "total_found": len(simplified),
        })
    except Exception as e:
        log.exception("analyze_image_description failed")
        return jsonify(create_error_response(str(e))), 500
