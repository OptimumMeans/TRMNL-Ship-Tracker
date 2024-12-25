from flask import Flask, Response, jsonify, request, render_template
from flask_cors import CORS
import logging
from datetime import datetime, UTC

from .config import Config
from .services.display import DisplayGenerator
from .services.vesselfinder_service import VesselFinderService
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

# Initialize services
display_generator = DisplayGenerator(Config.DISPLAY_WIDTH, Config.DISPLAY_HEIGHT)
vessel_service = VesselFinderService(
    api_key=Config.VESSELFINDER_API_KEY,
    mmsi=Config.MMSI
)

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
        "refresh_interval": Config.REFRESH_INTERVAL
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
            "display_dimensions": f"{Config.DISPLAY_WIDTH}x{Config.DISPLAY_HEIGHT}"
        }
    })

@app.route('/webhook', methods=['GET'])
def trmnl_webhook():
    """TRMNL webhook endpoint."""
    try:
        # Get latest vessel data
        vessel_data = vessel_service.get_vessel_data()
        
        if not vessel_data:
            return render_template('error.html', message="Unable to fetch vessel data")
        
        # Create display data
        display_data = {
            'ship_name': vessel_data['ship_name'],
            'mmsi': vessel_data['mmsi'],
            'position': f"{vessel_data['lat']}°, {vessel_data['lon']}°",
            'speed': vessel_data['speed'],
            'course': vessel_data['course'],
            'last_update': format_timestamp(vessel_data['timestamp'])
        }
        
        # Return template response
        return render_template(
            'ship_display.html', 
            data=display_data,
            refresh_interval=Config.REFRESH_INTERVAL
        )
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return render_template('error.html', message=str(e))

if __name__ == "__main__":
    logger.info(f"Starting TRMNL Ship Tracker")
    logger.info(f"Plugin UUID: {Config.TRMNL_PLUGIN_UUID}")
    logger.info(f"Target MMSI: {Config.MMSI}")
    logger.info(f"Refresh Interval: {Config.REFRESH_INTERVAL} seconds")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
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
            "cache_timeout": Config.CACHE_TIMEOUT
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
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )