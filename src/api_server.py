from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from utils import (
    setup_logging, 
    load_json_dataset, 
    validate_query, 
    format_worker_response,
    get_github_dataset_url,
    create_error_response,
    create_success_response
)
from ml_model import HandymanMLSystem

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Initialize ML system globally
ml_system = None

def init_ml_system():
    """Initialize the ML system with the dataset"""
    global ml_system
    try:
        logger.info("Initializing ML system...")
        
        # Try to load dataset from multiple sources
        dataset_path = os.path.join('data', 'handyman_database_3000.json')
        dataset = None
        
        if os.path.exists(dataset_path):
            logger.info(f"Loading dataset from local file: {dataset_path}")
            dataset = load_json_dataset(dataset_path)
        else:
            # Try to load from GitHub (replace with your GitHub details)
            github_url = get_github_dataset_url(
                username="amalf238",  # Replace with your username
                repo="handyman-ml-api", 
                file_path="data/handyman_database_3000.json"
            )
            logger.info(f"Loading dataset from GitHub: {github_url}")
            dataset = load_json_dataset(github_url)
        
        if not dataset:
            raise Exception("Dataset could not be loaded from any source")
        
        # Initialize and train ML system
        ml_system = HandymanMLSystem()
        ml_system.load_dataset_from_dict(dataset)  # Load from dictionary
        ml_system.train_system()
        
        logger.info("✅ ML system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize ML system: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ml_system_ready': ml_system is not None and ml_system.trained,
        'version': '1.0.0'
    })

@app.route('/api/search-workers', methods=['POST'])
def search_workers():
    """Main endpoint for worker recommendations"""
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response('ML system not ready')), 500
        
        data = request.get_json()
        
        # Validate request
        is_valid, error_message = validate_query(data)
        if not is_valid:
            return jsonify(create_error_response(error_message)), 400
        
        query = data['query'].strip()
        max_results = data.get('max_results', 5)
        
        # Get AI recommendations
        recommendations = ml_system.get_recommendations(query, max_results)
        
        # Format response
        formatted_workers = []
        for rec in recommendations:
            worker = rec['worker']
            formatted_worker = format_worker_response(
                worker=worker,
                score=rec['score'],
                distance=rec['distance_km'],
                confidence=rec['service_confidence']
            )
            formatted_workers.append(formatted_worker)
        
        # Create metadata
        metadata = {
            'processing_time_ms': 0,
            'ai_analysis': {
                'detected_service': getattr(ml_system, 'last_detected_service', None),
                'detected_location': getattr(ml_system, 'last_detected_location', None)
            }
        }
        
        return jsonify(create_success_response(formatted_workers, query, metadata))
        
    except Exception as e:
        logger.error(f"Error in search_workers: {str(e)}")
        return jsonify(create_error_response(str(e))), 500

@app.route('/api/analyze-image-description', methods=['POST'])
def analyze_image_description():
    """Endpoint specifically for image descriptions from ChatGPT"""
    try:
        if not ml_system or not ml_system.trained:
            return jsonify(create_error_response('ML system not ready')), 500
        
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify(create_error_response('Description parameter is required')), 400
        
        description = data['description'].strip()
        if not description:
            return jsonify(create_error_response('Description cannot be empty')), 400
        
        location = data.get('location', 'colombo')
        max_results = data.get('max_results', 3)
        
        # Enhanced query with context
        enhanced_query = f"Issue description: {description}. Location: {location}. Need professional help."
        
        # Get recommendations
        recommendations = ml_system.get_recommendations(enhanced_query, max_results)
        
        # Return simplified response for image analysis
        simplified_results = []
        for rec in recommendations:
            worker = rec['worker']
            simplified_results.append({
                'name': worker.get('worker_name', ''),
                'service': worker.get('service_category', ''),
                'rating': worker.get('rating', 0),
                'phone': worker.get('contact', {}).get('phone_number', ''),
                'daily_rate': worker.get('pricing', {}).get('daily_wage_lkr', 0),
                'available_today': worker.get('availability', {}).get('available_today', False),
                'distance_km': round(rec['distance_km'], 1),
                'confidence': round(rec['service_confidence'] * 100, 1)
            })
        
        return jsonify({
            'success': True,
            'analyzed_description': description,
            'recommended_workers': simplified_results,
            'total_found': len(simplified_results)
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_image_description: {str(e)}")
        return jsonify(create_error_response(str(e))), 500

if __name__ == '__main__':
    # Initialize ML system on startup
    try:
        init_ml_system()
        print("🚀 ML system ready!")
    except Exception as e:
        print(f"❌ Startup failed: {str(e)}")
        exit(1)
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)