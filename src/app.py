from flask import Flask, Response, jsonify, request, render_template
from flask_cors import CORS
import logging
from datetime import datetime, UTC
import traceback
import os

from .config import Config
from .services.display import DisplayGenerator
from .utils.formatters import format_timestamp, format_error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")
    raise

# Use environment variables to control mode
MOCK_MODE = os.getenv('MOCK_MODE', 'false').lower() == 'true'
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Initialize services based on mode
if MOCK_MODE or FLASK_ENV == 'development':
    logger.info("Running in mock mode with test data")
    from tests.mock_vessel_service import MockVesselFinderService
    vessel_service = MockVesselFinderService()
else:
    logger.info("Running in production mode")
    from .services.vesselfinder_service import VesselFinderService
    vessel_service = VesselFinderService(
        api_key=Config.VESSELFINDER_API_KEY,
        mmsi=Config.MMSI
    )

display_generator = DisplayGenerator(Config.DISPLAY_WIDTH, Config.DISPLAY_HEIGHT)

@app.route('/')
def home():
    """Root route that explains the API."""
    return jsonify({
        "name": "TRMNL Ship Tracker",
        "description": "API for tracking ship positions on TRMNL e-ink display",
        "version": "1.0.0",
        "status": "running",
        "last_update": vessel_service.last_update.isoformat() if vessel_service.last_update else None,
        "mmsi": Config.MMSI,
        "refresh_interval": Config.REFRESH_INTERVAL,
        "mode": "mock" if MOCK_MODE else ("development" if FLASK_ENV == 'development' else "production")
    })

@app.route('/status')
def status():
    """Status endpoint for monitoring."""
    return jsonify({
        "timestamp": datetime.now(UTC).isoformat(),
        "service_status": "operational",
        "last_update": vessel_service.last_update.isoformat() if vessel_service.last_update else None,
        "vessel_data": vessel_service.get_cached_data(),
        "config": {
            "mmsi": Config.MMSI,
            "refresh_interval": Config.REFRESH_INTERVAL,
            "display_dimensions": f"{Config.DISPLAY_WIDTH}x{Config.DISPLAY_HEIGHT}",
            "mode": "mock" if MOCK_MODE else ("development" if FLASK_ENV == 'development' else "production")
        }
    })

@app.route('/webhook', methods=['GET'])
def trmnl_webhook():
    try:
        # Get vessel data
        vessel_data = vessel_service.get_vessel_data()
        logger.info(f"Mode: {'MOCK' if MOCK_MODE else 'PRODUCTION'}")
        logger.info(f"Vessel data retrieved: {vessel_data}")
        
        # Generate BMP image using DisplayGenerator
        image_data = display_generator.create_display(vessel_data)
        logger.info(f"BMP image data generated: {len(image_data)} bytes")
        
        # Return binary image with correct headers
        response = Response(
            image_data,
            mimetype='image/bmp',
            headers={
                'X-TRMNL-Refresh': str(Config.REFRESH_INTERVAL),
                'X-TRMNL-Plugin-UUID': Config.TRMNL_PLUGIN_UUID
            }
        )
        return response
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            display_generator.create_error_display(str(e)),
            mimetype='image/bmp'
        )

@app.route('/debug')
def debug():
    """Debug endpoint to see raw API response."""
    try:
        vessel_data = vessel_service.get_vessel_data()
        return jsonify({
            "vessel_data": vessel_data,
            "api_key_length": len(Config.VESSELFINDER_API_KEY),
            "mmsi": Config.MMSI,
            "last_update": vessel_service.last_update.isoformat() if vessel_service.last_update else None,
            "cache_status": "valid" if vessel_service._is_cache_valid() else "invalid",
            "cache_timeout": Config.CACHE_TIMEOUT,
            "mode": "mock" if MOCK_MODE else ("development" if FLASK_ENV == 'development' else "production")
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
        
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    logger.info(f"Starting TRMNL Ship Tracker")
    logger.info(f"Plugin UUID: {Config.TRMNL_PLUGIN_UUID}")
    logger.info(f"Target MMSI: {Config.MMSI}")
    logger.info(f"Refresh Interval: {Config.REFRESH_INTERVAL} seconds")
    logger.info(f"Mode: {'mock' if MOCK_MODE else ('development' if FLASK_ENV == 'development' else 'production')}")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )