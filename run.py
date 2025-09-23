"""
Main entry point for the Handyman ML API
"""
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api_server import app, init_ml_system
from src.utils import setup_logging

if __name__ == '__main__':
    # Setup logging
    setup_logging()
    
    # Initialize ML system
    try:
        init_ml_system()
        print("✅ ML system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ML system: {str(e)}")
        sys.exit(1)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Handyman ML API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)