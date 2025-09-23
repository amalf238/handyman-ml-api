# src/api_server.py
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
    create_success_response
)
from ml_model import HandymanMLSystem

setup_logging()
logger = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)

# --- config ---
WORKERS_URL = os.getenv("WORKERS_URL", "").strip()  # NEW: lets you point to GitHub/Drive raw JSON
LOCAL_PATH = os.path.join('data', 'handyman_database_3000.json')
GH_USER = os.getenv("GH_USER", "amalf238")          # fallback only
GH_REPO = os.getenv("GH_REPO", "handyman-ml-api")
GH_FILE = os.getenv("GH_FILE", "data/handyman_database_3000.json")

ml_system: HandymanMLSystem | None = None

def _resolve_dataset_source() -> str:
    # 1) use env url if set
    if WORKERS_URL:
        logger.info(f"Loading dataset from WORKERS_URL: {WORKERS_URL}")
        return WORKERS_URL
    # 2) else local file if present
    if os.path.exists(LOCAL_PATH):
        logger.info(f"Loading dataset from local file: {LOCAL_PATH}")
        return LOCAL_PATH
    # 3) else fallback to GitHub raw (edit GH_* if needed)
    url = get_github_dataset_url(GH_USER, GH_REPO, GH_FILE)
    logger.info(f"Loading dataset from GitHub: {url}")
    return url

def init_ml_system():
    """Initialize the ML system with the dataset"""
    global ml_system
    logger.info("Initializing ML system...")
    dataset_source = _resolve_dataset_source()
    dataset = load_json_dataset(dataset_source)
    if not dataset:
        raise Exception("Dataset could not be loaded")
    ml_system = HandymanMLSystem()
    ml_system.load_dataset_from_dict(dataset)
    ml_system.train_system()
    logger.info("✅ ML system initialized successfully")
    return True

# NOTE: /health is now provided by run.py. Do not define it here.

@app.route('/api/search-workers', methods=['POST'])
def search_workers():
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response('ML system not ready')), 500
        data = request.get_json()
        is_valid, error_message = validate_query(data)
        if not is_valid:
            return jsonify(create_error_response(error_message)), 400

        query = data['query'].strip()
        max_results = data.get('max_results', 5)
        recs = ml_system.get_recommendations(query, max_results)

        formatted = [format_worker_response(
            worker=r['worker'],
            score=r['score'],
            distance=r['distance_km'],
            confidence=r['service_confidence']
        ) for r in recs]

        metadata = {
            'processing_time_ms': 0,
            'ai_analysis': {
                'detected_service': getattr(ml_system, 'last_detected_service', None),
                'detected_location': getattr(ml_system, 'last_detected_location', None)
            }
        }
        return jsonify(create_success_response(formatted, query, metadata))
    except Exception as e:
        logger.error(f"Error in search_workers: {str(e)}")
        return jsonify(create_error_response(str(e))), 500

@app.route('/api/analyze-image-description', methods=['POST'])
def analyze_image_description():
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response('ML system not ready')), 500
        data = request.get_json() or {}
        if 'description' not in data:
            return jsonify(create_error_response('Description parameter is required')), 400
        description = data['description'].strip()
        if not description:
            return jsonify(create_error_response('Description cannot be empty')), 400

        location = data.get('location', 'colombo')
        max_results = data.get('max_results', 3)
        enhanced_query = f"Issue description: {description}. Location: {location}. Need professional help."
        recs = ml_system.get_recommendations(enhanced_query, max_results)

        simplified = [{
            'name': r['worker'].get('worker_name', ''),
            'service': r['worker'].get('service_category', ''),
            'rating': r['worker'].get('rating', 0),
            'phone': r['worker'].get('contact', {}).get('phone_number', ''),
            'daily_rate': r['worker'].get('pricing', {}).get('daily_wage_lkr', 0),
            'available_today': r['worker'].get('availability', {}).get('available_today', False),
            'distance_km': round(r['distance_km'], 1),
            'confidence': round(r['service_confidence'] * 100, 1)
        } for r in recs]

        return jsonify({
            'success': True,
            'analyzed_description': description,
            'recommended_workers': simplified,
            'total_found': len(simplified)
        })
    except Exception as e:
        logger.error(f"Error in analyze_image_description: {str(e)}")
        return jsonify(create_error_response(str(e))), 500
