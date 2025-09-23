"""
Utility functions for the handyman ML API
"""
import json
import pickle
import os
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log') if os.path.exists('.') else logging.NullHandler()
        ]
    )

def load_json_dataset(file_path: str) -> Dict[str, Any]:
    """
    Load JSON dataset from file or URL
    
    Args:
        file_path: Path to JSON file or URL
        
    Returns:
        Dict containing the loaded dataset
        
    Raises:
        Exception: If file cannot be loaded
    """
    try:
        if file_path.startswith('http'):
            # Load from URL (GitHub raw)
            response = requests.get(file_path, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to download dataset: {response.status_code}")
        else:
            # Load from local file
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
    except Exception as e:
        logger.error(f"Error loading dataset from {file_path}: {str(e)}")
        raise

def save_model(model, file_path: str):
    """
    Save a trained model to disk using pickle
    
    Args:
        model: The model object to save
        file_path: Path where to save the model
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving model to {file_path}: {str(e)}")
        raise

def load_model(file_path: str):
    """
    Load a trained model from disk
    
    Args:
        file_path: Path to the saved model file
        
    Returns:
        The loaded model object
    """
    try:
        with open(file_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from {file_path}")
        return model
    except Exception as e:
        logger.error(f"Error loading model from {file_path}: {str(e)}")
        raise

def validate_query(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate incoming API query data
    
    Args:
        data: Request data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "No data provided"
    
    if 'query' not in data:
        return False, "Query parameter is required"
    
    query = data['query']
    if not isinstance(query, str) or not query.strip():
        return False, "Query must be a non-empty string"
    
    if len(query) > 1000:
        return False, "Query too long (max 1000 characters)"
    
    # Validate optional parameters
    if 'max_results' in data:
        max_results = data['max_results']
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            return False, "max_results must be an integer between 1 and 20"
    
    return True, None

def format_worker_response(worker: Dict[str, Any], score: float, distance: float, confidence: float) -> Dict[str, Any]:
    """
    Format worker data for API response
    
    Args:
        worker: Raw worker data from dataset
        score: AI confidence score
        distance: Distance in kilometers
        confidence: Service confidence score
        
    Returns:
        Formatted worker data for API response
    """
    try:
        return {
            'id': worker.get('worker_id', ''),
            'name': worker.get('worker_name', ''),
            'service_type': worker.get('service_category', ''),
            'rating': float(worker.get('rating', 0)),
            'experience_years': int(worker.get('experience_years', 0)),
            'jobs_completed': int(worker.get('jobs_completed', 0)),
            'location': {
                'city': worker.get('location', {}).get('city', ''),
                'latitude': float(worker.get('location', {}).get('latitude', 0)),
                'longitude': float(worker.get('location', {}).get('longitude', 0))
            },
            'pricing': {
                'daily_wage': int(worker.get('pricing', {}).get('daily_wage_lkr', 0)),
                'half_day_rate': int(worker.get('pricing', {}).get('half_day_rate_lkr', 0)),
                'minimum_charge': int(worker.get('pricing', {}).get('minimum_charge_lkr', 0))
            },
            'contact': {
                'phone': worker.get('contact', {}).get('phone_number', ''),
                'whatsapp_available': bool(worker.get('contact', {}).get('whatsapp_available', False)),
                'email': worker.get('contact', {}).get('email', '')
            },
            'availability': {
                'available_today': bool(worker.get('availability', {}).get('available_today', False)),
                'emergency_service': bool(worker.get('availability', {}).get('emergency_service', False)),
                'working_hours': worker.get('availability', {}).get('working_hours', '')
            },
            'profile': {
                'bio': worker.get('profile', {}).get('bio', ''),
                'specializations': worker.get('profile', {}).get('specializations', [])
            },
            'ai_score': round(float(score), 1),
            'distance_km': round(float(distance), 1),
            'service_confidence': round(float(confidence * 100), 1)
        }
    except Exception as e:
        logger.error(f"Error formatting worker response: {str(e)}")
        # Return minimal safe response
        return {
            'id': worker.get('worker_id', 'unknown'),
            'name': worker.get('worker_name', 'Unknown Worker'),
            'service_type': 'General',
            'rating': 0.0,
            'experience_years': 0,
            'jobs_completed': 0,
            'location': {'city': 'Unknown', 'latitude': 0.0, 'longitude': 0.0},
            'pricing': {'daily_wage': 0, 'half_day_rate': 0, 'minimum_charge': 0},
            'contact': {'phone': '', 'whatsapp_available': False, 'email': ''},
            'availability': {'available_today': False, 'emergency_service': False, 'working_hours': ''},
            'profile': {'bio': '', 'specializations': []},
            'ai_score': 0.0,
            'distance_km': 0.0,
            'service_confidence': 0.0
        }

def get_github_dataset_url(username: str, repo: str, file_path: str) -> str:
    """
    Generate GitHub raw URL for dataset
    
    Args:
        username: GitHub username
        repo: Repository name
        file_path: Path to file in repo
        
    Returns:
        GitHub raw URL
    """
    return f"https://raw.githubusercontent.com/{username}/{repo}/main/{file_path}"

def calculate_distance_score(distance_km: float, max_distance: float = 100.0) -> float:
    """
    Calculate distance-based score
    
    Args:
        distance_km: Distance in kilometers
        max_distance: Maximum distance for scoring
        
    Returns:
        Distance score (0-20)
    """
    if distance_km <= 0:
        return 20.0
    
    # Linear decay: closer = higher score
    score = max(0, 20 - (distance_km / max_distance * 20))
    return min(20.0, score)

def calculate_quality_score(rating: float, max_rating: float = 5.0) -> float:
    """
    Calculate quality-based score from rating
    
    Args:
        rating: Worker rating
        max_rating: Maximum possible rating
        
    Returns:
        Quality score (0-10)
    """
    if rating <= 0:
        return 0.0
    
    return min(10.0, (rating / max_rating) * 10)

def sanitize_text(text: str) -> str:
    """
    Sanitize text input for processing
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Basic sanitization
    text = text.strip()
    text = ' '.join(text.split())  # Remove extra whitespace
    
    # Remove potentially harmful characters
    harmful_chars = ['<', '>', '&', '"', "'", '\x00']
    for char in harmful_chars:
        text = text.replace(char, '')
    
    return text

def create_error_response(error_message: str, status_code: int = 500) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        error_message: Error message
        status_code: HTTP status code
        
    Returns:
        Standardized error response dictionary
    """
    return {
        'success': False,
        'error': error_message,
        'status_code': status_code,
        'workers': [],
        'total_results': 0
    }

def create_success_response(workers: List[Dict[str, Any]], query: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        workers: List of worker recommendations
        query: Original query
        metadata: Additional metadata
        
    Returns:
        Standardized success response dictionary
    """
    return {
        'success': True,
        'query': query,
        'total_results': len(workers),
        'workers': workers,
        'metadata': metadata or {}
    }

class ModelCache:
    """Simple model caching utility"""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str):
        """Get cached model"""
        return self._cache.get(key)
    
    def set(self, key: str, value):
        """Cache model"""
        self._cache[key] = value
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self._cache)

# Global model cache instance
model_cache = ModelCache()